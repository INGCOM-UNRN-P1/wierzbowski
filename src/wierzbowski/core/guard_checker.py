"""Auditoría de guardas de inclusión (#ifndef FOO_H / #pragma once) y Makefiles."""

import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from wierzbowski.core.models import MakefileIssue

GUARD_PATTERN = re.compile(r'^\s*#\s*ifndef\s+([a-zA-Z0-9_]+)\s*\n\s*#\s*define\s+\1', re.MULTILINE)
PRAGMA_ONCE_PATTERN = re.compile(r'^\s*#\s*pragma\s+once', re.MULTILINE)


def _macro_esperada(header_path: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "_", header_path.name).upper()


def inspeccionar_guarda(header_path: Path) -> Tuple[bool, Optional[str], Optional[str]]:
    """Devuelve (tiene_guarda, macro, aviso).

    `aviso` señala una guarda que no corresponde al nombre del archivo. Se
    aceptan los prefijos/sufijos habituales (`PROYECTO_LISTA_H`, `LISTA_H_`,
    `__LISTA_H__`): lo que no puede pasar es que el nombre de la guarda sea el de
    OTRO archivo (`VECTOR_H` en `lista.h`), típico de un encabezado copiado.
    """
    content = header_path.read_text(encoding="utf-8", errors="replace")
    if PRAGMA_ONCE_PATTERN.search(content):
        return True, None, None

    match = GUARD_PATTERN.search(content)
    if match:
        macro_name = match.group(1)
        esperada = _macro_esperada(header_path)
        if not macro_name.strip("_").endswith(esperada.strip("_")):
            return True, macro_name, (
                f"la guarda '{macro_name}' no corresponde al archivo (se esperaría '{esperada}'): "
                "¿se copió de otro encabezado?"
            )
        return True, macro_name, None

    return False, None, None


def check_header_guard(header_path: Path) -> Tuple[bool, str]:
    """Verifica si un archivo .h posee guardas estándar o #pragma once."""
    tiene, macro, aviso = inspeccionar_guarda(header_path)
    if not tiene:
        return False, "Falta guarda de inclusión"
    if aviso:
        return True, f"Guard no estándar: {macro}"
    return True, macro or "#pragma once"


def auditar_guardas(headers: Iterable[Path]) -> Tuple[List[str], List[str]]:
    """Devuelve (problemas, avisos) de las guardas de un conjunto de cabeceras.

    Son problemas la guarda ausente y la que comparten dos cabeceras: al incluir
    ambas, el preprocesador descarta la segunda sin ningún mensaje. Es un aviso
    la que no corresponde al nombre del archivo, que antes se descartaba.
    """
    problemas: List[str] = []
    avisos: List[str] = []
    por_macro: Dict[str, List[Path]] = {}
    for header in headers:
        tiene, macro, aviso = inspeccionar_guarda(header)
        if not tiene:
            problemas.append(f"{header.name}: Falta guarda de inclusión")
            continue
        if macro:
            por_macro.setdefault(macro, []).append(header)
        if aviso:
            avisos.append(f"{header.name}: {aviso}")
    for macro, usadas_por in por_macro.items():
        if len(usadas_por) > 1:
            for header in usadas_por:
                otras = ", ".join(o.name for o in usadas_por if o is not header)
                problemas.append(
                    f"{header.name}: la guarda '{macro}' también la usa {otras}; "
                    "si se incluyen juntos, el segundo queda vacío sin aviso."
                )
    return problemas, avisos


_REGLA = re.compile(r"^[^\s#=:][^=:]*:(?!=)")


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

    en_regla = False
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if line[:1] not in (" ", "\t", "\n", "\r", "#", ""):
            en_regla = bool(_REGLA.match(line))
        if stripped.startswith(".PHONY:"):
            has_phony = True
        if stripped.startswith("clean:"):
            has_clean = True
        if stripped.startswith("all:"):
            has_all = True

        # Verificar si una receta usa espacios en lugar de un Tab inicial
        if en_regla and line.startswith(" ") and stripped and not stripped.startswith("#"):
            if idx > 1 and lines[idx - 2].rstrip().endswith("\\"):
                continue
            issues.append(MakefileIssue(
                code="MKF001",
                severity="ERROR",
                line_number=idx,
                message="Receta de regla indentada con espacios en lugar de un caracter TAB.",
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
