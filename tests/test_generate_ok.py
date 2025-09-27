from pathlib import Path

from fastapi.testclient import TestClient

from app import app
from llm_backends import CloudLLM
from scripts.run_generator import (
    DEFAULT_API_URL,
    build_payload,
    call_generator,
    format_response_summary,
)


def mock_generate(self, system: str, user: str) -> str:
    return (
        "// FILE: ExamplePort_versioned.h\n```c\nv1\n```\n"
        "// FILE: Converter_ExamplePort.h\n```c\nv2\n```\n"
        "// FILE: Converter_ExamplePort.cpp\n```cpp\nv3\n```\n"
        "// FILE: converters.cpp\n```cpp\nv4\n```"
    )


def assert_success_response(data):
    assert data["root"] == "ExamplePort"
    names = {f["name"] for f in data["files"]}
    assert names == {
        "ExamplePort_versioned.h",
        "Converter_ExamplePort.h",
        "Converter_ExamplePort.cpp",
        "converters.cpp",
    }
    for f in data["files"]:
        assert f["content"]
    assert data["zip_base64"]


def test_generate_ok(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(CloudLLM, "generate", mock_generate)
    client = TestClient(app)
    fixtures = Path(__file__).parent / "fixtures"
    payload = build_payload(
        root="ExamplePort",
        old_header_path=fixtures / "old_header.h",
        new_header_path=fixtures / "new_header.h",
    )
    resp = client.post("/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert_success_response(data)


def test_call_generator_matches_cli(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(CloudLLM, "generate", mock_generate)
    client = TestClient(app)
    fixtures = Path(__file__).parent / "fixtures"
    payload = build_payload(
        root="ExamplePort",
        old_header_path=fixtures / "old_header.h",
        new_header_path=fixtures / "new_header.h",
    )

    def fake_post(url, json, timeout):
        assert url == DEFAULT_API_URL
        resp = client.post("/generate", json=json)

        class _Wrapper:
            def __init__(self, inner):
                self._inner = inner

            def raise_for_status(self):
                self._inner.raise_for_status()

            def json(self):
                return self._inner.json()

        return _Wrapper(resp)

    monkeypatch.setattr("scripts.run_generator.requests.post", fake_post)
    data = call_generator(DEFAULT_API_URL, payload)
    assert_success_response(data)
    summary_lines = list(format_response_summary(data))
    assert any("ExamplePort_versioned.h" in line for line in summary_lines)

