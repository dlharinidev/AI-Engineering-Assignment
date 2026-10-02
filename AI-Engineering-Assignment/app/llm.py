import os
import json

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def generate_test_cases(combined_text: str):
    """Generate QA test cases from manual section text.

    Tries OpenAI gpt-4o with JSON structured output.
    Falls back to mock test cases if no API key or if call fails.
    """
    prompt = f"""
    Based on the following technical manual section, generate 3-5 QA test cases.
    Each test case should have a 'title', 'steps' (a list of strings), and 'expected_result'.

    Return a JSON object with a single key "test_cases" containing a list of test case objects.

    Section Content:
    {combined_text}
    """

    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            raw_content = response.choices[0].message.content
            parsed = json.loads(raw_content)
            # Normalise: accept both {"test_cases": [...]} and a bare list
            if isinstance(parsed, list):
                return parsed
            return parsed.get("test_cases", parsed)
        except Exception as e:
            # Log error but fall through to mock
            print(f"[LLM] OpenAI call failed: {e}")

    # ── Fallback mock test cases (used when no API key or on failure) ──
    return [
        {
            "title": "Verify cuff pressure safety cutoff",
            "steps": [
                "Attach the cuff to the device.",
                "Initiate a measurement cycle.",
                "Simulate pressure exceeding the safety threshold."
            ],
            "expected_result": "Device deflates cuff automatically and displays the correct error code."
        },
        {
            "title": "Verify battery installation",
            "steps": [
                "Open the battery compartment.",
                "Insert 4 AA batteries with correct polarity.",
                "Close the compartment and power on."
            ],
            "expected_result": "Device powers on and displays the home screen without error."
        },
        {
            "title": "Verify measurement display",
            "steps": [
                "Press the START button.",
                "Wait for cuff to inflate and deflate.",
                "Observe the reading on the display."
            ],
            "expected_result": "Systolic, diastolic, and pulse values are shown on the display."
        }
    ]