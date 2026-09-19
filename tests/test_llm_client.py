import pytest

from src.llm_client import parse_json_response


def test_parse_json_response_plain():
    assert parse_json_response('{"a": 1}') == {"a": 1}


def test_parse_json_response_code_fenced():
    assert parse_json_response('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_json_response_with_surrounding_prose():
    assert parse_json_response('Sure, here you go: {"a": 1} hope that helps') == {"a": 1}


def test_parse_json_response_raises_on_no_json():
    with pytest.raises(ValueError):
        parse_json_response("no json here")
