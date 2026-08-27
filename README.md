# WIERZBOWSKI — Auditor de Grafos de Inclusión, Ciclos y Makefiles en C

**WIERZBOWSKI** analiza la arquitectura de proyectos multi-archivo en C, construyendo el grafo de dependencias de `#include`, detectando dependencias circulares, verificando guardas de inclusión y auditando Makefiles.

---

## 🚀 Uso Rápido

```bash
# Auditar dependencias en el directorio actual
wierzbowski audit .

# Auditar proyecto específico
wierzbowski audit ./tp_modular/

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
