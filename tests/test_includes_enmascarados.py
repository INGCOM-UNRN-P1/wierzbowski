"""Regresión de WIERZ-D0301: los `#include` inactivos no forman parte del grafo."""

from pathlib import Path

from wierzbowski.core.header_graph import build_dependency_graph, extract_includes


def test_un_include_dentro_de_un_comentario_de_bloque_no_cuenta():
    fuente = '/* viejo:\n#include "b.h"\n*/\n#include "c.h"\n'
    assert extract_includes(fuente) == ["c.h"]


def test_un_include_en_un_comentario_de_linea_no_cuenta():
    assert extract_includes('// #include "b.h"\n#include "c.h"\n') == ["c.h"]


def test_un_include_bajo_if_0_no_cuenta():
    fuente = '#if 0\n#include "b.h"\n#endif\n#include "c.h"\n'
    assert extract_includes(fuente) == ["c.h"]


def test_los_includes_reales_de_ambos_estilos_se_conservan():
    assert extract_includes('#include <stdio.h>\n#include "propio.h"\n') == ["stdio.h", "propio.h"]


def test_una_url_en_un_string_no_se_confunde_con_un_comentario():
    """`//` dentro de un literal no inicia un comentario ni oculta el include."""
    fuente = 'const char *u = "http://x";\n#include "b.h"\n'
    assert extract_includes(fuente) == ["b.h"]


def test_el_ciclo_falso_por_comentario_no_aparece_en_el_grafo(tmp_path):
    """a.h incluye b.h de verdad; b.h solo MENCIONA a a.h en un comentario."""
    (tmp_path / "a.h").write_text('#ifndef A_H\n#define A_H\n#include "b.h"\n#endif\n', encoding="utf-8")
    (tmp_path / "b.h").write_text(
        '#ifndef B_H\n#define B_H\n/* antes:\n#include "a.h"\n*/\n#endif\n', encoding="utf-8"
    )
    grafo = build_dependency_graph(tmp_path)
    assert "a.h" not in grafo["b.h"].includes
