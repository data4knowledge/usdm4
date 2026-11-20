"""tools/fix_usdm.py, the command line for USDM4().fix() (GitHub 106)."""

import json

from tools import fix_usdm

DATA = {
    "id": "S",
    "instanceType": "Study",
    "codes": [
        {"id": "C", "code": "C1", "decode": "x", "instanceType": "Code"},
        {"id": "C", "code": "C1", "decode": "x", "instanceType": "Code"},
    ],
}


def write_input(tmp_path):
    source = tmp_path / "in.json"
    source.write_text(json.dumps(DATA))
    return source


def test_fix_writes_output_and_log(tmp_path, capsys):
    source = write_input(tmp_path)
    output = tmp_path / "out.json"
    assert fix_usdm.main([str(source), str(output), "--no-ct"]) == 0
    assert [c["id"] for c in json.loads(output.read_text())["codes"]] == ["C", "C_2"]
    log = json.loads((tmp_path / "out.log.json").read_text())
    assert log["summary"]["changes"] == {"ids": 1}
    assert json.loads(source.read_text()) == DATA
    assert "Changes {'ids': 1}" in capsys.readouterr().out


def test_log_path_and_steps_off(tmp_path, capsys):
    source = write_input(tmp_path)
    output = tmp_path / "out.json"
    log = tmp_path / "audit.json"
    args = [str(source), str(output), "--no-ids", "--no-ct", "--log", str(log)]
    assert fix_usdm.main(args) == 0
    assert json.loads(output.read_text()) == DATA
    assert json.loads(log.read_text())["changes"] == []
    assert "Changes 0" in capsys.readouterr().out


def test_missing_input(tmp_path, capsys):
    assert fix_usdm.main([str(tmp_path / "none.json"), str(tmp_path / "o.json")]) == 1
    assert "not found" in capsys.readouterr().err


def test_output_must_not_be_input(tmp_path, capsys):
    source = write_input(tmp_path)
    assert fix_usdm.main([str(source), str(source)]) == 1
    assert "must not be the input" in capsys.readouterr().err
    assert json.loads(source.read_text()) == DATA
