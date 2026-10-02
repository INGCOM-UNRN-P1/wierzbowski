"""Reglas de la cátedra sobre Makefiles (antes dredd audit-makefile) y grafo en Mermaid."""

import json

from typer.testing import CliRunner

from wierzbowski.cli import app
from wierzbowski.core.makefile_catedra import reglas_catedra

runner = CliRunner()

BUENO = """CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -g
.PHONY: all clean

all: app

app: main.o
\t$(CC) $(CFLAGS) main.o -o app -lm

clean:
\trm -f *.o app
"""


def _codigos(texto, **kw):
    return {i.code for i in reglas_catedra(texto, **kw)}


def test_makefile_correcto_sin_observaciones():
    assert _codigos(BUENO) == set()


def test_flags_obligatorios_y_phony():
    sin_flags = BUENO.replace("CFLAGS = -Wall -Wextra -std=c11 -g", "CFLAGS = -g")
    assert "MKF004" in _codigos(sin_flags)
    test_fuera = BUENO + "\ntest: app\n\t./app\n"
    assert "MKF005" in _codigos(test_fuera)


def test_trampas():
    texto = BUENO + "\ntrampa:\n\tgcc -w x.c || true\n\tcurl http://x\n\tcp ../modelo.o .\n\tgcc a.c -lssl\n"
    assert {"MKF010", "MKF011", "MKF012", "MKF013", "MKF014"} <= _codigos(texto)
    assert "MKF015" in _codigos("CC = ./trampa.sh\n" + BUENO)


def test_comando_makefile(tmp_path):
    (tmp_path / "Makefile").write_text(BUENO + "\nx:\n\tgcc a.c -lssl\n", encoding="utf-8")
    res = runner.invoke(app, ["makefile", str(tmp_path), "--json"])
    datos = json.loads(res.stdout)
    assert res.exit_code == 1 and [o["code"] for o in datos["observaciones"]] == ["MKF014"]
    assert runner.invoke(app, ["makefile", str(tmp_path), "--librerias", "m,ssl"]).exit_code == 0


def test_grafo_mermaid(tmp_path):
    (tmp_path / "a.h").write_text('#ifndef A_H\n#define A_H\n#include "b.h"\n#endif\n', encoding="utf-8")
    (tmp_path / "b.h").write_text('#ifndef B_H\n#define B_H\n#include "a.h"\n#endif\n', encoding="utf-8")
    res = runner.invoke(app, ["audit", str(tmp_path), "--mermaid"])
    assert "graph LR" in res.stdout and "n_a_h --> n_b_h" in res.stdout and "fill:#fdd" in res.stdout
