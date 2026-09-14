from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import gettext_lazy as _

from apps.users.models import RecipeList


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["email"]
        labels = {"email": _("Email")}


class ProfilePasswordForm(PasswordChangeForm):
    pass


class RecipeListForm(forms.ModelForm):
    class Meta:
        model = RecipeList
        fields = ["name"]
        labels = {"name": _("List name")}
