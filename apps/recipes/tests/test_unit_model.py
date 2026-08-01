from django.forms import modelform_factory
from django.test import TestCase

from apps.recipes.models import Unit


class UnitModelTests(TestCase):
    def test_unit_type_choices_accept_plain_values(self):
        form_class = modelform_factory(Unit, fields=["name", "type"])
        form = form_class(data={"name": "pcs", "type": "count"})

        self.assertTrue(form.is_valid(), form.errors)
