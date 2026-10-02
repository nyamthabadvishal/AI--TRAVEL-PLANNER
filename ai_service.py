import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from travel_utils import normalize_trip_data

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
if load_dotenv is not None:
    load_dotenv(dotenv_path=BASE_DIR / ".env")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", os.getenv("OPENAI_MODEL", "llama3.2"))


# ---------------------------------------------------------
# CUSTOM ERROR
# ---------------------------------------------------------

class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass


# ---------------------------------------------------------
# OLLAMA CLIENT
# ---------------------------------------------------------

def _ollama_request(payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise AIServiceError(
            "Ollama is not reachable. Start Ollama locally and run "
            "'ollama pull llama3.2' if needed."
        ) from exc
    except Exception as exc:
        raise AIServiceError(f"Ollama request failed: {exc}") from exc


# ---------------------------------------------------------
# CLEAN JSON RESPONSE
# ---------------------------------------------------------

def _extract_json(text: str) -> dict[str, Any]:
    """
    Convert the model's response into a Python dictionary.

    Handles:
    - Normal JSON
    - ```json ... ```
    - Text before/after JSON
    """

    if not text:
        raise AIServiceError("The model returned an empty response.")

    text = text.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        possible_json = text[start:end + 1]
        try:
            result = json.loads(possible_json)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    raise AIServiceError(
        "The model returned a response that could not be converted to JSON."
    )


# ---------------------------------------------------------
# GENERATE JSON
# ---------------------------------------------------------

def _generate_json(
    instructions: str,
    prompt: str,
) -> dict[str, Any]:
    payload = {
        "model": MODEL_NAME,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt},
        ],
    }

    try:
        response = _ollama_request(payload)
        raw_response = response.get("message", {}).get("content", "").strip()

        if not raw_response:
            raise AIServiceError("Ollama returned an empty JSON response.")

        return _extract_json(raw_response)
    except AIServiceError:
        raise
    except Exception as exc:
        raise AIServiceError(f"Ollama API request failed: {exc}") from exc


def generate_travel_plan(
    destination: str,
    days: int,
    travelers: int,
    budget: float,
    travel_type: str,
    interests: list[str],
) -> dict[str, Any]:

    instructions = """
You are an expert AI travel planner.

Your task is to create practical,
personalized and realistic travel plans.

IMPORTANT:

The final response MUST be valid JSON.

Return JSON only.

Do not use Markdown.

Do not write explanations outside JSON.

Do not use code blocks.

Never claim that prices have been verified live.

Never claim hotel availability has been verified live.

Never claim transport schedules have been verified live.

All prices are planning estimates.

Avoid false precision.

The JSON object MUST contain these top-level keys:

trip_summary
itinerary
budget
recommendations
packing_list

The itinerary must contain exactly one object
for every requested travel day.

Each itinerary day must contain:

day
title
morning
afternoon
evening
tips

Each morning, afternoon and evening section
must contain:

places
activities
food
estimated_cost

The budget object must contain:

accommodation
food
transport
activities
shopping_misc
emergency_buffer
total_estimated

Recommendations must contain objects with:

name
reason
best_for

packing_list must be an array of strings.

Make sure the entire response is valid JSON.
""".strip()

    interests_text = ", ".join(interests) if interests else "General sightseeing"

    prompt = f"""
Create a complete AI travel plan.

TRIP INFORMATION

Destination:
{destination}

Number of days:
{days}

Number of travelers:
{travelers}

Travel type:
{travel_type}

Total budget:
₹{budget:,.0f}

Interests:
{interests_text}


REQUIREMENTS

1. Return the complete answer as valid JSON.

2. Create exactly {days} itinerary day objects.

3. Make the itinerary suitable for {travelers} traveler(s).

4. Respect the travel type: {travel_type}.

5. Consider these interests: {interests_text}.

6. Keep the estimated trip cost reasonably close to the provided budget.

7. Include accommodation estimates.

8. Include food estimates.

9. Include transportation estimates.

10. Include activity estimates.

11. Include shopping and miscellaneous expenses.

12. Include an emergency buffer.

13. Include local food suggestions.

14. Include practical activities.

15. Include practical travel tips.

16. Create personalized recommendations.

17. Create a useful packing checklist.

18. Do not claim that prices are live.

19. Do not claim that hotel availability is currently verified.

20. Do not claim that transport schedules are currently verified.

21. Treat all prices as estimates.

22. Return JSON only.

23. Do not use Markdown.

24. Do not use code blocks.

25. The final answer must be a valid JSON object.
""".strip()

    generated_trip = _generate_json(instructions, prompt)
    return normalize_trip_data(generated_trip)


# ---------------------------------------------------------
# GENERATE PACKING LIST
# ---------------------------------------------------------

def generate_packing_list(
    destination: str,
    days: int,
    travel_type: str,
    interests: list[str],
) -> list[str]:

    instructions = """
You are an expert travel packing assistant.

Create a practical packing checklist.

IMPORTANT:

The final response MUST be valid JSON.

The JSON structure must be:

{
    "packing_list": [
        "item 1",
        "item 2"
    ]
}

Return JSON only.

Do not use Markdown.

Do not use code blocks.

Do not write explanations outside JSON.
""".strip()

    interests_text = ", ".join(interests) if interests else "General travel"

    prompt = f"""
Create a travel packing checklist.

Destination:
{destination}

Number of days:
{days}

Travel type:
{travel_type}

Interests:
{interests_text}

Create useful packing items based on:

- destination
- trip duration
- travel type
- interests

Return valid JSON only.

The JSON must contain:

packing_list

The packing_list must be an array of strings.

The final answer must be valid JSON.
""".strip()

    result = _generate_json(instructions, prompt)
    packing_list = result.get("packing_list", [])

    if not isinstance(packing_list, list):
        return []

    return [str(item) for item in packing_list]


# ---------------------------------------------------------
# AI TRAVEL CHATBOT
# ---------------------------------------------------------

def generate_chat_reply(
    trip: dict[str, Any],
    user_message: str,
) -> str:

    trip_context = json.dumps(trip, ensure_ascii=False, indent=2)

    chat_prompt = f"""
You are an AI travel assistant.

Use the following trip information to answer the user's question.

CURRENT TRIP:

{trip_context}


USER QUESTION:

{user_message}


IMPORTANT:

Give a practical and concise answer.

Do not invent live information.

Do not claim that prices are currently verified.

Do not claim hotel availability is currently verified.

Do not claim transport schedules are currently verified.

If information may have changed, tell the user to verify it before booking.

This is a normal conversational response, so DO NOT return JSON for this chatbot request.
""".strip()

    payload = {
        "model": MODEL_NAME,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful AI travel assistant. Answer questions about the user's current trip. Use the provided trip context. Keep answers useful, clear and concise. Do not claim unverified live information. This chatbot response does not need to be JSON.",
            },
            {"role": "user", "content": chat_prompt},
        ],
    }

    try:
        response = _ollama_request(payload)
        answer = response.get("message", {}).get("content", "").strip()
        if not answer:
            return "Sorry, I could not generate an answer right now."
        return answer
    except AIServiceError:
        raise
    except Exception as exc:
        raise AIServiceError(f"Ollama chatbot request failed: {exc}") from exc
