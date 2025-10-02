import sys
from argparse import Namespace
from types import ModuleType

import pytest

from llm_backends import LLMError, LocalLlamaLLM
from scripts.run_generator_local import _preflight


def test_local_llm_requires_model_path(monkeypatch):
    monkeypatch.delenv("LLAMA_MODEL_PATH", raising=False)
    with pytest.raises(LLMError):
        LocalLlamaLLM()


def test_local_llm_accepts_explicit_file(tmp_path):
    dummy = tmp_path / "model.gguf"
    dummy.write_text("test")
    llm = LocalLlamaLLM(model=str(dummy))
    assert llm.model == str(dummy)
    assert llm.model_path == dummy


def test_preflight_validates_and_discovers_model(tmp_path, monkeypatch):
    module = ModuleType("llama_cpp")
    monkeypatch.setitem(sys.modules, "llama_cpp", module)
    folder = tmp_path / "modeldir"
    folder.mkdir()
    gguf = folder / "model.gguf"
    gguf.write_text("dummy")
    args = Namespace(backend=None, model=str(folder))
    _preflight(args)
    assert args.backend == "local-llama"
    assert args.model == str(gguf)


def test_preflight_rejects_wrong_backend(monkeypatch):
    module = ModuleType("llama_cpp")
    monkeypatch.setitem(sys.modules, "llama_cpp", module)
    args = Namespace(backend="openai", model=None)
    with pytest.raises(RuntimeError):
        _preflight(args)
