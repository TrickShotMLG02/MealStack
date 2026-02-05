from django import template
from apps.common.time import format_timedelta

register = template.Library()

@register.filter
def pretty_duration(value):
    return format_timedelta(value)