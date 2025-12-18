import pytest

from kaig.llm import extract_json


@pytest.mark.parametrize(
    "code,expected",
    [
        (
            """```json
    {"name":"martin"}
    ```""",
            '{"name":"martin"}',
        ),
        (
            """```
    { "name": "martin" }
    ```""",
            '{ "name": "martin" }',
        ),
        (
            'Json: "{ "user": {"name":"martin"} }"',
            '{ "user": {"name":"martin"} }',
        ),
        (
            '{"name":"martin"}"',
            '{"name":"martin"}',
        ),
    ],
)
def test_extract_json(code: str, expected: str):
    assert extract_json(code) == expected
