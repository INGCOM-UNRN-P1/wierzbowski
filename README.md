# WIERZBOWSKI — Auditor de Grafos de Inclusión, Ciclos y Makefiles en C

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
