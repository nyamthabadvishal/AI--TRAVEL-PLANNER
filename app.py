from urllib.parse import quote_plus

import streamlit as st

from ai_service import (
    AIServiceError,
    generate_chat_reply,
    generate_travel_plan,
)
from database import (
    delete_trip,
    get_trip,
    init_db,
    list_trips,
    save_trip,
)
from travel_utils import (
    budget_dataframe,
    normalize_place_name,
    normalize_trip_data,
    validate_inputs,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Smart Travel Planner",
    page_icon="✈️",
    layout="wide",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #667085;
        margin-bottom: 1rem;
    }

    .metric-card {
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# INITIALIZE DATABASE
# =========================================================

try:
    init_db()
except Exception as exc:
    st.error(f"Database initialization failed: {exc}")
    st.stop()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">✈️ AI-Powered Smart Travel Planner</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Create personalized AI itineraries, budget plans, "
    "recommendations and packing checklists."
    "</div>",
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

if "trip" not in st.session_state:
    st.session_state.trip = None

if "chat" not in st.session_state:
    st.session_state.chat = []


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("🌍 Trip Details")

    destination = st.text_input(
        "Destination",
        placeholder="Example: Hyderabad",
    )

    days = st.number_input(
        "Number of days",
        min_value=1,
        max_value=30,
        value=3,
        step=1,
    )

    travelers = st.number_input(
        "Number of travelers",
        min_value=1,
        max_value=20,
        value=2,
        step=1,
    )

    budget = st.number_input(
        "Total budget (₹)",
        min_value=1000.0,
        value=30000.0,
        step=1000.0,
    )

    travel_type = st.selectbox(
        "Travel type",
        [
            "Solo",
            "Couple",
            "Family",
            "Friends",
        ],
    )

    interests = st.multiselect(
        "Interests",
        [
            "Historical places",
            "Nature",
            "Adventure",
            "Food",
            "Shopping",
            "Beaches",
            "Temples",
            "Nightlife",
            "Photography",
        ],
        default=[
            "Food",
            "Photography",
        ],
    )

    generate_button = st.button(
        "✈️ Generate My Travel Plan",
        type="primary",
        use_container_width=True,
    )


# =========================================================
# GENERATE TRAVEL PLAN
# =========================================================

if generate_button:

    errors = validate_inputs(
        destination,
        days,
        travelers,
        budget,
        interests,
    )

    if errors:

        for error in errors:
            st.error(error)

    else:

        with st.spinner(
            "🤖 OpenAI is creating your personalized travel plan..."
        ):

            try:

                generated_trip = generate_travel_plan(
                    destination=destination.strip(),
                    days=int(days),
                    travelers=int(travelers),
                    budget=float(budget),
                    travel_type=travel_type,
                    interests=interests,
                )

                if not isinstance(generated_trip, dict):
                    raise AIServiceError(
                        "The AI returned an invalid travel plan."
                    )

                st.session_state.trip = normalize_trip_data(generated_trip)
                st.session_state.chat = []

                st.success(
                    "✅ Travel plan generated successfully!"
                )

            except AIServiceError as exc:

                st.error(str(exc))

            except Exception as exc:

                st.error(
                    f"Unexpected error while generating the trip: {exc}"
                )


# =========================================================
# GET CURRENT TRIP
# =========================================================

trip = st.session_state.trip


# =========================================================
# DISPLAY TRIP
# =========================================================

if trip:

    trip_summary = trip.get(
        "trip_summary",
        {},
    )

    trip_destination = trip_summary.get(
        "destination",
        destination,
    )

    trip_days = trip_summary.get(
        "days",
        int(days),
    )

    trip_travelers = trip_summary.get(
        "travelers",
        int(travelers),
    )

    trip_type = trip_summary.get(
        "travel_type",
        travel_type,
    )

    st.subheader(
        f"🌍 {trip_destination}"
    )

    st.caption(
        f"{trip_days} days • "
        f"{trip_travelers} travelers • "
        f"{trip_type} • "
        f"Budget ₹{float(budget):,.0f}"
    )

    # =====================================================
    # TABS
    # =====================================================

    itinerary_tab, budget_tab, recommendations_tab, packing_tab, map_tab, save_tab = st.tabs(
        [
            "🗓️ Itinerary",
            "💰 Budget",
            "⭐ Recommendations",
            "🎒 Packing",
            "🗺️ Map",
            "💾 Save",
        ]
    )

    # =====================================================
    # ITINERARY
    # =====================================================

    with itinerary_tab:

        st.header("🗓️ Day-by-Day Itinerary")

        itinerary = trip.get(
            "itinerary",
            [],
        )

        if not isinstance(itinerary, list) or not itinerary:

            st.warning(
                "No itinerary was returned by the AI."
            )

        else:

            for day in itinerary:

                if not isinstance(day, dict):
                    continue

                day_number = day.get(
                    "day",
                    "",
                )

                day_title = day.get(
                    "title",
                    "Travel Plan",
                )

                st.markdown(
                    f"### Day {day_number}: {day_title}"
                )

                for period in [
                    "morning",
                    "afternoon",
                    "evening",
                    "night",
                ]:

                    section = day.get(
                        period,
                        {},
                    )

                    if not section and "night" in day and period == "evening":
                        section = day.get("night", {})

                    if period == "night" and "night" not in day and "evening" in day:
                        section = day.get("evening", {})

                    if not isinstance(section, dict):
                        section = {}

                    places = section.get(
                        "places",
                        [],
                    )

                    activities = section.get(
                        "activities",
                        [],
                    )

                    food = section.get(
                        "food",
                        [],
                    )

                    estimated_cost = section.get(
                        "estimated_cost",
                        0,
                    )

                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"#### {period.title()}"
                        )

                        if places:

                            cleaned_places = [
                                normalize_place_name(place)
                                for place in places
                                if normalize_place_name(place)
                            ]

                            st.write(
                                "**📍 Places:** "
                                + ", ".join(cleaned_places)
                            )

                        if activities:

                            cleaned_activities = [
                                normalize_place_name(activity)
                                for activity in activities
                                if normalize_place_name(activity)
                            ]

                            st.write(
                                "**🎯 Activities:** "
                                + ", ".join(cleaned_activities)
                            )

                        if food:

                            cleaned_food = [
                                normalize_place_name(food_item)
                                for food_item in food
                                if normalize_place_name(food_item)
                            ]

                            st.write(
                                "**🍴 Food:** "
                                + ", ".join(cleaned_food)
                            )

                        if estimated_cost:

                            try:

                                cost = float(
                                    estimated_cost
                                )

                                st.caption(
                                    f"💰 Estimated cost: "
                                    f"₹{cost:,.0f}"
                                )

                            except (
                                ValueError,
                                TypeError,
                            ):

                                st.caption(
                                    f"💰 Estimated cost: "
                                    f"{estimated_cost}"
                                )

                tips = day.get(
                    "tips",
                    "",
                )

                if tips:

                    st.info(
                        f"💡 Tip: {tips}"
                    )


    # =====================================================
    # BUDGET
    # =====================================================

    with budget_tab:

        st.header("💰 Budget Planner")

        budget_data = trip.get(
            "budget",
            {},
        )

        if not isinstance(budget_data, dict):
            budget_data = {}

        try:

            total_estimated = float(
                budget_data.get(
                    "total_estimated",
                    0,
                )
            )

        except (
            ValueError,
            TypeError,
        ):

            total_estimated = 0.0

        try:

            user_budget = float(
                budget
            )

        except (
            ValueError,
            TypeError,
        ):

            user_budget = 0.0

        remaining_budget = (
            user_budget - total_estimated
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Estimated Total",
                f"₹{total_estimated:,.0f}",
            )

        with col2:

            per_person = (
                total_estimated
                / max(int(travelers), 1)
            )

            st.metric(
                "Per Person",
                f"₹{per_person:,.0f}",
            )

        with col3:

            st.metric(
                "Remaining Budget",
                f"₹{remaining_budget:,.0f}",
            )

        if remaining_budget < 0:

            st.error(
                "⚠️ The estimated trip cost is "
                "higher than your selected budget."
            )

        else:

            st.success(
                "✅ The estimated trip cost is "
                "within your selected budget."
            )

        # Budget dataframe

        try:

            budget_df = budget_dataframe(
                budget_data
            )

        except Exception as exc:

            st.error(
                f"Unable to display budget: {exc}"
            )

            budget_df = None

        if budget_df is not None and not budget_df.empty:

            st.subheader(
                "📋 Budget Breakdown"
            )

            st.dataframe(
                budget_df,
                use_container_width=True,
                hide_index=True,
            )

            st.subheader(
                "📊 Budget Distribution"
            )

            try:

                chart_data = budget_df.set_index(
                    "Category"
                )["Amount"]

                st.bar_chart(
                    chart_data
                )

            except Exception:

                st.info(
                    "Budget chart could not be displayed."
                )

        else:

            st.info(
                "No budget breakdown was returned."
            )

        st.caption(
            "ℹ️ All prices are AI-generated planning "
            "estimates, not live quotes."
        )


    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    with recommendations_tab:

        st.header(
            "⭐ Personalized Recommendations"
        )

        recommendations = trip.get(
            "recommendations",
            [],
        )

        if (
            not isinstance(
                recommendations,
                list,
            )
            or not recommendations
        ):

            st.info(
                "No recommendations were returned."
            )

        else:

            for recommendation in recommendations:

                if not isinstance(
                    recommendation,
                    dict,
                ):
                    continue

                name = recommendation.get(
                    "name",
                    "Recommendation",
                )

                reason = recommendation.get(
                    "reason",
                    "",
                )

                best_for = recommendation.get(
                    "best_for",
                    [],
                )

                st.markdown(
                    f"### ⭐ {name}"
                )

                if reason:

                    st.write(
                        reason
                    )

                if best_for:

                    st.caption(
                        "Best for: "
                        + ", ".join(
                            map(str, best_for)
                        )
                    )

                st.divider()


    # =====================================================
    # PACKING CHECKLIST
    # =====================================================

    with packing_tab:

        st.header(
            "🎒 AI Packing Checklist"
        )

        packing_list = trip.get(
            "packing_list",
            [],
        )

        if (
            not isinstance(
                packing_list,
                list,
            )
            or not packing_list
        ):

            st.info(
                "No packing checklist was returned."
            )

        else:

            st.write(
                "Tick the items as you pack:"
            )

            for index, item in enumerate(
                packing_list
            ):

                st.checkbox(
                    str(item),
                    key=f"packing_{index}",
                )


    # =====================================================
    # MAP
    # =====================================================

    with map_tab:

        st.header(
            "🗺️ Travel Locations"
        )

        st.write(
            "Search itinerary places on OpenStreetMap."
        )

        places = []

        for day in trip.get(
            "itinerary",
            [],
        ):

            if not isinstance(
                day,
                dict,
            ):
                continue

            for period in [
                "morning",
                "afternoon",
                "evening",
            ]:

                section = day.get(
                    period,
                    {},
                )

                if not isinstance(
                    section,
                    dict,
                ):
                    continue

                day_places = section.get(
                    "places",
                    [],
                )

                if isinstance(
                    day_places,
                    list,
                ):

                    places.extend(
                        day_places
                    )

        unique_places = []

        for place in places:

            place = normalize_place_name(place)

            if (
                place
                and place not in unique_places
            ):

                unique_places.append(
                    place
                )

        if not unique_places:

            st.info(
                "No places were found in the itinerary."
            )

        else:

            for place in unique_places:

                search_query = (
                    f"{place}, "
                    f"{trip_destination}"
                )

                map_url = (
                    "https://www.openstreetmap.org/"
                    "search?query="
                    + quote_plus(search_query)
                )

                st.markdown(
                    f"- [{place}]({map_url})"
                )


    # =====================================================
    # SAVE TRIP
    # =====================================================

    with save_tab:

        st.header(
            "💾 Save Your Trip"
        )

        trip_name = st.text_input(
            "Trip name",
            value=f"{trip_destination} Trip",
        )

        save_button = st.button(
            "💾 Save This Trip",
            type="primary",
        )

        if save_button:

            if not trip_name.strip():

                st.error(
                    "Please enter a trip name."
                )

            else:

                try:

                    trip_id = save_trip(
                        trip_name.strip(),
                        str(trip_destination),
                        normalize_trip_data(trip),
                    )

                    st.success(
                        f"✅ Trip saved successfully! "
                        f"Trip ID: {trip_id}"
                    )

                except Exception as exc:

                    st.error(
                        f"Unable to save trip: {exc}"
                    )


# =========================================================
# AI TRAVEL ASSISTANT
# =========================================================

st.divider()

st.subheader(
    "🤖 AI Travel Assistant"
)

if trip:

    st.write(
        "Ask questions about your generated trip."
    )

    user_message = st.chat_input(
        "Ask about your current trip..."
    )

    if user_message:

        st.session_state.chat.append(
            (
                "user",
                user_message,
            )
        )

        try:

            answer = generate_chat_reply(
                trip,
                user_message,
            )

            st.session_state.chat.append(
                (
                    "assistant",
                    answer,
                )
            )

        except AIServiceError as exc:

            st.error(
                str(exc)
            )

        except Exception as exc:

            st.error(
                f"Chatbot error: {exc}"
            )

    # Display chat messages

    for role, message in st.session_state.chat:

        with st.chat_message(role):

            st.write(message)

else:

    st.info(
        "Generate a trip first to activate "
        "the trip-aware AI assistant."
    )


# =========================================================
# SAVED TRIPS
# =========================================================

st.divider()

st.subheader(
    "💾 Saved Trips"
)

try:

    saved_trips = list_trips()

except Exception as exc:

    st.error(
        f"Unable to load saved trips: {exc}"
    )

    saved_trips = []


if saved_trips:

    for saved_trip in saved_trips:

        col1, col2, col3 = st.columns(
            [5, 1, 1]
        )

        with col1:

            st.write(
                f"**{saved_trip['trip_name']}** "
                f"— {saved_trip['destination']} "
                f"— {saved_trip['created_at']}"
            )

        with col2:

            if st.button(
                "📂 Load",
                key=f"load_trip_{saved_trip['id']}",
            ):

                try:

                    loaded_trip = get_trip(
                        saved_trip["id"]
                    )

                    if loaded_trip:

                        st.session_state.trip = (
                            normalize_trip_data(
                                loaded_trip["trip_data"]
                            )
                        )

                        st.session_state.chat = []

                        st.success(
                            "Trip loaded successfully!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Trip could not be found."
                        )

                except Exception as exc:

                    st.error(
                        f"Unable to load trip: {exc}"
                    )

        with col3:

            if st.button(
                "🗑️ Delete",
                key=f"delete_trip_{saved_trip['id']}",
            ):

                try:

                    delete_trip(
                        saved_trip["id"]
                    )

                    st.success(
                        "Trip deleted successfully!"
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Unable to delete trip: {exc}"
                    )

else:

    st.caption(
        "No saved trips yet."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "✈️ AI Smart Travel Planner | "
    "Powered by OpenAI + Streamlit + SQLite"
)
