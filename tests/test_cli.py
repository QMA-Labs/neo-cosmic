import json

from neo.cli import main


def test_memory_cli_round_trip(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setenv("NEO_DATA_DIR", str(tmp_path))
    assert main(["memory", "set", "hello", '{"world":true}']) == 0
    capsys.readouterr()
    assert main(["memory", "get", "hello"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["value"] == {"world": True}


def test_status_is_valid_json(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setenv("NEO_DATA_DIR", str(tmp_path))
    assert main(["status"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["storage"]["path"] == str(tmp_path)
    assert result["model"]["model"] in {"qwen3.5:9b", "qwen3.5:0.8b"}
