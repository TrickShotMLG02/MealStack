from datetime import timedelta

import django.utils.text

GERMAN_CHAR_MAP = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "ß": "ss",
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",
}


def normalize_german(text: str) -> str:
    for src, target in GERMAN_CHAR_MAP.items():
        text = text.replace(src, target)
    return text


def slugify(text: str) -> str:
    """
    Uses slugify to convert text to slug, while applying normalizations
    :param text: The text to slugify
    :return: The slug with applied normalizations
    """
    normalized_text = normalize_german(text)

    return django.utils.text.slugify(normalized_text)

def time_formatting(delta: timedelta) -> str:
    """
    Uses timedelta to format the total time
    :param delta: The timedelta to format into a string
    :return: The formatted string i.e. 3h 15m
    """
    hours = delta.total_seconds() // 3600
    minutes = (delta.total_seconds() % 3600) // 60
    return f"{int(hours)}h {int(minutes)}m" if hours else f"{int(minutes)}m"
