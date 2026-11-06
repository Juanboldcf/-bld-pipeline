---
name: generar-roadmap-tarjeta-debito
description: "Genera un documento de roadmap estructurado y listo para stakeholders para un producto de emisión de tarjetas de débito, y adicionalmente crea un archivo CSV preparado para ser importado directamente como tareas en ClickUp."
category: product
catalog_summary: "Generación de roadmap de tarjeta de débito, planificación estratégica, exportación a ClickUp"
display_order: 1
---

# Generar Roadmap de Tarjeta de Débito

Toma un backlog de iniciativas, objetivos y restricciones de emisión de tarjetas de débito, y produce un documento de roadmap defendible y altamente legible. El resultado está estructurado para la alineación multifuncional y finaliza con un documento técnico para volcar la planificación en ClickUp.

## Inputs Requeridos del Usuario

* **Marco temporal:** (ej. Q4 2026, H1 2027)
* **Objetivos Estratégicos/OKRs:** (ej. Aumentar tasa de activación de tarjetas, reducir pérdidas por fraude)
* **Backlog Crudo/Iniciativas:** (Una lista de funcionalidades, deuda técnica y tareas de compliance a priorizar)
* **Restricciones Conocidas:** (ej. Dependencias de proveedores, fechas límite regulatorias, capacidad)

## Formato y Estructura del Entregable

Genera la respuesta utilizando la siguiente estructura exacta:

### 1. Título y Encabezado
* Título: **Roadmap [Nombre del Producto/Squad] [Marco temporal]**
* Subtítulo: *Prioridades de Producto · Solicitud de Feedback Temprano*

### 2. Tabla de Criterios de Priorización
Crea una tabla definiendo cómo se evaluaron las iniciativas:
| Criterio | Lo que buscamos |
| :--- | :--- |
| **¿Mueve un OKR medible este trimestre?** | El impacto debe ser concreto, no solo "a futuro" o sin métrica clara. |
| **¿Resuelve un dolor documentado?** | Foco en fricción existente (ej. fallas en entrega de tarjetas). |
| **¿El equipo tiene capacidad real?** | Preferimos menos iniciativas cerradas con éxito que muchas a medias. |
| **¿Tiene dependencias externas confirmadas?** | Crucial (procesadores, redes como franquicias Visa/Mastercard). |

### 3. Los Pilares del Trimestre
Organiza la estrategia en 3-4 objetivos macro usando una tabla (Emoji, Pilar, Qué resuelve, Equipos).

### 4. Desglose de Iniciativas (Por Pilar)
Para cada pilar, lista las iniciativas priorizadas incluyendo:
* **El Problema Estructural:** ¿Por qué estamos haciendo esto?
* **La Solución/Valor:** ¿Cómo resuelve este problema la intervención?
* **Dependencias/Escala:** Cualquier dependencia regulatoria o del procesador.

### 5. La lista de "No por ahora" (Trade-offs)
Incluye 2-3 elementos muy solicitados que quedaron *fuera* para dar espacio al trabajo priorizado, e indica la razón exacta del porqué.

### 6. Cómo y cuándo darnos tu feedback
Termina el documento de comunicación con estas 4 preguntas:
* ¿Hay compromisos con clientes clave o aliados que no están reflejados en este plan?
* ¿Alguna iniciativa te genera una duda sobre el timing o el alcance?
* ¿Hay algo que esperabas ver y no está?
* ¿Algo que deberíamos pausar o reconsiderar dado el contexto actual?

---

### 7. Exportación para ClickUp (Archivo CSV)
Al final de tu respuesta, debes generar un segundo documento: un bloque de código en formato CSV (`csv`) que contenga únicamente las iniciativas aprobadas (las de la sección 4). Este bloque debe estar listo para copiarse, guardarse como `.csv` e importarse a ClickUp.

Usa exactamente estos encabezados de columna en la primera fila:
`Task Name,List Name,Status,Description,Timeframe`

* **Task Name:** El nombre de la iniciativa.
* **List Name:** El Pilar estratégico al que pertenece (esto creará la Lista o Carpeta en ClickUp).
* **Status:** Usa el estado "TO DO".
* **Description:** Una versión resumida (1 oración) de la solución/valor. *Asegúrate de encerrar la descripción entre comillas dobles para no romper el formato CSV por el uso de comas internas.*
* **Timeframe:** El marco temporal dado en el input original (ej. Q4 2026).

## Pautas de Generación
* **Tono:** Estratégico, decisivo y transparente.
* **Formato:** Usa Markdown limpio. Genera el CSV estrictamente en un bloque de código al final.
* **Precisión del CSV:** Verifica que no haya saltos de línea dentro de las filas del CSV y que los textos con comas estén entre comillas dobles.
