"""Reglas de la cátedra sobre Makefiles: flags obligatorios, .PHONY completo y trampas.

Las trampas venían de `dredd audit-makefile` (wierzbowski es el dueño de los Makefiles, revisión
04 §5, N-ECO-12): silenciar advertencias, enmascarar errores, descargar de la red, copiar binarios
precompilados, enlazar bibliotecas no autorizadas o redefinir CC con un script.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

from wierzbowski.core.models import MakefileIssue

FLAGS_OBLIGATORIOS = ("-Wall", "-Wextra", "-std=c11")
LIBRERIAS_PERMITIDAS: Set[str] = {"m", "pthread", "rt", "p1_test", "check"}

_ASIGNACION_CFLAGS = re.compile(r"^\s*CFLAGS\s*(?:\+|:|\?)?=\s*(?P<valor>.*)$")
_PHONY = re.compile(r"^\s*\.PHONY\s*:\s*(?P<objetivos>.*)$")
_OBJETIVO = re.compile(r"^(?P<nombre>[A-Za-z0-9_.-]+)\s*:(?!=)")
_FALSOS = ("all", "clean", "test", "run", "install")


def _sin_comentario(linea: str) -> str:
    return linea.split("#", 1)[0]


def _trampas(num: int, s: str, permitidas: Set[str]) -> List[MakefileIssue]:
    issues: List[MakefileIssue] = []
    if re.search(r"(?:^|\s)-w(?:\s|$)", s) or "-Wno-all" in s:
        issues.append(MakefileIssue(code="MKF010", severity="ERROR", line_number=num,
                                    message="Se silencian las advertencias del compilador con '-w' o '-Wno-all'.",
                                    suggestion="Quitá esa bandera: las advertencias son parte de la corrección."))
    if re.search(r"\|\|\s*(true|exit\s*0|:)\s*$", s):
        issues.append(MakefileIssue(code="MKF011", severity="ERROR", line_number=num,
                                    message="Se enmascara el código de salida con '|| true' o '|| exit 0'.",
                                    suggestion="Dejá que el comando falle: si no, make informa éxito aunque haya errores."))
    if re.search(r"\b(curl|wget|git\s+clone|nc|ssh)\b", s):
        issues.append(MakefileIssue(code="MKF012", severity="ERROR", line_number=num,
                                    message="El Makefile descarga o se conecta a la red.",
                                    suggestion="La compilación tiene que usar solo los archivos de la entrega."))
    if re.search(r"\bcp\s+\S*\.(o|a|so|dll)\b", s) or re.search(r"\bcp\s+\S*\bbin\b", s):
        issues.append(MakefileIssue(code="MKF013", severity="ERROR", line_number=num,
                                    message="Se copian binarios u objetos precompilados en lugar de compilarlos.",
                                    suggestion="Generá los .o y ejecutables desde los fuentes, con reglas de make."))
    for lib in re.findall(r"(?:^|\s)-l([A-Za-z0-9_\-]+)", s):
        if lib.lower() not in permitidas:
            issues.append(MakefileIssue(code="MKF014", severity="ERROR", line_number=num,
                                        message=f"Se enlaza una biblioteca no autorizada: '-l{lib}'.",
                                        suggestion=f"Bibliotecas permitidas: {', '.join(sorted(permitidas))}."))
    if re.match(r"^\s*CC\s*[:?]?=\s*(\./|\.\./|bash|sh|python)", s):
        issues.append(MakefileIssue(code="MKF015", severity="ERROR", line_number=num,
                                    message="CC apunta a un script o a una ruta local en lugar del compilador.",
                                    suggestion="Usá CC = gcc (o clang)."))
    return issues


def reglas_catedra(contenido: str, flags_obligatorios: Iterable[str] = FLAGS_OBLIGATORIOS,
                   librerias_permitidas: Optional[Set[str]] = None) -> List[MakefileIssue]:
    """Flags obligatorios en CFLAGS (QoL #1071), .PHONY completo (#1072) y trampas."""
    issues: List[MakefileIssue] = []
    permitidas = librerias_permitidas or LIBRERIAS_PERMITIDAS
    cflags: List[str] = []
    linea_cflags = 1
    phony: Set[str] = set()
    objetivos: Dict[str, int] = {}
    for num, linea in enumerate(contenido.splitlines(), 1):
        texto = _sin_comentario(linea)
        m = _ASIGNACION_CFLAGS.match(texto)
        if m:
            cflags += m.group("valor").split()
            linea_cflags = num
        m = _PHONY.match(texto)
        if m:
            phony |= set(m.group("objetivos").split())
        elif not linea.startswith(("\t", " ")):
            m = _OBJETIVO.match(texto)
            if m:
                objetivos.setdefault(m.group("nombre"), num)
        s = texto.strip()
        if s:
            issues.extend(_trampas(num, s, permitidas))

    faltan = [f for f in flags_obligatorios if f not in cflags]
    if faltan:
        issues.append(MakefileIssue(
            code="MKF004", severity="WARNING", line_number=linea_cflags,
            message=("No se define CFLAGS" if not cflags else "Faltan banderas obligatorias de la cátedra en CFLAGS")
            + f": {' '.join(faltan)}.",
            suggestion=f"CFLAGS = {' '.join(FLAGS_OBLIGATORIOS)} -g (y usá $(CFLAGS) en las reglas de compilación)."))
    if phony:
        sin_declarar = [o for o in _FALSOS if o in objetivos and o not in phony]
        if sin_declarar:
            issues.append(MakefileIssue(
                code="MKF005", severity="WARNING", line_number=objetivos[sin_declarar[0]],
                message=f"Objetivos sin archivo que no están en .PHONY: {', '.join(sin_declarar)}.",
                suggestion=f"Agregalos: .PHONY: {' '.join(sorted(phony | set(sin_declarar)))}."))
    return issues


def resolver_makefile(ruta: Path) -> Path:
    if ruta.is_dir():
        for nombre in ("Makefile", "makefile", "GNUmakefile"):
            if (ruta / nombre).is_file():
                return ruta / nombre
        return ruta / "Makefile"
    return ruta


def auditar_makefile(ruta: Path, librerias_permitidas: Optional[Set[str]] = None) -> List[MakefileIssue]:
    """Las reglas de la cátedra sobre un Makefile (o el Makefile de un directorio)."""
    ruta = resolver_makefile(ruta)
    if not ruta.is_file():
        return []
    return reglas_catedra(ruta.read_text(encoding="utf-8", errors="replace"), librerias_permitidas=librerias_permitidas)
