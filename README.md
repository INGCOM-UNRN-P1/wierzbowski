# WIERZBOWSKI — Auditor de Grafos de Inclusión, Ciclos y Makefiles en C

> 📖 **Manual de Usuario:** Para una guía exhaustiva de comandos, banderas, arquitectura y ejemplos, consultá el [Manual de Uso](MANUAL.md).

**WIERZBOWSKI** analiza la arquitectura de proyectos multi-archivo en C, construyendo el grafo de dependencias de `#include`, detectando dependencias circulares, verificando guardas de inclusión y auditando Makefiles.

---

## 🎯 Alcance

### Qué cubre
- Auditoría estática de grafos de inclusión de archivos de cabecera (`#include`) y Makefiles en C.
- Detección de dependencias circulares y ciclos de inclusión entre archivos `.h` y `.c`.
- Verificación de presencia de guardas de inclusión defensivas (`#ifndef / #define` o `#pragma once`) en cabeceras `.h`.
- Auditoría de sintaxis y coherencia de reglas en Makefiles de proyectos estudiantiles.

### Qué no cubre (Límites y Delegación)
- Compilación de código ni generación de binarios (delegado a `daedalus`).
- Auditoría del interior de macros preprocesadas (delegado a `zhora`).
- Auditoría de layout de memoria de structs declarados en cabeceras (delegado a `brett`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Multiplataforma. Python >= 3.10.

### Dependencias Externas y Binarios
- Ninguno obligatorio (análisis estático de código fuente y Makefiles).

### Integración en el Ecosistema
- CLI `wierzbowski`. Plugin registrado en `ripley.plugins` (`headers_audit`).

---

## 🚀 Uso Rápido

```bash
# Auditar dependencias en el directorio actual
wierzbowski audit .
wierzbowski check .

# Auditar proyecto específico
wierzbowski audit ./tp_modular/

# Generar informe en formato Markdown
wierzbowski report .

# Salida estructurada JSON
wierzbowski audit . --json
```

---

## 🔍 Reglas Auditadas

- **Detección de Ciclos**: Grafos de inclusión circulares (`a.h ➔ b.h ➔ a.h`).
- **Guardas de Inclusión**: Falta de `#ifndef / #define` o `#pragma once`.
- **`MKF001`**: Recetas de Makefiles indentadas con espacios en lugar de TAB.
- **`MKF002`**: Reglas sin archivo objetivo sin declaración en `.PHONY`.
- **`MKF003`**: Ausencia de target `clean`.

<!-- p1:referencia:inicio — generado por p1-tools/scripts/readme_generado.py: no editar a mano -->

## Referencia rápida

### Requisitos

- Python ≥ 3.11 y [uv](https://docs.astral.sh/uv/getting-started/installation/).

### Comandos

| Comando | Descripción |
|:--|:--|
| `wierzbowski check`, `wierzbowski audit` | Audita dependencias entre cabeceras, ciclos de inclusión y Makefiles. |
| `wierzbowski report` | Genera directamente la sección de reporte Markdown de WIERZBOWSKI para Dredd. |
| `wierzbowski doctor` | Verifica el estado del entorno de auditoría de dependencias WIERZBOWSKI (Python, Make, GCC). |

Ayuda de cada comando: `wierzbowski <comando> -h`.

### Salida JSON

Con `--json`, estos comandos emiten el resultado como JSON por la salida estándar, para usarlo desde scripts, ripley o dredd: `wierzbowski check`, `wierzbowski audit`, `wierzbowski doctor`. El de `doctor --json` lleva `schema_version` y `ok`.

### Códigos de salida

| Código | Significado |
|:--|:--|
| `0` | Terminó bien (en `doctor`: está todo lo requerido). |
| `1` | El comando encontró problemas (hallazgos, pruebas que fallan, un umbral que no se alcanza) o un dato no se pudo usar (un archivo ilegible, un formato inválido). |
| `2` | Error de uso: comando, opción o argumento inválido. |

<!-- p1:referencia:fin -->
