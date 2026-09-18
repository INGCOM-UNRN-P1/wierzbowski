"""Regresión de WIERZ-D0303: el aviso de guarda no estándar era una rama muerta.

`check_header_guard` devolvía `(True, "Guard no estándar: ...")` y nadie mostraba
la nota; además `VECTOR_H` en `lista.h` pasaba como válida por terminar en `_H`,
y dos cabeceras con la misma guarda (encabezado copiado) no se detectaban.
"""

import json

import pytest
from typer.testing import CliRunner

from wierzbowski.cli import app
from wierzbowski.core.guard_checker import auditar_guardas, check_header_guard, inspeccionar_guarda
from wierzbowski.plugins.ripley_plugin import WierzbowskiPlugin

runner = CliRunner()


def _h(tmp_path, nombre, guarda, cuerpo="int x;\n"):
    ruta = tmp_path / nombre
    ruta.write_text(f"#ifndef {guarda}\n#define {guarda}\n{cuerpo}#endif\n", encoding="utf-8")
    return ruta


@pytest.mark.parametrize(
    "nombre, guarda",
    [
        ("lista.h", "LISTA_H"),
        ("lista.h", "PROYECTO_LISTA_H"),
        ("lista.h", "LISTA_H_"),
        ("lista.h", "__LISTA_H__"),
        ("tda-pila.h", "TDA_PILA_H"),
    ],
)
def test_las_convenciones_habituales_no_generan_aviso(tmp_path, nombre, guarda):
    assert inspeccionar_guarda(_h(tmp_path, nombre, guarda)) == (True, guarda, None)


def test_una_guarda_de_otro_archivo_genera_aviso_aunque_termine_en_H(tmp_path):
    tiene, macro, aviso = inspeccionar_guarda(_h(tmp_path, "lista.h", "VECTOR_H"))
    assert tiene and macro == "VECTOR_H"
    assert "LISTA_H" in aviso


def test_pragma_once_no_tiene_macro_ni_aviso(tmp_path):
    ruta = tmp_path / "p.h"
    ruta.write_text("#pragma once\nint x;\n", encoding="utf-8")
    assert inspeccionar_guarda(ruta) == (True, None, None)
    assert check_header_guard(ruta) == (True, "#pragma once")


def test_una_cabecera_sin_guarda_es_un_problema(tmp_path):
    ruta = tmp_path / "s.h"
    ruta.write_text("int sin_guarda;\n", encoding="utf-8")
    problemas, avisos = auditar_guardas([ruta])
    assert problemas == ["s.h: Falta guarda de inclusión"]
    assert avisos == []


def test_dos_cabeceras_con_la_misma_guarda_son_un_problema(tmp_path):
    a = _h(tmp_path, "lista.h", "VECTOR_H")
    b = _h(tmp_path, "vector.h", "VECTOR_H")
    problemas, avisos = auditar_guardas([a, b])
    assert len(problemas) == 2
    assert any(p.startswith("lista.h:") and "vector.h" in p for p in problemas)
    assert any(p.startswith("vector.h:") and "lista.h" in p for p in problemas)
    assert len(avisos) == 1 and avisos[0].startswith("lista.h:")


def test_una_guarda_con_nombre_incorrecto_pero_unica_no_hace_fallar_la_auditoria(tmp_path):
    _h(tmp_path, "lista.h", "OTRA_H")
    res = runner.invoke(app, ["audit", str(tmp_path), "--json"])
    assert res.exit_code == 0, res.output
    datos = json.loads(res.output)
    assert datos["passed"] is True
    assert datos["guard_issues"] == []
    assert len(datos["guard_notes"]) == 1


def test_una_guarda_duplicada_hace_fallar_la_auditoria(tmp_path):
    _h(tmp_path, "lista.h", "VECTOR_H")
    _h(tmp_path, "vector.h", "VECTOR_H")
    res = runner.invoke(app, ["audit", str(tmp_path), "--json"])
    assert res.exit_code == 1
    assert len(json.loads(res.output)["guard_issues"]) == 2


def test_el_aviso_se_muestra_en_la_terminal_y_en_markdown(tmp_path):
    _h(tmp_path, "lista.h", "OTRA_H")
    res = runner.invoke(app, ["audit", str(tmp_path)])
    assert "OTRA_H" in res.output and "no corresponde" in res.output

    salida = tmp_path / "r.md"
    res = runner.invoke(app, ["audit", str(tmp_path), "--md", str(salida)])
    assert res.exit_code == 0
    assert "OTRA_H" in salida.read_text(encoding="utf-8")

    res = runner.invoke(app, ["report", str(tmp_path)])
    assert "OTRA_H" in res.output


def test_el_plugin_reporta_la_colision_y_los_avisos(tmp_path):
    _h(tmp_path, "lista.h", "VECTOR_H")
    _h(tmp_path, "vector.h", "VECTOR_H")
    resultado = WierzbowskiPlugin().run({"source_dir": str(tmp_path)})
    assert resultado["passed"] is False
    assert len(resultado["guard_errors"]) == 2
    assert len(resultado["guard_notes"]) == 1
