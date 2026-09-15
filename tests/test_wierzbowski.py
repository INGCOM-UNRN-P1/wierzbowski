"""Tests unitarios y de integración para WIERZBOWSKI."""

import json
from pathlib import Path
from typer.testing import CliRunner
from wierzbowski.cli import app
from wierzbowski.core.header_graph import build_dependency_graph, detect_cycles
from wierzbowski.core.guard_checker import check_header_guard, lint_makefile
from wierzbowski.plugins.ripley_plugin import WierzbowskiPlugin

runner = CliRunner()


def test_cli_doctor():
    res = runner.invoke(app, ["doctor"])
    assert res.exit_code == 0
    assert "doctor" in res.output.lower()

    res_json = runner.invoke(app, ["doctor", "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert data["herramienta"] == "wierzbowski"
    assert data["ok"] is True


def test_detect_circular_dependency(tmp_path):
    a = tmp_path / "a.h"
    b = tmp_path / "b.h"
    a.write_text('#ifndef A_H\n#define A_H\n#include "b.h"\n#endif')
    b.write_text('#ifndef B_H\n#define B_H\n#include "a.h"\n#endif')

    nodes = build_dependency_graph(tmp_path)
    cycles = detect_cycles(nodes)
    assert len(cycles) > 0


def test_header_guard_checker(tmp_path):
    good = tmp_path / "good.h"
    good.write_text("#ifndef GOOD_H\n#define GOOD_H\nint x;\n#endif")
    ok, _ = check_header_guard(good)
    assert ok is True

    bad = tmp_path / "bad.h"
    bad.write_text("int sin_guarda;\n")
    bad_ok, _ = check_header_guard(bad)
    assert bad_ok is False


def test_makefile_linter_spaces(tmp_path):
    mk = tmp_path / "Makefile"
    mk.write_text("all:\n    gcc main.c\n")
    issues = lint_makefile(mk)
    assert any(i.code == "MKF001" for i in issues)


def test_cli_audit_json(tmp_path):
    h = tmp_path / "modulo.h"
    h.write_text("#pragma once\nint foo(void);")
    res = runner.invoke(app, ["audit", str(tmp_path), "--json"])
    assert res.exit_code == 0
    assert '"passed": true' in res.output


def test_cli_version():
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert "WIERZBOWSKI" in res.output


def test_ripley_plugin(tmp_path):
    h = tmp_path / "ok.h"
    h.write_text("#pragma once\nint bar(void);")
    plugin = WierzbowskiPlugin()
    res = plugin.run({"source_dir": str(tmp_path)})
    assert res["passed"] is True
    assert "cycles" in res
