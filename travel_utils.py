import re

import pandas as pd


def normalize_place_name(value):
    """
    Rebuild place names that are returned as comma-separated single letters.
    Example: "B, a, r, a, ..., M, a, n, d, i, r" -> "Barakhamba Mandir"
    """

    if value is None:
        return ""

    text = str(value).strip()
    if not text:
        return ""

    text = text.replace("，", ",").replace("–", " ").replace("—", " ")
    text = re.sub(r"[\[\]\(\)]", "", text)
    tokens = [token for token in re.split(r"[\s,]+", text) if token]

    if not tokens:
        return ""

    if all(len(token) == 1 and token.isalpha() for token in tokens):
        joined = "".join(tokens)
        joined = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", joined)
        joined = re.sub(r"\s+", " ", joined).strip()
        return joined

    cleaned = re.sub(r"\s*,\s*", " ", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_string_list(values):
    """Clean a list of text items by removing comma-split letter artifacts."""

    if values is None:
        return []

    if isinstance(values, str):
        values = [values]
    elif not isinstance(values, list):
        return []

    cleaned = []
    for value in values:
        if value is None:
            continue

        if isinstance(value, list):
            cleaned.extend(normalize_string_list(value))
            continue

        if isinstance(value, str):
            text = value.strip()
            if not text:
                continue
            if text.startswith("[") and text.endswith("]"):
                try:
                    parsed = eval(text, {"__builtins__": {}}, {})
                    if isinstance(parsed, list):
                        cleaned.extend(normalize_string_list(parsed))
                        continue
                except Exception:
                    pass

            if all(len(part.strip()) == 1 and part.strip().isalpha() for part in re.split(r"\s*,\s*|\s+", text) if part.strip()):
                combined = "".join(part.strip() for part in re.split(r"\s*,\s*|\s+", text) if part.strip())
                normalized = normalize_place_name(combined)
            else:
                normalized = normalize_place_name(text)

            if normalized and normalized not in cleaned:
                cleaned.append(normalized)

    return cleaned


def normalize_trip_data(trip_data):
    """Normalize itinerary values so place names are consistent throughout the app."""

    if not isinstance(trip_data, dict):
        return trip_data

    itinerary = trip_data.get("itinerary", [])
    if not isinstance(itinerary, list):
        return trip_data

    cleaned_itinerary = []
    for day in itinerary:
        if not isinstance(day, dict):
            cleaned_itinerary.append(day)
            continue

        cleaned_day = dict(day)
        for period in ["morning", "afternoon", "evening", "night"]:
            section = cleaned_day.get(period, {})
            if not isinstance(section, dict):
                section = {}
                cleaned_day[period] = section

            for key in ["places", "activities", "food"]:
                value = section.get(key, [])
                if isinstance(value, str):
                    section[key] = normalize_string_list([value])
                elif isinstance(value, list):
                    section[key] = normalize_string_list(value)
                else:
                    section[key] = []

            cleaned_day[period] = section

        for alias, canonical in {"night": "evening"}.items():
            if alias in cleaned_day and canonical not in cleaned_day:
                cleaned_day[canonical] = cleaned_day[alias]
                cleaned_day.pop(alias, None)

        cleaned_itinerary.append(cleaned_day)

    trip_data["itinerary"] = cleaned_itinerary
    return trip_data


def validate_inputs(
    destination,
    days,
    travelers,
    budget,
    interests
):

    errors = []

    if not destination or not destination.strip():
        errors.append("Please enter a destination.")

    if int(days) < 1:
        errors.append("Days must be at least 1.")

    if int(travelers) < 1:
        errors.append("Travelers must be at least 1.")

    if float(budget) <= 0:
        errors.append("Budget must be greater than 0.")

    if not interests:
        errors.append("Select at least one interest.")

    return errors


def calculate_budget(
    accommodation=0,
    food=0,
    transport=0,
    activities=0,
    shopping_misc=0,
    emergency_buffer=0,
):

    categories = {
        "Accommodation": float(accommodation),
        "Food": float(food),
        "Transport": float(transport),
        "Activities": float(activities),
        "Shopping / Misc": float(shopping_misc),
        "Emergency Buffer": float(emergency_buffer),
    }

    categories["Total Estimated"] = sum(categories.values())

    return categories


def budget_dataframe(budget_data):

    data = [
        ("Accommodation", budget_data.get("accommodation", 0)),
        ("Food", budget_data.get("food", 0)),
        ("Transport", budget_data.get("transport", 0)),
        ("Activities", budget_data.get("activities", 0)),
        ("Shopping / Misc", budget_data.get("shopping_misc", 0)),
        ("Emergency Buffer", budget_data.get("emergency_buffer", 0)),
    ]

    return pd.DataFrame(
        data,
        columns=["Category", "Amount"]
    )


def format_inr(value):
    return f"₹{float(value):,.0f}"