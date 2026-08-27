"""Auditoría de guardas de inclusión (#ifndef FOO_H / #pragma once) y Makefiles."""

import re
from pathlib import Path
from typing import List, Tuple
from wierzbowski.core.models import MakefileIssue

GUARD_PATTERN = re.compile(r'^\s*#\s*ifndef\s+([a-zA-Z0-9_]+)\s*\n\s*#\s*define\s+\1', re.MULTILINE)
PRAGMA_ONCE_PATTERN = re.compile(r'^\s*#\s*pragma\s+once', re.MULTILINE)


def check_header_guard(header_path: Path) -> Tuple[bool, str]:
    """Verifica si un archivo .h posee guardas estándar o #pragma once."""
    content = header_path.read_text(encoding="utf-8", errors="replace")
    if PRAGMA_ONCE_PATTERN.search(content):
        return True, "#pragma once"

    match = GUARD_PATTERN.search(content)
    if match:
        macro_name = match.group(1)
        expected_macro = header_path.name.upper().replace(".", "_").replace("-", "_")
        if macro_name != expected_macro and not macro_name.endswith("_H"):
            return True, f"Guard no estándar: {macro_name}"
        return True, macro_name

    return False, "Falta guarda de inclusión"


def lint_makefile(makefile_path: Path) -> List[MakefileIssue]:
    """Analiza un Makefile en busca de errores clásicos y buenas prácticas."""
    issues = []
    if not makefile_path.exists():
        return issues

    content = makefile_path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    has_phony = False
    has_clean = False
    has_all = False

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith(".PHONY:"):
            has_phony = True
        if stripped.startswith("clean:"):
            has_clean = True
        if stripped.startswith("all:"):
            has_all = True

        # Verificar si una receta usa espacios en lugar de un Tab inicial
        if line.startswith("    ") and not line.startswith("\t") and not stripped.startswith("#"):
            if idx > 1 and lines[idx - 2].rstrip().endswith("\\"):
                continue
            issues.append(MakefileIssue(
                code="MKF001",
                severity="ERROR",
                line_number=idx,
                message="Receta de regla indentada con 4 espacios en lugar de un caracter TAB.",
                suggestion="Make requiere obligatoriamente caracteres TAB (ASCII 0x09) para las líneas de comandos."
            ))

    if not has_phony:
        issues.append(MakefileIssue(
            code="MKF002",
            severity="WARNING",
            line_number=1,
            message="El Makefile no declara target especial .PHONY para reglas sin archivo objetivo (all, clean).",
            suggestion="Agregá '.PHONY: all clean' al inicio para evitar colisiones si existen archivos llamados 'clean' o 'all'."
        ))

    if not has_clean:
        issues.append(MakefileIssue(
            code="MKF003",
            severity="INFO",
            line_number=1,
            message="No se encontró target 'clean' en el Makefile.",
            suggestion="Definí 'clean:' con 'rm -rf build/ *.o' para facilitar la limpieza de artefactos compilados."
        ))

    return issues
