from shortdeck_cli.cli import main


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
