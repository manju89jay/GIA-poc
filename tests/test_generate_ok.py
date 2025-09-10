from pathlib import Path

from fastapi.testclient import TestClient

from app import app
from llm_backends import CloudLLM


def mock_generate(self, system: str, user: str) -> str:
    return (
        "// FILE: HPSD_HealthVectorPort_versioned.h\n```c\nv1\n```\n"
        "// FILE: Converter_HPSD_HealthVectorPort.h\n```c\nv2\n```\n"
        "// FILE: Converter_HPSD_HealthVectorPort.cpp\n```cpp\nv3\n```\n"
        "// FILE: converters.cpp\n```cpp\nv4\n```"
    )


def test_generate_ok(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(CloudLLM, "generate", mock_generate)
    client = TestClient(app)
    fixtures = Path(__file__).parent / "fixtures"
    old_header = (fixtures / "old_header.h").read_text()
    new_header = (fixtures / "new_header.h").read_text()
    payload = {
        "root": "HPSD_HealthVectorPort",
        "old_header": old_header,
        "new_header": new_header,
        "backend": "openai",
        "return_zip": True,
    }
    resp = client.post("/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["root"] == "HPSD_HealthVectorPort"
    names = {f["name"] for f in data["files"]}
    assert names == {
        "HPSD_HealthVectorPort_versioned.h",
        "Converter_HPSD_HealthVectorPort.h",
        "Converter_HPSD_HealthVectorPort.cpp",
        "converters.cpp",
    }
    for f in data["files"]:
        assert f["content"]
    assert data["zip_base64"]
