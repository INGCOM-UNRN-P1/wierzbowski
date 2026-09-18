"""Plugin de WIERZBOWSKI para el microkernel RIPLEY."""

from pathlib import Path
from typing import Dict, Any
from wierzbowski.core.header_graph import build_dependency_graph, detect_cycles
from wierzbowski.core.guard_checker import auditar_guardas, lint_makefile


class WierzbowskiPlugin:
    """Plugin de auditoría de dependencias y Makefiles para Ripley."""

    name = "headers_audit"
    description = "Auditor de grafos de inclusión, dependencias circulares y Makefiles"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        source_dir = Path(context.get("source_dir", "."))
        nodes = build_dependency_graph(source_dir)
        cycles = detect_cycles(nodes)

        guard_errors, guard_notes = auditar_guardas(sorted(source_dir.glob("**/*.h")))

        makefile = source_dir / "Makefile"
        mk_issues = lint_makefile(makefile) if makefile.exists() else []

        passed = (len(cycles) == 0) and (len(guard_errors) == 0) and not any(i.severity == "ERROR" for i in mk_issues)

        return {
            "passed": passed,
            "circular_dependencies_count": len(cycles),
            "cycles": [c.description for c in cycles],
            "guard_errors": guard_errors,
            "guard_notes": guard_notes,
            "makefile_issues_count": len(mk_issues)
        }
