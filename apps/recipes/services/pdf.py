from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils import timezone
from django.utils.translation import gettext as _
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from django.core.exceptions import ObjectDoesNotExist

from apps.common.time import format_timedelta
from apps.recipes.models import Recipe
from apps.recipes.services.servings import scale_nutrition, scale_quantity


PALETTE = {
    "page": colors.HexColor("#fbfaf7"),
    "ink": colors.HexColor("#23313a"),
    "muted": colors.HexColor("#66717a"),
    "accent": colors.HexColor("#0f766e"),
    "accent_soft": colors.HexColor("#e6f3f1"),
    "accent_warm": colors.HexColor("#f5ead9"),
    "line": colors.HexColor("#d8d2c8"),
    "panel": colors.white,
    "panel_soft": colors.HexColor("#f7f9fb"),
    "panel_alt": colors.HexColor("#fff9f1"),
}


def _recipe_image_path(recipe: Recipe) -> Path | None:
    prefetched_images = getattr(recipe, "prefetched_images", None)
    if prefetched_images:
        candidate = next((img for img in prefetched_images if img.is_primary and img.image), None)
        candidate = candidate or next((img for img in prefetched_images if img.image), None)
    else:
        primary = recipe.recipeimage_set.filter(is_primary=True).first()
        candidate = primary or recipe.recipeimage_set.first()

    if candidate and candidate.image:
        media_path = Path(settings.MEDIA_ROOT) / candidate.image.name
        if media_path.exists():
            return media_path

    placeholder = finders.find("recipes/images/placeholder.jpg")
    if placeholder:
        return Path(placeholder)

    return None


def _recipe_ingredient_groups(recipe: Recipe):
    return getattr(recipe, "prefetched_ingredient_groups", None) or list(recipe.recipeingredientgroup_set.all())


def _recipe_step_groups(recipe: Recipe):
    return getattr(recipe, "prefetched_step_groups", None) or list(recipe.recipestepgroup_set.all())


def _recipe_notes(recipe: Recipe):
    return getattr(recipe, "prefetched_notes", None) or list(recipe.recipenote_set.all())


def _format_quantity(quantity: float) -> str:
    return f"{quantity:.2f}".rstrip("0").rstrip(".")


def _duration_display(value) -> str:
    if not value or value.total_seconds() == 0:
        return "0m"
    return format_timedelta(value)


def _format_meta(recipe: Recipe) -> str:
    meta_parts = []
    if recipe.cuisine:
        meta_parts.append(escape(recipe.cuisine.name))
    if recipe.author:
        meta_parts.append(escape(recipe.author))
    if recipe.source:
        safe_source = escape(recipe.source, {"\"": "&quot;"})
        meta_parts.append(f'<a href="{safe_source}">{escape(recipe.source)}</a>')
    return " &nbsp;•&nbsp; ".join(meta_parts) or "&nbsp;"


def _metric_card(label: str, value: str, styles, width: float, background: colors.Color, border: colors.Color):
    card = Table(
        [
            [Paragraph(escape(label), styles["CardLabel"])],
            [Paragraph(escape(value), styles["CardValue"])],
        ],
        colWidths=[width],
    )
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.7, border),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return card


def _boxed_paragraph(text: str, styles, style_name: str, width: float, background, border) -> Table:
    box = Table([[Paragraph(text, styles[style_name])]], colWidths=[width])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.7, border),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return box


def _section_table(rows, col_widths, background, border_color, extra_styles=None):
    table = Table(rows, colWidths=col_widths, repeatRows=0)
    commands = [
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.7, border_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, border_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    if extra_styles:
        commands.extend(extra_styles)
    table.setStyle(TableStyle(commands))
    return table


def build_recipe_pdf(recipe: Recipe, recipe_url: str, servings: int | None = None) -> bytes:
    target_servings = servings if servings is not None else recipe.servings
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title=recipe.title,
        author=recipe.author or "MealStack",
        subject=recipe.title,
        keywords=", ".join(
            filter(
                None,
                [recipe.title, recipe.cuisine.name if recipe.cuisine else None, recipe.author],
            )
        ),
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="RecipeTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=PALETTE["ink"],
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RecipeMeta",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=12,
            textColor=PALETTE["muted"],
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RecipeIntro",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=12,
            textColor=PALETTE["muted"],
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            spaceBefore=10,
            spaceAfter=6,
            textColor=PALETTE["ink"],
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionSubheading",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.4,
            leading=11.2,
            textColor=PALETTE["accent"],
            spaceBefore=4,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CardLabel",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.4,
            leading=8.6,
            textColor=PALETTE["muted"],
            alignment=1,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CardValue",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=13.4,
            leading=15,
            textColor=PALETTE["ink"],
            alignment=1,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TagLine",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=9.5,
            textColor=PALETTE["accent"],
        )
    )
    styles.add(
        ParagraphStyle(
            name="IngredientAmount",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.3,
            leading=11,
            textColor=PALETTE["ink"],
        )
    )
    styles.add(
        ParagraphStyle(
            name="IngredientName",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.3,
            leading=11.2,
            textColor=PALETTE["ink"],
        )
    )
    styles.add(
        ParagraphStyle(
            name="StepNumber",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.white,
            alignment=1,
        )
    )
    styles.add(
        ParagraphStyle(
            name="StepText",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=12,
            textColor=PALETTE["ink"],
        )
    )
    styles.add(
        ParagraphStyle(
            name="NutritionLabel",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=PALETTE["ink"],
        )
    )
    styles.add(
        ParagraphStyle(
            name="NutritionValue",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=PALETTE["ink"],
            alignment=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="NoteText",
            parent=styles["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=9.2,
            leading=12,
            textColor=PALETTE["ink"],
        )
    )

    story = [Spacer(1, 1)]

    image_path = _recipe_image_path(recipe)
    tags = list(recipe.tags.all())
    has_hero_image = image_path is not None
    hero_left_width = doc.width - (66 * mm if has_hero_image else 0)

    intro_flowables = [
        Paragraph(escape(recipe.title), styles["RecipeTitle"]),
        Paragraph(_format_meta(recipe), styles["RecipeMeta"]),
    ]

    if tags:
        tag_text = ", ".join(escape(tag.name) for tag in tags)
        intro_flowables.append(_boxed_paragraph(tag_text, styles, "TagLine", hero_left_width, PALETTE["accent_soft"], PALETTE["accent"]))

    intro_flowables.append(
        Table(
            [[
                _metric_card(_("Servings"), str(target_servings), styles, (hero_left_width - 9 * mm) / 4, PALETTE["accent_soft"], PALETTE["accent"]),
                _metric_card(_("Prep"), _duration_display(recipe.preparation_time), styles, (hero_left_width - 9 * mm) / 4, PALETTE["panel_soft"], PALETTE["line"]),
                _metric_card(_("Cook"), _duration_display(recipe.cooking_time), styles, (hero_left_width - 9 * mm) / 4, PALETTE["panel_soft"], PALETTE["line"]),
                _metric_card(_("Total"), _duration_display(recipe.total_time), styles, (hero_left_width - 9 * mm) / 4, PALETTE["accent_warm"], PALETTE["accent"]),
            ]],
            colWidths=[(hero_left_width - 9 * mm) / 4] * 4,
            hAlign="LEFT",
        )
    )

    if has_hero_image:
        try:
            image = Image(str(image_path))
            image._restrictSize(62 * mm, 78 * mm)
            image_box = Table([[image]], colWidths=[64 * mm], hAlign="RIGHT")
            image_box.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), PALETTE["panel"]),
                        ("BOX", (0, 0), (-1, -1), 0.8, PALETTE["line"]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )
            hero_table = Table(
                [[intro_flowables, image_box]],
                colWidths=[hero_left_width, 64 * mm],
                hAlign="LEFT",
            )
            hero_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), PALETTE["panel"]),
                        ("BOX", (0, 0), (-1, -1), 0.8, PALETTE["line"]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(hero_table)
        except Exception:
            story.extend(intro_flowables)
    else:
        story.extend(intro_flowables)

    story.append(Spacer(1, 10))

    try:
        nutrition = recipe.recipe_nutrition
    except ObjectDoesNotExist:
        nutrition = None

    if nutrition:
        nutrition_totals = scale_nutrition(nutrition, target_servings)
        story.append(Paragraph(_("Nutrition"), styles["SectionHeading"]))
        story.append(_boxed_paragraph(f"{_('Selected servings')}: {target_servings}", styles, "RecipeIntro", doc.width * 0.35, PALETTE["panel_soft"], PALETTE["line"]))
        story.append(Spacer(1, 4))
        nutrition_rows = [
            [
                Paragraph(_("Metric"), styles["NutritionLabel"]),
                Paragraph(_("Per serving"), styles["NutritionLabel"]),
                Paragraph(_("Total"), styles["NutritionLabel"]),
            ],
            [
                Paragraph(_("Calories"), styles["NutritionLabel"]),
                Paragraph(f"{nutrition.per_serving_kcal:.0f} kcal", styles["NutritionValue"]),
                Paragraph(f"{nutrition_totals.kcal:.0f} kcal", styles["NutritionValue"]),
            ],
            [
                Paragraph(_("Protein"), styles["NutritionLabel"]),
                Paragraph(f"{nutrition.per_serving_protein:.0f} g", styles["NutritionValue"]),
                Paragraph(f"{nutrition_totals.protein:.0f} g", styles["NutritionValue"]),
            ],
            [
                Paragraph(_("Fat"), styles["NutritionLabel"]),
                Paragraph(f"{nutrition.per_serving_fat:.0f} g", styles["NutritionValue"]),
                Paragraph(f"{nutrition_totals.fat:.0f} g", styles["NutritionValue"]),
            ],
            [
                Paragraph(_("Carbs"), styles["NutritionLabel"]),
                Paragraph(f"{nutrition.per_serving_carbs:.0f} g", styles["NutritionValue"]),
                Paragraph(f"{nutrition_totals.carbs:.0f} g", styles["NutritionValue"]),
            ],
            [
                Paragraph(_("Sugar"), styles["NutritionLabel"]),
                Paragraph(f"{nutrition.per_serving_sugar:.0f} g", styles["NutritionValue"]),
                Paragraph(f"{nutrition_totals.sugar:.0f} g", styles["NutritionValue"]),
            ],
            [
                Paragraph(_("Salt"), styles["NutritionLabel"]),
                Paragraph(f"{nutrition.per_serving_salt:.0f} g", styles["NutritionValue"]),
                Paragraph(f"{nutrition_totals.salt:.0f} g", styles["NutritionValue"]),
            ],
        ]
        if getattr(nutrition, "per_serving_saturates", None) is not None:
            nutrition_rows.append(
                [
                    Paragraph(_("Saturates"), styles["NutritionLabel"]),
                    Paragraph(f"{nutrition.per_serving_saturates:.0f} g", styles["NutritionValue"]),
                    Paragraph(f"{nutrition.per_serving_saturates * target_servings:.0f} g", styles["NutritionValue"]),
                ]
            )
        nutrition_table = _section_table(
            nutrition_rows,
            [38 * mm, 43 * mm, 43 * mm],
            PALETTE["panel_alt"],
            PALETTE["line"],
            extra_styles=[
                ("BACKGROUND", (0, 0), (-1, 0), PALETTE["accent_soft"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), PALETTE["accent"]),
            ],
        )
        story.append(nutrition_table)
        story.append(Spacer(1, 10))

    story.append(Paragraph(_("Ingredients"), styles["SectionHeading"]))
    ingredient_groups = _recipe_ingredient_groups(recipe)
    for group in ingredient_groups:
        if len(ingredient_groups) > 1:
            story.append(Paragraph(escape(group.name or _("Ingredients")), styles["SectionSubheading"]))

        ingredient_rows = []
        for ri in group.recipeingredient_set.all():
            quantity = scale_quantity(ri.quantity, recipe.servings, target_servings)
            ingredient_rows.append(
                [
                    Paragraph(f"{_format_quantity(quantity)} {escape(ri.unit.name)}", styles["IngredientAmount"]),
                    Paragraph(escape(ri.ingredient.name), styles["IngredientName"]),
                ]
            )

        if ingredient_rows:
            ingredient_table = _section_table(
                ingredient_rows,
                [34 * mm, doc.width - 34 * mm],
                PALETTE["panel"],
                PALETTE["line"],
                extra_styles=[
                    ("BACKGROUND", (0, 0), (0, -1), PALETTE["accent_soft"]),
                    ("TEXTCOLOR", (0, 0), (0, -1), PALETTE["accent"]),
                ],
            )
            story.append(ingredient_table)
            story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(_("No ingredients added yet."), styles["RecipeIntro"]))
            story.append(Spacer(1, 4))

    story.append(Paragraph(_("Method"), styles["SectionHeading"]))
    step_groups = _recipe_step_groups(recipe)
    for group in step_groups:
        if len(step_groups) > 1:
            story.append(Paragraph(escape(group.name or _("Method")), styles["SectionSubheading"]))

        step_rows = []
        for index, step in enumerate(group.recipestep_set.all(), start=1):
            step_rows.append(
                [
                    Paragraph(str(index), styles["StepNumber"]),
                    Paragraph(escape(step.description).replace("\n", "<br/>"), styles["StepText"]),
                ]
            )

        if step_rows:
            step_table = _section_table(
                step_rows,
                [12 * mm, doc.width - 12 * mm],
                PALETTE["panel"],
                PALETTE["line"],
                extra_styles=[
                    ("BACKGROUND", (0, 0), (0, -1), PALETTE["accent"]),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                ],
            )
            story.append(step_table)
            story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(_("No steps added yet."), styles["RecipeIntro"]))
            story.append(Spacer(1, 4))

    notes = _recipe_notes(recipe)
    if notes:
        story.append(Paragraph(_("Notes"), styles["SectionHeading"]))
        for note in notes:
            if note.content:
                note_box = Table(
                    [[Paragraph(escape(note.content).replace("\n", "<br/>"), styles["NoteText"])]],
                    colWidths=[doc.width],
                )
                note_box.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), PALETTE["accent_soft"]),
                            ("BOX", (0, 0), (-1, -1), 0.6, PALETTE["accent"]),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 7),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                        ]
                    )
                )
                story.append(note_box)
                story.append(Spacer(1, 5))

    def add_footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFillColor(PALETTE["page"])
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.setFillColor(PALETTE["accent"])
        canvas.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, fill=1, stroke=0)
        canvas.setStrokeColor(PALETTE["line"])
        canvas.setLineWidth(0.6)
        canvas.line(doc_obj.leftMargin, 13.5 * mm, A4[0] - doc_obj.rightMargin, 13.5 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(PALETTE["muted"])
        footer_y = 8.6 * mm
        canvas.drawString(doc_obj.leftMargin, footer_y, f"{_('Recipe URL')}: {recipe_url}")
        exported_text = f"{_('Exported at')}: {timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M')}"
        canvas.drawRightString(A4[0] - doc_obj.rightMargin, footer_y, exported_text)
        canvas.setFont("Helvetica-Bold", 8.2)
        canvas.setFillColor(PALETTE["accent"])
        canvas.drawRightString(A4[0] - doc_obj.rightMargin, 5.1 * mm, str(canvas.getPageNumber()))
        canvas.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    return buffer.getvalue()
