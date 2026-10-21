import json
import re

FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _first_json_block(text: str):
    """Decode the first {...} or [...] found in text, or raise ValueError."""
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "{[":
            try:
                return decoder.raw_decode(text[i:])[0]
            except ValueError:
                continue
    raise ValueError("no JSON found")


def safe_json_parse(text):
    if isinstance(text, (dict, list)):
        return text
    if not isinstance(text, str):
        return {"raw_response": text}

    candidates = [text.strip()]
    # small models often wrap JSON in ```json fences or add prose around it
    candidates += [m.strip() for m in FENCE.findall(text)]

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except Exception:
            pass
    for candidate in candidates:
        try:
            return _first_json_block(candidate)
        except ValueError:
            pass

    # MODEL MAY RETURN RAW TEXT — fallback into a wrapped dict
    return {"raw_response": text}
