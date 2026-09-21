"""WIERZ-D0402 (--version global) y D0202 (audit/report comparten la recolección)."""

from typer.testing import CliRunner
from wierzbowski import __version__
from wierzbowski.cli import app

runner = CliRunner()


def test_version_opcion_global():
    for flag in ("--version", "-v"):
        res = runner.invoke(app, [flag])
        assert res.exit_code == 0 and __version__ in res.output


def test_audit_y_report_coinciden(tmp_path):
    (tmp_path / "a.h").write_text("#ifndef A_H\n#define A_H\n#include \"b.h\"\n#endif\n")
    (tmp_path / "b.h").write_text("#ifndef B_H\n#define B_H\n#include \"a.h\"\n#endif\n")
    md = tmp_path / "audit.md"
    runner.invoke(app, ["audit", str(tmp_path), "--md", str(md)])
    rep = runner.invoke(app, ["report", str(tmp_path)])
    assert md.read_text().strip() == rep.output.strip()
