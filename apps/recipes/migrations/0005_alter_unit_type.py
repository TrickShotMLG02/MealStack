from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


def normalize_unit_type_values(apps, schema_editor):
    Unit = apps.get_model("recipes", "Unit")
    replacements = {
        "UnitType.WEIGHT": "weight",
        "UnitType.VOLUME": "volume",
        "UnitType.COUNT": "count",
    }
    for old_value, new_value in replacements.items():
        Unit.objects.filter(type=old_value).update(type=new_value)


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0004_ingredient_generic_name"),
    ]

    operations = [
        migrations.RunPython(normalize_unit_type_values, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="unit",
            name="type",
            field=models.CharField(
                choices=[
                    ("weight", _("Weight")),
                    ("volume", _("Volume")),
                    ("count", _("Count")),
                ],
                max_length=10,
                verbose_name=_("Type"),
            ),
        ),
    ]
