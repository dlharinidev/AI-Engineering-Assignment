import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_test_cases(combined_text: str):
    prompt = f"""
    Based on the following technical manual section, generate 3-5 QA test cases.
    Each test case should have a 'title', 'steps', and 'expected_result'.
    
    Format the response as a JSON list.
    
    Section Content:
    {combined_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        raw_content = response.choices[0].message.content
        return json.loads(raw_content)
    except Exception as e:
        # "It usually works" is not a design. Handle failure.
        return {
            "error": "Failed to generate structured output",
            "raw_log": str(e),
            "fallback_test_cases": []
        }