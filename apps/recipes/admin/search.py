import re
import unicodedata
from difflib import SequenceMatcher

from django.db.models import Case, IntegerField, Value, When


class FuzzySearchAdminMixin:
    """Add tolerant fallback matching to the standard admin search.

    Django's normal ``icontains`` search remains the fast path. If it finds
    nothing, the fallback compares normalized words in the configured fields,
    which makes admin search forgiving of capitalization, accents, and small
    spelling mistakes without changing the public recipe search behavior.
    """

    fuzzy_search_fields = ()
    fuzzy_match_threshold = 0.72

    @staticmethod
    def _normalize(value):
        decomposed = unicodedata.normalize("NFKD", str(value).casefold())
        without_accents = "".join(
            character for character in decomposed if not unicodedata.combining(character)
        )
        return re.sub(r"[^\w]+", " ", without_accents).strip()

    @classmethod
    def _field_value(cls, obj, field_name):
        value = obj
        for part in field_name.split("__"):
            value = getattr(value, part, None)
            if value is None:
                return ""
        return str(value)

    @classmethod
    def _field_score(cls, query_tokens, field_value):
        normalized_value = cls._normalize(field_value)
        if not normalized_value:
            return 0

        value_tokens = normalized_value.split()
        token_scores = []
        for query_token in query_tokens:
            best_score = 0
            for value_token in value_tokens:
                if query_token in value_token:
                    score = 1
                else:
                    score = SequenceMatcher(None, query_token, value_token).ratio()
                best_score = max(best_score, score)
            token_scores.append(best_score)

        if not token_scores or min(token_scores) < cls.fuzzy_match_threshold:
            return 0
        return sum(token_scores) / len(token_scores)

    def _fuzzy_matches(self, queryset, search_term):
        query_tokens = self._normalize(search_term).split()
        if not query_tokens:
            return []

        matches = []
        for obj in queryset:
            score = max(
                (
                    self._field_score(query_tokens, self._field_value(obj, field_name))
                    for field_name in self.fuzzy_search_fields
                ),
                default=0,
            )
            if score:
                matches.append((score, obj))

        matches.sort(key=lambda item: (-item[0], self._normalize(str(item[1])), item[1].pk))
        return [obj for _, obj in matches]

    def get_search_results(self, request, queryset, search_term):
        results, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        if not search_term or results.exists():
            return results, may_have_duplicates

        fuzzy_matches = self._fuzzy_matches(queryset, search_term)
        if not fuzzy_matches:
            return results, may_have_duplicates

        match_ids = [obj.pk for obj in fuzzy_matches]
        ordering = Case(
            *[
                When(pk=match_id, then=Value(index))
                for index, match_id in enumerate(match_ids)
            ],
            output_field=IntegerField(),
        )
        return queryset.filter(pk__in=match_ids).order_by(ordering), False
