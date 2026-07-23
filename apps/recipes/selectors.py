from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
import shlex
import unicodedata

from django.db.models import QuerySet

from apps.recipes.models import Recipe


SEARCH_SCORE_THRESHOLD = 0.42
STRUCTURED_MATCH_THRESHOLD = 0.9
SUGGESTION_SCORE_THRESHOLD = 0.55


@dataclass(frozen=True)
class SearchSuggestion:
    kind: str
    label: str
    value: str
    recipe_slug: str | None = None


def _normalize_search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    stripped = "".join(character for character in normalized if not unicodedata.combining(character))
    cleaned = re.sub(r"[^0-9a-zA-Z]+", " ", stripped.casefold())
    return " ".join(cleaned.split())


def _tokenize_search_query(query: str) -> list[str]:
    normalized_query = " ".join((query or "").split())
    if not normalized_query:
        return []

    try:
        tokens = shlex.split(normalized_query)
    except ValueError:
        tokens = normalized_query.split()

    return [token for token in tokens if token]


def _candidate_score(query: str, candidate: str) -> float:
    normalized_query = _normalize_search_text(query)
    normalized_candidate = _normalize_search_text(candidate)

    if not normalized_query or not normalized_candidate:
        return 0.0

    if normalized_query in normalized_candidate:
        return 1.0

    query_tokens = normalized_query.split()
    candidate_tokens = normalized_candidate.split()

    overall_length_factor = min(len(normalized_query), len(normalized_candidate)) / max(
        len(normalized_query),
        len(normalized_candidate),
    )
    overall_ratio = SequenceMatcher(None, normalized_query, normalized_candidate).ratio() * overall_length_factor

    token_scores: list[float] = []
    for token in query_tokens:
        best = SequenceMatcher(None, token, normalized_candidate).ratio()
        for candidate_token in candidate_tokens:
            if token == candidate_token:
                best = 1.0
                break

            if token in candidate_token or candidate_token.startswith(token):
                best = max(best, 0.96)

            length_factor = min(len(token), len(candidate_token)) / max(len(token), len(candidate_token))
            best = max(best, SequenceMatcher(None, token, candidate_token).ratio() * length_factor)

        token_scores.append(best)

    token_ratio = sum(token_scores) / len(token_scores) if token_scores else 0.0
    return max(overall_ratio, token_ratio)


def _recipe_search_candidates(recipe: Recipe) -> list[str]:
    candidates = [
        recipe.title,
        recipe.author or "",
        recipe.source or "",
    ]

    if recipe.cuisine:
        candidates.append(recipe.cuisine.name)

    for tag in recipe.tags.all():
        candidates.append(tag.name)

    for ingredient_group in recipe.recipeingredientgroup_set.all():
        candidates.append(ingredient_group.name or "")
        for recipe_ingredient in ingredient_group.recipeingredient_set.all():
            ingredient = recipe_ingredient.ingredient
            candidates.extend(
                [
                    ingredient.name,
                    ingredient.generic_name or "",
                    ingredient.brand or "",
                ]
            )

    for step_group in recipe.recipestepgroup_set.all():
        candidates.append(step_group.name or "")
        for step in step_group.recipestep_set.all():
            candidates.append(step.description)

    for note in recipe.recipenote_set.all():
        candidates.append(note.content or "")

    return [candidate for candidate in candidates if candidate]


def _recipe_ingredient_candidates(recipe: Recipe) -> list[str]:
    candidates: list[str] = []
    for ingredient_group in recipe.recipeingredientgroup_set.all():
        for recipe_ingredient in ingredient_group.recipeingredient_set.all():
            ingredient = recipe_ingredient.ingredient
            candidates.extend(
                [
                    ingredient.name,
                    ingredient.generic_name or "",
                    ingredient.brand or "",
                ]
            )

    return [candidate for candidate in candidates if candidate]


def _recipe_tag_candidates(recipe: Recipe) -> list[str]:
    return [tag.name for tag in recipe.tags.all()]


def _recipe_cuisine_candidates(recipe: Recipe) -> list[str]:
    return [recipe.cuisine.name] if recipe.cuisine else []


def _structured_candidate_score(query: str, candidate: str) -> float:
    normalized_query = _normalize_search_text(query)
    normalized_candidate = _normalize_search_text(candidate)

    if not normalized_query or not normalized_candidate:
        return 0.0

    if normalized_query == normalized_candidate:
        return 1.0

    if normalized_candidate.startswith(normalized_query):
        return 0.98

    candidate_tokens = normalized_candidate.split()
    if any(token.startswith(normalized_query) for token in candidate_tokens):
        return 0.96

    if normalized_query in normalized_candidate:
        return 0.92

    return 0.0


def _candidate_fields_match(query: str, recipe: Recipe) -> float:
    return max(
        (_candidate_score(query, candidate) for candidate in _recipe_search_candidates(recipe)),
        default=0.0,
    )


def _ingredient_fields_match(query: str, recipe: Recipe) -> float:
    return max(
        (_structured_candidate_score(query, candidate) for candidate in _recipe_ingredient_candidates(recipe)),
        default=0.0,
    )


def _tag_fields_match(query: str, recipe: Recipe) -> float:
    return max(
        (_structured_candidate_score(query, candidate) for candidate in _recipe_tag_candidates(recipe)),
        default=0.0,
    )


def _cuisine_fields_match(query: str, recipe: Recipe) -> float:
    return max(
        (_structured_candidate_score(query, candidate) for candidate in _recipe_cuisine_candidates(recipe)),
        default=0.0,
    )


def _infer_structured_kind(recipes: list[Recipe], query: str) -> str | None:
    normalized_query = _normalize_search_text(query)
    if len(normalized_query) < 3 or len(_tokenize_search_query(query)) != 1:
        return None

    matchers = (
        ("ingredient", _ingredient_fields_match),
        ("tag", _tag_fields_match),
        ("cuisine", _cuisine_fields_match),
    )

    for kind, matcher in matchers:
        if any(matcher(query, recipe) >= STRUCTURED_MATCH_THRESHOLD for recipe in recipes):
            return kind

    return None


def _recipe_has_exact_ingredient_match(recipe: Recipe, query: str) -> bool:
    normalized_query = _normalize_search_text(query)
    if not normalized_query:
        return False

    for candidate in _recipe_ingredient_candidates(recipe):
        if _normalize_search_text(candidate) == normalized_query:
            return True

    return False


def _recipe_has_exact_tag_match(recipe: Recipe, query: str) -> bool:
    normalized_query = _normalize_search_text(query)
    if not normalized_query:
        return False

    return any(_normalize_search_text(tag.name) == normalized_query for tag in recipe.tags.all())


def _recipe_has_exact_cuisine_match(recipe: Recipe, query: str) -> bool:
    if not recipe.cuisine:
        return False

    return _normalize_search_text(recipe.cuisine.name) == _normalize_search_text(query)


def search_recipes(queryset: QuerySet[Recipe], query: str, kind: str | None = None):
    tokens = _tokenize_search_query(query)
    if not tokens:
        return queryset

    recipes = list(queryset)
    structured_kind = kind if kind in {"ingredient", "tag", "cuisine"} else _infer_structured_kind(recipes, query)
    ranked: list[tuple[float, Recipe]] = []
    for recipe in recipes:
        if structured_kind == "ingredient" and kind == "ingredient":
            score = 1.0 if _recipe_has_exact_ingredient_match(recipe, query) else 0.0
        elif structured_kind == "ingredient":
            score = _ingredient_fields_match(query, recipe)
        elif structured_kind == "tag" and kind == "tag":
            score = 1.0 if _recipe_has_exact_tag_match(recipe, query) else 0.0
        elif structured_kind == "tag":
            score = _tag_fields_match(query, recipe)
        elif structured_kind == "cuisine" and kind == "cuisine":
            score = 1.0 if _recipe_has_exact_cuisine_match(recipe, query) else 0.0
        elif structured_kind == "cuisine":
            score = _cuisine_fields_match(query, recipe)
        else:
            score = min(_candidate_fields_match(token, recipe) for token in tokens)

        threshold = (
            1.0
            if kind in {"ingredient", "tag", "cuisine"}
            else STRUCTURED_MATCH_THRESHOLD if structured_kind else SEARCH_SCORE_THRESHOLD
        )
        if score >= threshold:
            ranked.append((score, recipe))

    ranked.sort(key=lambda item: (-item[0], _normalize_search_text(item[1].title), item[1].pk or 0))
    return [recipe for _, recipe in ranked]


def _distinct_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    distinct: list[str] = []
    for value in values:
        normalized = _normalize_search_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        distinct.append(value)
    return distinct


def _best_suggestion_score(query: str, value: str) -> float:
    score = _structured_candidate_score(query, value)

    if score < STRUCTURED_MATCH_THRESHOLD:
        return 0.0

    return score


def search_suggestions(query: str, limit: int = 6) -> list[SearchSuggestion]:
    normalized_query = _normalize_search_text(query)
    if len(normalized_query) < 2:
        return []

    suggestions: list[tuple[float, SearchSuggestion]] = []
    seen: set[tuple[str, str]] = set()

    recipe_candidates = (
        Recipe.objects.filter(status="published")
        .select_related("cuisine")
        .only("title", "slug", "author", "source", "cuisine__name")
    )
    for recipe in recipe_candidates:
        score = max(
            _candidate_score(query, recipe.title),
            _candidate_score(query, recipe.author or ""),
            _candidate_score(query, recipe.source or ""),
            _candidate_score(query, recipe.cuisine.name if recipe.cuisine else ""),
        )
        if score < SUGGESTION_SCORE_THRESHOLD:
            continue

        key = ("recipe", _normalize_search_text(recipe.title))
        if key in seen:
            continue

        seen.add(key)
        suggestions.append(
            (
                score,
                SearchSuggestion(
                    kind="recipe",
                    label=recipe.title,
                    value=recipe.title,
                    recipe_slug=recipe.slug,
                ),
            )
        )

    tag_names = _distinct_values(
        list(
            Recipe.objects.filter(status="published")
            .values_list("tags__name", flat=True)
            .distinct()
        )
    )
    cuisine_names = _distinct_values(
        list(
            Recipe.objects.filter(status="published", cuisine__isnull=False)
            .values_list("cuisine__name", flat=True)
            .distinct()
        )
    )
    ingredient_names = _distinct_values(
        list(
            Recipe.objects.filter(status="published")
            .values_list("recipeingredientgroup__recipeingredient__ingredient__name", flat=True)
            .distinct()
        )
    )

    for kind, values in (
        ("tag", tag_names),
        ("cuisine", cuisine_names),
        ("ingredient", ingredient_names),
    ):
        for value in values:
            key = (kind, _normalize_search_text(value))
            if key in seen:
                continue

            score = _best_suggestion_score(query, value)
            if score <= 0:
                continue

            seen.add(key)
            suggestions.append(
                (
                    score,
                    SearchSuggestion(
                        kind=kind,
                        label=value,
                        value=value,
                    ),
                )
            )

    suggestions.sort(key=lambda item: (-item[0], item[1].kind, _normalize_search_text(item[1].label)))
    return [suggestion for _, suggestion in suggestions[:limit]]
