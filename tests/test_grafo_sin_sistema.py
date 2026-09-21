"""WIERZ-D0302: las cabeceras del sistema no son nodos/aristas del grafo del proyecto."""

from wierzbowski.core.header_graph import build_dependency_graph, extract_includes


def test_extract_includes_puede_omitir_sistema():
    fuente = '#include <stdio.h>\n#include "propio.h"\n'
    assert extract_includes(fuente) == ["stdio.h", "propio.h"]
    assert extract_includes(fuente, incluir_sistema=False) == ["propio.h"]


def test_grafo_no_agrega_aristas_a_cabeceras_del_sistema(tmp_path):
    (tmp_path / "a.h").write_text('#include <stdio.h>\n#include <stdlib.h>\n#include "b.h"\n')
    (tmp_path / "b.h").write_text("")
    grafo = build_dependency_graph(tmp_path)
    assert grafo["a.h"].includes == ["b.h"]
