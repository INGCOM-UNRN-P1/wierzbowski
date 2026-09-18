"""Enmascarado de comentarios y bloques `#if 0` antes de extraer `#include`.

Un `#include` escrito dentro de un comentario de bloque o de un `#if 0` no
existe para el compilador, pero un regex anclado a inicio de línea lo ve igual
y lo mete al grafo de dependencias, con lo que aparecen ciclos y dependencias
que no son reales.

A diferencia de otros enmascarados del ecosistema, acá los literales de cadena
NO se blanquean: `#include "b.h"` los usa como parte de la sintaxis. Se
recorren solo para que un `//` o `/*` dentro de un string no se confunda con
el inicio de un comentario.
"""

from __future__ import annotations

import re
from typing import Optional

_INICIO_IF_FALSO = re.compile(r"^\s*#\s*if\s+0\s*(?://.*|/\*.*)?$")
_INICIO_CONDICIONAL = re.compile(r"^\s*#\s*(if|ifdef|ifndef)\b")
_FIN_CONDICIONAL = re.compile(r"^\s*#\s*endif\b")
_RAMA_ALTERNATIVA = re.compile(r"^\s*#\s*(else|elif)\b")


def _blanquear(texto: str) -> str:
    """Sustituye cada carácter por un espacio, conservando los saltos de línea."""
    return "".join("\n" if c == "\n" else " " for c in texto)


def enmascarar_comentarios(contenido: str) -> str:
    """Blanquea comentarios de línea y de bloque, dejando intactos los literales."""
    resultado = []
    i, n = 0, len(contenido)

    while i < n:
        c = contenido[i]
        par = contenido[i:i + 2]

        if par == "//":
            fin = contenido.find("\n", i)
            fin = n if fin == -1 else fin
            resultado.append(_blanquear(contenido[i:fin]))
            i = fin
        elif par == "/*":
            fin = contenido.find("*/", i + 2)
            fin = n if fin == -1 else fin + 2
            resultado.append(_blanquear(contenido[i:fin]))
            i = fin
        elif c in ('"', "'"):
            j = i + 1
            while j < n:
                if contenido[j] == "\\":
                    j += 2
                    continue
                if contenido[j] == c:
                    j += 1
                    break
                if contenido[j] == "\n":
                    break
                j += 1
            resultado.append(contenido[i:j])
            i = j
        else:
            resultado.append(c)
            i += 1

    return "".join(resultado)


def enmascarar_bloques_inactivos(contenido: str) -> str:
    """Blanquea el cuerpo de los bloques `#if 0`, incluidos los anidados."""
    salida = []
    profundidad: Optional[int] = None

    for linea in contenido.splitlines(keepends=True):
        if profundidad is None:
            salida.append(linea)
            if _INICIO_IF_FALSO.match(linea.rstrip("\n")):
                profundidad = 1
            continue

        if _INICIO_CONDICIONAL.match(linea):
            profundidad += 1
            salida.append(_blanquear(linea))
        elif _FIN_CONDICIONAL.match(linea):
            profundidad -= 1
            if profundidad == 0:
                profundidad = None
                salida.append(linea)
            else:
                salida.append(_blanquear(linea))
        elif profundidad == 1 and _RAMA_ALTERNATIVA.match(linea):
            profundidad = None
            salida.append(linea)
        else:
            salida.append(_blanquear(linea))

    return "".join(salida)


def enmascarar_para_includes(contenido: str) -> str:
    """Comentarios primero (un `#if 0` dentro de un comentario no cuenta)."""
    return enmascarar_bloques_inactivos(enmascarar_comentarios(contenido))
