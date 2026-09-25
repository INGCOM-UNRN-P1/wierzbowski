# Manual de Uso y Referencia Técnica: wierzbowski

> **WIERZBOWSKI** — Auditor de grafos de inclusión de headers, dependencias circulares y Makefiles en C
> **Versión:** `0.1.0` · **CLI principal:** `wierzbowski` · **Plugin Ripley:** `headers_audit`

---

## 1. Arquitectura y Propósito Pedagógico

`wierzbowski` forma parte del ecosistema de herramientas de la cátedra de Programación 1 (UNRN). Su objetivo central es resolver de forma modular, determinista y automatizada las tareas asociadas a su dominio específico dentro del ciclo de desarrollo, evaluación y aprendizaje de software en C.

### Alcance Funcional (Qué cubre)
- Auditoría estática de grafos de inclusión de archivos de cabecera (`#include`) y Makefiles en C.
- Detección de dependencias circulares y ciclos de inclusión entre archivos `.h` y `.c`.
- Verificación de presencia de guardas de inclusión defensivas (`#ifndef / #define` o `#pragma once`) en cabeceras `.h`.
- Auditoría de sintaxis y coherencia de reglas en Makefiles de proyectos estudiantiles.

### Límites de Responsabilidad y Delegación (Qué no cubre)
- Compilación de código ni generación de binarios (delegado a `daedalus`).
- Auditoría del interior de macros preprocesadas (delegado a `zhora`).
- Auditoría de layout de memoria de structs declarados en cabeceras (delegado a `brett`).

### Principios de Diseño
- **Enfoque Pedagógico:** Diagnósticos y mensajes en español rioplatense orientados a facilitar la comprensión de errores conceptuales.
- **Salida Estructurada Dual:** Soporte nativo para visualización enriquecida en terminal (Rich) y salida parseable para orquestadores (`--json`).
- **Integración Contractual:** Capacidad de emitir secciones de reporte para `dredd` (`dredd-section`) y actuar como satélite orquestado por `ripley`.
- **Idempotencia y Robustez:** Validación de precondiciones y comandos de autodiagnóstico (`doctor`) para verificación del entorno.

---

## 2. Instalación y Requisitos

### Requisitos del Sistema
- **Python:** `>= 3.10` (recomendado Python 3.11 o 3.12).
- **Gestor de paquetes:** [`uv`](https://github.com/astral-sh/uv) (entorno estándar de cátedra).
- **Toolchain C (si aplica):** GCC / Clang, Make, GDB y bibliotecas estándar de desarrollo.

### Instalación en el Entorno de Usuario
Para instalar la herramienta de forma global y aislada en el sistema mediante `uv tool`:
```bash
uv tool install --editable /home/mrtin/dev/tools/wierzbowski
```

### Verificación de Instalación
Ejecutá el comando `doctor` para constatar que todas las dependencias y binarios requeridos estén presentes y operativos:
```bash
wierzbowski doctor
```

---

## 3. Guía Integral de Comandos (CLI)

| Comando | Descripción Breve |
| :--- | :--- |
| [`wierzbowski check`](#check) | Audita dependencias entre cabeceras, ciclos de inclusión y Makefiles. |
| [`wierzbowski audit`](#audit) | Audita dependencias entre cabeceras, ciclos de inclusión y Makefiles. |
| [`wierzbowski report`](#report) | Genera directamente la sección de reporte Markdown de WIERZBOWSKI para Dredd. |
| [`wierzbowski doctor`](#doctor) | Verifica el estado del entorno de auditoría de dependencias WIERZBOWSKI (Python, Make, GCC). |
| [`wierzbowski version`](#version) | Muestra la versión de WIERZBOWSKI. |

### `wierzbowski check`

Audita dependencias entre cabeceras, ciclos de inclusión y Makefiles.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--directory` | `<class 'pathlib._local.Path'>` | `.` | Directorio raíz del proyecto C a analizar |
| `--json` | `<class 'bool'>` | `False` | Emitir salida en formato JSON estructurado |
| `--md`, `--output-md` | `Optional[pathlib._local.Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |

#### Ejemplo de Invocación
```bash
wierzbowski check
```

### `wierzbowski audit`

Audita dependencias entre cabeceras, ciclos de inclusión y Makefiles.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--directory` | `<class 'pathlib._local.Path'>` | `.` | Directorio raíz del proyecto C a analizar |
| `--json` | `<class 'bool'>` | `False` | Emitir salida en formato JSON estructurado |
| `--md`, `--output-md` | `Optional[pathlib._local.Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |

#### Ejemplo de Invocación
```bash
wierzbowski audit
```

### `wierzbowski report`

Genera directamente la sección de reporte Markdown de WIERZBOWSKI para Dredd.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--directory` | `<class 'pathlib._local.Path'>` | `.` | Directorio raíz del proyecto C a analizar |
| `--output`, `-o` | `Optional[pathlib._local.Path]` | `None` | Ruta de destino del archivo Markdown. |

#### Ejemplo de Invocación
```bash
wierzbowski report
```

### `wierzbowski doctor`

Verifica el estado del entorno de auditoría de dependencias WIERZBOWSKI (Python, Make, GCC).

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `<class 'bool'>` | `False` | Emitir diagnóstico en formato JSON estructurado. |

#### Ejemplo de Invocación
```bash
wierzbowski doctor
```

### `wierzbowski version`

Muestra la versión de WIERZBOWSKI.

#### Ejemplo de Invocación
```bash
wierzbowski version
```

---

## 4. Formatos de Salida e Integración con el Ecosistema

### Modo Interactivo / Terminal (Rich)
Por defecto, la herramienta renderiza paneles, árboles y tablas estilizadas para facilitar la lectura del estudiante y docente en terminales modernas con soporte ANSI.

### Modo Estructurado JSON (`--json`)
Para integración con pipelines de CI/CD, scripts de automatización u orquestadores externos, la opción `--json` emite un documento JSON estricto por la salida estándar (`stdout`), dirigiendo cualquier mensaje de logging a `stderr`:
```bash
wierzbowski check --json
```

### Integración con Dredd (`dredd-section`)
Cuando la herramienta genera reportes de evaluación para entregas de alumnos, produce una sección Markdown estandarizada conforme al contrato de integración de Dredd (v1.0.0):
```markdown
<!-- dredd-section: wierzbowski, tool=wierzbowski, version=0.1.0, status=ok -->
```
Este encabezado garantiza la agregación determinista de los hallazgos en la rúbrica docente.

### Integración con Ripley
`wierzbowski` está registrada en el catálogo de plugins satélites de Ripley (`SATELLITE_CATALOG`). Puede invocarse directamente a través del motor de evaluación de Ripley configurando el análisis en `ripley.toml`.

---

## 5. Diagnóstico y Códigos de Salida

### Códigos de Retorno (`exit code`)
| Código | Significado |
| :---: | :--- |
| `0` | Ejecución exitosa sin hallazgos críticos ni errores de sintaxis. |
| `1` | Hallazgos pedagógicos detectados, infracción de reglas o advertencias activas. |
| `2` | Error de sintaxis en argumentos CLI o archivo fuente no encontrado. |
| `>2` | Error no recuperable del sistema, fallo de memoria o excepción interna. |

### Diagnóstico del Entorno (`doctor`)
Ante comportamientos inesperados, verificá el estado operativo con:
```bash
wierzbowski doctor
```
Comprueba la presencia de las dependencias requeridas y la integridad de los componentes del paquete.