import pandas as pd

from travel_utils import (
    budget_dataframe,
    calculate_budget,
    format_inr,
    normalize_place_name,
    validate_inputs,
)


def test_validate_inputs_valid_data():
    """
    Test validation with correct trip details.
    """

    errors = validate_inputs(
        destination="Hyderabad",
        days=3,
        travelers=2,
        budget=30000,
        interests=["Food", "Photography"],
    )

    assert errors == []


def test_validate_inputs_empty_destination():
    """
    Test validation when destination is empty.
    """

    errors = validate_inputs(
        destination="",
        days=3,
        travelers=2,
        budget=30000,
        interests=["Food"],
    )

    assert "Please enter a destination." in errors


def test_validate_inputs_invalid_days():
    """
    Test validation when number of days is invalid.
    """

    errors = validate_inputs(
        destination="Hyderabad",
        days=0,
        travelers=2,
        budget=30000,
        interests=["Food"],
    )

    assert "Days must be at least 1." in errors


def test_validate_inputs_invalid_travelers():
    """
    Test validation when number of travelers is invalid.
    """

    errors = validate_inputs(
        destination="Hyderabad",
        days=3,
        travelers=0,
        budget=30000,
        interests=["Food"],
    )

    assert "Travelers must be at least 1." in errors


def test_validate_inputs_invalid_budget():
    """
    Test validation when budget is invalid.
    """

    errors = validate_inputs(
        destination="Hyderabad",
        days=3,
        travelers=2,
        budget=0,
        interests=["Food"],
    )

    assert "Budget must be greater than 0." in errors


def test_validate_inputs_no_interests():
    """
    Test validation when no interests are selected.
    """

    errors = validate_inputs(
        destination="Hyderabad",
        days=3,
        travelers=2,
        budget=30000,
        interests=[],
    )

    assert "Select at least one interest." in errors


def test_calculate_budget():
    """
    Test budget calculation.
    """

    result = calculate_budget(
        accommodation=5000,
        food=3000,
        transport=2000,
        activities=1500,
        shopping_misc=1000,
        emergency_buffer=500,
    )

    assert result["Accommodation"] == 5000
    assert result["Food"] == 3000
    assert result["Transport"] == 2000
    assert result["Activities"] == 1500
    assert result["Shopping / Misc"] == 1000
    assert result["Emergency Buffer"] == 500

    assert result["Total Estimated"] == 13000


def test_budget_dataframe():
    """
    Test whether budget data is converted into a DataFrame.
    """

    budget_data = {
        "accommodation": 5000,
        "food": 3000,
        "transport": 2000,
        "activities": 1500,
        "shopping_misc": 1000,
        "emergency_buffer": 500,
    }

    df = budget_dataframe(budget_data)

    assert isinstance(df, pd.DataFrame)

    assert list(df.columns) == [
        "Category",
        "Amount",
    ]

    assert len(df) == 6

    assert df["Amount"].sum() == 13000


def test_format_inr():
    """
    Test Indian Rupee currency formatting.
    """

    result = format_inr(25000)

    assert result == "₹25,000"


def test_normalize_place_name_removes_char_separators():
    """
    Character-split place names should be rebuilt without comma separators.
    """

    result = normalize_place_name(
        "B, a, r, a, k, h, a, m, b, a, , M, a, n, d, i, r"
    )

    assert result == "Barakhamba Mandir"


def test_normalize_trip_data_handles_string_places_field():
    """
    Itinerary strings that contain comma-split place names should be converted
    into a clean list.
    """

    trip_data = {
        "itinerary": [
            {
                "day": 1,
                "morning": {
                    "places": "B, a, r, a, k, h, a, m, b, a, , M, a, n, d, i, r",
                    "activities": ["Temple visit"],
                    "food": ["Paratha"],
                },
                "night": {
                    "places": "Red Fort",
                    "activities": ["Light walk"],
                    "food": ["Chaat"],
                },
            }
        ]
    }

    normalized = normalize_trip_data(trip_data)

    assert normalized["itinerary"][0]["morning"]["places"] == [
        "Barakhamba Mandir"
    ]
    assert normalized["itinerary"][0]["night"]["places"] == [
        "Red Fort"
    ]

