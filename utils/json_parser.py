import json

def safe_json_parse(text: str):
    try:
        return json.loads(text)
    except Exception:
        # MODEL MAY RETURN RAW TEXT — fallback into a wrapped dict
        return {"raw_response": text}
