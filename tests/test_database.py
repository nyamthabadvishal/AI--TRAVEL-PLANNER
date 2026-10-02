import tempfile
from pathlib import Path

import database


def test_database_initialization():
    """
    Test whether the SQLite database and trips table
    are created successfully.
    """

    original_db_path = database.DB_PATH

    with tempfile.TemporaryDirectory() as temp_dir:

        database.DB_PATH = Path(temp_dir) / "test_travel_planner.db"

        # Initialize database
        database.init_db()

        # Check database file exists
        assert database.DB_PATH.exists()

        # Check trips table can be accessed
        trips = database.list_trips()

        assert isinstance(trips, list)
        assert len(trips) == 0

    # Restore original database path
    database.DB_PATH = original_db_path


def test_save_and_get_trip():
    """
    Test saving a trip and retrieving it from SQLite.
    """

    original_db_path = database.DB_PATH

    with tempfile.TemporaryDirectory() as temp_dir:

        database.DB_PATH = Path(temp_dir) / "test_travel_planner.db"

        database.init_db()

        trip_data = {
            "trip_summary": {
                "destination": "Hyderabad",
                "days": 3,
                "travelers": 2
            },
            "itinerary": [],
            "budget": {
                "total_estimated": 15000
            },
            "recommendations": [],
            "packing_list": []
        }

        # Save trip
        trip_id = database.save_trip(
            "Hyderabad Trip",
            "Hyderabad",
            trip_data
        )

        assert trip_id > 0

        # Retrieve trip
        saved_trip = database.get_trip(trip_id)

        assert saved_trip is not None
        assert saved_trip["trip_name"] == "Hyderabad Trip"
        assert saved_trip["destination"] == "Hyderabad"
        assert saved_trip["trip_data"]["budget"]["total_estimated"] == 15000

    database.DB_PATH = original_db_path


def test_delete_trip():
    """
    Test deleting a saved trip.
    """

    original_db_path = database.DB_PATH

    with tempfile.TemporaryDirectory() as temp_dir:

        database.DB_PATH = Path(temp_dir) / "test_travel_planner.db"

        database.init_db()

        trip_data = {
            "trip_summary": {
                "destination": "Goa"
            },
            "itinerary": [],
            "budget": {},
            "recommendations": [],
            "packing_list": []
        }

        # Save trip
        trip_id = database.save_trip(
            "Goa Trip",
            "Goa",
            trip_data
        )

        assert database.get_trip(trip_id) is not None

        # Delete trip
        database.delete_trip(trip_id)

        # Verify deletion