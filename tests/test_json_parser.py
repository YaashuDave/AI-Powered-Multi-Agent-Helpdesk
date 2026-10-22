from utils.json_parser import safe_json_parse


def test_plain_json():
    assert safe_json_parse('{"a": 1}') == {"a": 1}
    assert safe_json_parse('["s1", "s2"]') == ["s1", "s2"]


def test_code_fence():
    assert safe_json_parse('```json\n{"escalate": true}\n```') == {"escalate": True}


def test_json_inside_prose():
    text = 'Sure! Here are the steps: {"steps": ["reset"]} Hope it helps.'
    assert safe_json_parse(text) == {"steps": ["reset"]}


def test_already_parsed():
    assert safe_json_parse({"x": 1}) == {"x": 1}


def test_fallback_keeps_raw_text():
    assert safe_json_parse("no json here") == {"raw_response": "no json here"}
    assert safe_json_parse("{broken") == {"raw_response": "{broken"}
