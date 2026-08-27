"""Construcción del grafo de dependencias de inclusión y detección de ciclos."""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from wierzbowski.core.models import HeaderNode, CircularDependency

INCLUDE_PATTERN = re.compile(r'^\s*#\s*include\s+["<]([^">]+)[">]', re.MULTILINE)


def extract_includes(file_content: str) -> List[str]:
    """Extrae todos los archivos incluidos en un fuente C o H."""
    return INCLUDE_PATTERN.findall(file_content)


def build_dependency_graph(directory: Path) -> Dict[str, HeaderNode]:
    """Construye el grafo de inclusión de cabeceras y fuentes del proyecto."""
    nodes: Dict[str, HeaderNode] = {}
    files = list(directory.glob("**/*.h")) + list(directory.glob("**/*.c"))

    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        includes = extract_includes(content)
        # Solo incluir cabeceras locales / del proyecto
        local_includes = [inc for inc in includes if not inc.endswith((".h", ".hpp")) or not inc.startswith("<")]
        # O si termina en .h y no es estándar de libc
        normalized_includes = []
        for inc in includes:
            if "/" not in inc and not inc.endswith((".h", ".hpp")):
                continue
            normalized_includes.append(Path(inc).name)

        nodes[f.name] = HeaderNode(
            file_path=str(f),
            file_name=f.name,
            includes=normalized_includes
        )

    return nodes


def detect_cycles(nodes: Dict[str, HeaderNode]) -> List[CircularDependency]:
    """Detecta ciclos en el grafo de dependencias utilizando DFS."""
    cycles: List[CircularDependency] = []
    visited: Set[str] = set()
    rec_stack: List[str] = []

    def dfs(node_name: str):
        visited.add(node_name)
        rec_stack.append(node_name)

        node = nodes.get(node_name)
        if node:
            for neighbor in node.includes:
                if neighbor in rec_stack:
                    # Ciclo encontrado
                    cycle_start = rec_stack.index(neighbor)
                    cycle_path = rec_stack[cycle_start:] + [neighbor]
                    desc = " ➔ ".join(cycle_path)
                    cycles.append(CircularDependency(cycle=cycle_path, description=desc))
                elif neighbor not in visited and neighbor in nodes:
                    dfs(neighbor)

        rec_stack.pop()

    for n in list(nodes.keys()):
        if n not in visited:
            dfs(n)

    return cycles
