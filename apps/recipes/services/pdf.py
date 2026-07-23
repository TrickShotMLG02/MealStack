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
from reportlab.platypus import (
    Image,
    Paragraph,
    Spacer,
    SimpleDocTemplate,
    Table,
    TableStyle,
)

from django.core.exceptions import ObjectDoesNotExist

from apps.recipes.models import Recipe


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


def build_recipe_pdf(recipe: Recipe, recipe_url: str) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
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
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#2c2c2c"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RecipeMeta",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#6b5c51"),
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
            textColor=colors.HexColor("#2c2c2c"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallLabel",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#7d6e64"),
        )
    )

    story = []
    story.append(Paragraph(escape(recipe.title), styles["RecipeTitle"]))

    meta_lines = []
    if recipe.cuisine:
        meta_lines.append(escape(recipe.cuisine.name))
    if recipe.author:
        meta_lines.append(escape(recipe.author))
    if recipe.source:
        safe_source = escape(recipe.source, {"\"": "&quot;"})
        meta_lines.append(f'<a href="{safe_source}">{escape(recipe.source)}</a>')
    story.append(Paragraph(" &nbsp;|&nbsp; ".join(meta_lines) or "&nbsp;", styles["RecipeMeta"]))
    story.append(Spacer(1, 8))

    image_path = _recipe_image_path(recipe)
    if image_path:
        try:
            image = Image(str(image_path))
            image._restrictSize(160 * mm, 90 * mm)
            story.append(image)
            story.append(Spacer(1, 10))
        except Exception:
            pass

    summary_data = [
        [Paragraph(_("Servings"), styles["SmallLabel"]), str(recipe.servings)],
        [Paragraph(_("Total time"), styles["SmallLabel"]), recipe.total_time_display()],
    ]
    summary_table = Table(summary_data, colWidths=[40 * mm, 120 * mm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e6d5c0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e6d5c0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 10))

    if recipe.tags.exists():
        tag_text = ", ".join(escape(tag.name) for tag in recipe.tags.all())
        story.append(Paragraph(f"{escape(_('Tags'))}: {tag_text}", styles["RecipeMeta"]))
        story.append(Spacer(1, 8))

    try:
        nutrition = recipe.recipe_nutrition
    except ObjectDoesNotExist:
        nutrition = None

    if nutrition:
        story.append(Paragraph(_("Nutrition"), styles["SectionHeading"]))
        nutrition_data = [
            [_("Calories"), f"{nutrition.per_serving_kcal:.0f} kcal"],
            [_("Protein"), f"{nutrition.per_serving_protein:.0f} g"],
            [_("Fat"), f"{nutrition.per_serving_fat:.0f} g"],
            [_("Carbs"), f"{nutrition.per_serving_carbs:.0f} g"],
            [_("Sugar"), f"{nutrition.per_serving_sugar:.0f} g"],
            [_("Salt"), f"{nutrition.per_serving_salt:.0f} g"],
        ]
        nutrition_table = Table(nutrition_data, colWidths=[45 * mm, 45 * mm])
        nutrition_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffaf5")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e6d5c0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e6d5c0")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(nutrition_table)
        story.append(Spacer(1, 10))

    story.append(Paragraph(_("Ingredients"), styles["SectionHeading"]))
    ingredient_groups = _recipe_ingredient_groups(recipe)
    for group in ingredient_groups:
        if len(ingredient_groups) > 1:
            story.append(Paragraph(escape(group.name or _("Ingredients")), styles["SmallLabel"]))
        for ri in group.recipeingredient_set.all():
            line = f"{ri.quantity:g} {escape(ri.unit.name)} {escape(ri.ingredient.name)}"
            story.append(Paragraph(line, styles["BodyText"]))
        story.append(Spacer(1, 4))

    story.append(Paragraph(_("Method"), styles["SectionHeading"]))
    step_groups = _recipe_step_groups(recipe)
    for group in step_groups:
        if len(step_groups) > 1:
            story.append(Paragraph(escape(group.name or _("Method")), styles["SmallLabel"]))
        for step in group.recipestep_set.all():
            story.append(Paragraph(escape(step.description).replace("\n", "<br/>"), styles["BodyText"]))
            story.append(Spacer(1, 2))
        story.append(Spacer(1, 4))

    notes = _recipe_notes(recipe)
    if notes:
        story.append(Paragraph(_("Notes"), styles["SectionHeading"]))
        for note in notes:
            if note.content:
                story.append(Paragraph(escape(note.content).replace("\n", "<br/>"), styles["BodyText"]))
                story.append(Spacer(1, 4))

    def add_footer(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6b5c51"))
        footer_y = 10 * mm
        canvas.drawString(doc_obj.leftMargin, footer_y, f"{_('Recipe URL')}: {recipe_url}")
        exported_text = f"{_('Exported at')}: {timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M')}"
        canvas.drawRightString(A4[0] - doc_obj.rightMargin, footer_y, exported_text)
        canvas.restoreState()

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    return buffer.getvalue()
