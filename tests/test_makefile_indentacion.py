"""WIERZ-D0304: MKF001 detecta recetas con espacios sin importar cuántos sean."""

import pytest
from wierzbowski.core.guard_checker import lint_makefile


@pytest.mark.parametrize("espacios", [1, 2, 3, 4, 8])
def test_receta_con_espacios(tmp_path, espacios):
    mk = tmp_path / "Makefile"
    mk.write_text("all:\n" + " " * espacios + "gcc -o x x.c\n")
    assert any(i.code == "MKF001" for i in lint_makefile(mk))


def test_receta_con_tab_y_variables_indentadas_no_se_marcan(tmp_path):
    mk = tmp_path / "Makefile"
    mk.write_text("CC = gcc\nifeq ($(X),1)\n  CFLAGS = -O2\nendif\nall:\n\tgcc x.c\n")
    assert not any(i.code == "MKF001" for i in lint_makefile(mk))
