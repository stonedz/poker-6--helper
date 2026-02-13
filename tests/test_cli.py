import json

from shortdeck_cli.cli import main
from shortdeck_cli.cli import cli_main


def test_cli_main_happy_path(monkeypatch, capsys):
    user_inputs = iter(["AKs", "5", "3", "2"])
    monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))

    main()

    output = capsys.readouterr().out
    assert "Hero position options:" in output
    assert "=== New Hand ===" in output
    assert "Hero: AKs @ CO" in output
    assert "Villain: MP2 did limp" in output
    assert "Scenario key: vs_limp:CO_vs_MP_limp" in output
    assert "Data recommendation:" in output
    assert "Session ended." in output


def test_cli_main_retries_invalid_then_accepts(monkeypatch, capsys):
    user_inputs = iter(["AK", "AKs", "9", "4", "9", "2", "9", "3"])
    monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))

    main()

    output = capsys.readouterr().out
    assert output.count("Invalid input:") >= 4
    assert "Hero: AKs @ HJ" in output
    assert "Scenario key: vs_all_in:HJ_vs_MP_all_in" in output
    assert "Data recommendation:" in output
    assert "Session ended." in output


def test_cli_auto_advance_and_reset(monkeypatch, capsys):
    user_inputs = iter(["AKs", "5", "3", "2", "00", "AA", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(user_inputs))

    main()

    output = capsys.readouterr().out
    assert "Hero: AKs @ CO" in output
    assert "Reset requested." in output
    assert "UTG turn: no prior player action." in output
    assert "Hero: AA @ UTG" in output
    assert "Villain: N/A (UTG open spot)" in output
    assert "Scenario key: open:UTG_rfi" in output


def test_cli_auto_mode_processes_jsonl_observation(tmp_path, capsys):
    payload = {
        "hero_hand": "AsAd",
        "hero_position": "CO",
        "villain_position": "UTG",
        "villain_action": "limp",
        "confidence": 0.42,
        "source": "pokerstars",
    }
    source_file = tmp_path / "obs.jsonl"
    source_file.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    cli_main(["--auto", "--auto-source-jsonl", str(source_file), "--auto-max-hands", "1", "--auto-poll-seconds", "0"])

    output = capsys.readouterr().out
    assert "=== Short Deck (6+) Auto Mode ===" in output
    assert "Warning: low confidence from pokerstars" in output
    assert "Hero: AsAd @ CO" in output
    assert "Villain: UTG did limp" in output
    assert "Scenario key: vs_limp:CO_vs_UTG_limp" in output
    assert "Auto mode finished." in output


def test_cli_auto_mode_utg_observation_does_not_require_villain_fields(tmp_path, capsys):
    payload = {
        "hero_hand": "KQs",
        "hero_position": "UTG",
    }
    source_file = tmp_path / "obs_utg.jsonl"
    source_file.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    cli_main(["--auto", "--auto-source-jsonl", str(source_file), "--auto-max-hands", "1", "--auto-poll-seconds", "0"])

    output = capsys.readouterr().out
    assert "Hero: KQs @ UTG" in output
    assert "Villain: N/A (UTG open spot)" in output
    assert "Scenario key: open:UTG_rfi" in output
