---
title: "Manual de Referencia: wierzbowski"
subtitle: "Wierzbowski — Auditor de Grafos de Inclusión de Headers, Dependencias Circulares y Makefiles"
author: "Cátedra de Algoritmos y Programación"
date: "2026-08-31"
---

(manual-wierzbowski)=
# Wierzbowski — Auditor de Grafos de Inclusión de Headers, Dependencias Circulares y Makefiles

````{abstract}
**Rol en el ecosistema:** Auditoría estática de dependencias entre archivos `.h` y `.c`, detección de inclusiones circulares, includes redundantes o no utilizados y validación de reglas en Makefiles.
````

---

(manual-wierzbowski-proposito)=
## 1. Propósito y Filosofía Pedagógica

La herramienta **`wierzbowski`** forma parte del ecosistema oficial de software de la cátedra. Su diseño sigue principios pedagógicos rigurosos:

1. **Evidencia Técnica Directa**: Todo diagnóstico se fundamenta en la norma ISO C (C11/C23), en el modelo de memoria del sistema o en convenciones arquitectónicas formales.
2. **Acción Correctiva Concreta**: Cada advertencia incluye la prescripción técnica inmediata para resolver el defecto sin recurrir a conjeturas.
3. **Autonomía del Estudiante**: Facilita la autoevaluación local antes de la entrega final del trabajo práctico.
4. **Objetividad Docente**: Estandariza la corrección automática eliminando discrepancias subjetivas en la evaluación.

---

(manual-wierzbowski-instalacion)=
## 2. Instalación y Diagnóstico del Entorno

````{important}
Asegurate de contar con el compilador GCC/Clang y las librerías del sistema instaladas antes de ejecutar `wierzbowski`.
````

Para comprobar el estado de salud de tu entorno de trabajo y las dependencias auxiliares:

````{code-block} bash
# Comprobación de dependencias del sistema
wierzbowski doctor
````

Si se detecta la falta de alguna utilidad (como `gdb`, `valgrind`, `clang-format` o `typst`), el comando indicará el paquete exacto a instalar según tu distribución GNU/Linux o entorno MSYS2.

---

(manual-wierzbowski-comandos)=
## 3. Referencia Completa de Comandos CLI

A continuación se detallan los subcomandos principales disponibles en `wierzbowski`:

| Sintaxis del Comando | Descripción y Efecto |
| :--- | :--- |
| `wierzbowski audit include/ src/` | Audita el grafo de dependencias de cabeceras buscando ciclos y redundancias. |
| `wierzbowski graph include/ -o dependencias.dot` | Exporta el grafo de inclusiones en formato DOT / Graphviz. |
| `wierzbowski check-makefile Makefile` | Valida que todas las dependencias declaradas en el Makefile sean consistentes. |
| `wierzbowski unused-includes src/` | Detecta `#include` que no son necesarios en el archivo. |

````{tip}
Podés agregar el flag `--json` a la mayoría de los comandos para exportar resultados en formato estructurado o `--md` para generar reportes Markdown para el informe de entrega.
````

---

(manual-wierzbowski-tutorial)=
## 4. Tutorial Paso a Paso con Ejemplos Reales

### Caso de Estudio

Considerá el siguiente fragmento de código representativo:

````{code-block} c
:linenos:
// Inclusión circular problemática:
// include/a.h incluye "b.h"
// include/b.h incluye "a.h"
// Wierzbowski detecta el ciclo y propone forward declarations.
````

### Ejecución de la Herramienta

Ejecutá el análisis desde tu terminal:

````{code-block} bash
wierzbowski audit include/ src/
````

### Salida Obtenida en Consola

````{code-block} text
[!] WIERZBOWSKI DEPENDENCY ALERT:
    • Ciclo de inclusión circular detectado: include/a.h <───> include/b.h
    • Inclusión redundante: 'src/main.c:2' incluye <stdlib.h> pero no utiliza ninguna función de esa cabecera.
    • Makefile: La regla 'bin/programa' no declara 'include/tda.h' como prerrequisito.
````

````{note}
Prestá atención a la explicación pedagógica generada: la herramienta no solo señala la línea del problema, sino que explica la causa raíz y el impacto en memoria o arquitectura.
````

---

(manual-wierzbowski-ejercicios)=
## 5. Ejercicios Prácticos y Desafíos

Practicá el uso avanzado de **`wierzbowski`** resolviendo los siguientes ejercicios:

````{exercise} Desafío 1: Detección de Inclusiones Circulares
Escanear todos los headers de un proyecto grande para resolver ciclos.

**Instrucción de ejecución:**
```bash
wierzbowski audit include/
```
````

````{solution} Desafío 1
```bash
wierzbowski audit include/
# Verificá que la operación concluya exitosamente con código de salida 0.
```
````

````{exercise} Desafío 2: Limpieza de Headers Inutilizados
Eliminar includes innecesarios para acelerar el tiempo de compilación.

**Instrucción de ejecución:**
```bash
wierzbowski unused-includes src/
```
````

````{solution} Desafío 2
```bash
wierzbowski unused-includes src/
# Revisá el archivo generado o el informe en terminal para confirmar la resolución del problema.
```
````

````{exercise} Desafío 3: Validación de Dependencias en Makefile
Comprobar que modificar un `.h` fuerza la recompilación de los `.c` correspondientes.

**Instrucción de ejecución:**
```bash
wierzbowski check-makefile Makefile
```
````

````{solution} Desafío 3
```bash
wierzbowski check-makefile Makefile
# Comprobá que la salida confirme la ausencia de advertencias o errores pendientes.
```
````

---

(manual-wierzbowski-makefile)=
## 6. Integración en el Flujo de Trabajo y Makefile

Para incorporar `wierzbowski` de forma automática a tu flujo de desarrollo, agregá la siguiente regla en el `Makefile` de tu proyecto:

````{code-block} makefile
check-wierzbowski:
	@echo "=== Ejecutando verificación con wierzbowski ==="
	wierzbowski check src/ include/

.PHONY: check-wierzbowski
````

Ejecutá `make check-wierzbowski` antes de cada commit para asegurar que tu código conserve el estado de aprobación.

---

(manual-wierzbowski-arquitectura)=
## 7. Arquitectura Interna y Mecanismo Técnico

La herramienta **`wierzbowski`** implementa un motor de alta precisión basado en:

- **Tecnología Núcleo:** `C Preprocessor Inclusions Graph Builder + NetworkX Cycle Detector + Makefile Dependency Parser`.
- **Aislamiento y Determinismo:** Diseñada para operar sin efectos colaterales en entornos de integración continua (CI), terminales de estudiantes y servidores docentes headless.
- **Manejo de Errores Pedagógico:** Todo fallo de sintaxis, memoria o lógica se traduce en una acción prescriptiva concreta con su respectiva justificación técnica.

---

(manual-wierzbowski-ecosistema)=
## 8. Integración y Conexión con el Ecosistema

````{note}
Ninguna herramienta opera de forma aislada. **`wierzbowski`** forma parte del pipeline integral de evaluación, verificación y enseñanza de la cátedra.
````

### Diagrama de Flujo e Interoperabilidad

````{mermaid}
graph TD
    HDR[Archivos include/*.h y src/*.c] --> WRZ[Wierzbowski: Grafo de Includes]
    MKF[Makefile del Proyecto] --> WRZ
    WRZ -->|Detección de Ciclos de Inclusión| NETX[NetworkX Cycle Detector]
    WRZ -->|Consistencia de Reglas| DAE[Daedalus: Compilador Defensivo]
    WRZ -->|Limpieza de Includes| RIP[Ripley: Linter de Cátedra]
````

### Matriz de Intercambio de Datos

| Canal | Herramientas Conectadas | Tipo de Datos Transferidos |
| :--- | :--- | :--- |
| **Entradas (Inputs)** | - `Código fuente C (.c/.h) y archivos Makefile` | Código fuente, AST, binarios, testcases, contratos |
| **Salidas (Outputs)** | - `daedalus (orden de compilación)`
- `ripley (reglas de headers)` | Informes Markdown, diagnósticos Rich, JSON, actas |
| **Sincronización** | `daedalus`, `corbel`, `ripley` | Validación cruzada, flags compartidos y autofix |

### Pipeline de Integración Recomendado

Podés encadenar `wierzbowski` con otras herramientas del ecosistema en una única línea de comando:

````{code-block} bash
# Pipeline de integración típico
wierzbowski audit include/ src/ && wierzbowski check-makefile Makefile
````

