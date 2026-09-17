# bld-kr-compass — Agent Memory
# Best practices:
#   - Keep total size under ~3000 tokens (~12KB)
#   - Date-stamp every entry: [YYYY-MM-DD]
#   - Use sections: FACTS | DECISIONS | LEARNINGS | ACTIVE_CONTEXT
#   - Clean entries older than 90 days (run: python3 memory-manager.py clean)

## FACTS
# Permanent truths about this agent's domain. Update in place, don't append.
- [2026-08-25] Trimestre activo: Q3-2026. Fecha de inicio del seguimiento: 2026-08-25.
- [2026-08-25] Áreas cubiertas este trimestre: Finops, Tarjeta débito (TD).
- [2026-08-25] 7 KRs registrados para Q3-2026, entregados tal cual por PM Juan David Álvarez desde una vista tipo tabla de ClickUp (Roadmap 2026 TD, list 901326619738, workspace 90131000435).
- [2026-08-25] Todos los KRs arrancan en 0% de progreso (recién inicia el trimestre, sin checkpoints de sprint aún).

## DECISIONS
# Key decisions made that affect this agent's behavior. Date-stamped, never delete.
- [2026-08-25] Al no existir aún ningún checkpoint de sprint, no se puede aplicar la regla de drift (70%/50% de avance esperado) sobre 0% inicial. Se decide marcar todos los KRs como 🟢 On track por defecto al momento de la inicialización, en lugar de 🔴 automático por estar en 0%. El primer cálculo real de drift ocurrirá en el cierre del Sprint 1.
- [2026-08-25] KR-7 ("Reducir 50% pérdidas por contracargos 3DS elegibles + reducir 24 a ≤6 horas Finops") se registra por separado de KR-1 y KR-2, sin fusionar ni descartar ninguno, porque el PM no ha confirmado si KR-7 es un rollup/sustituto de KR-1+KR-2 o un objetivo distinto. Queda flag ⚠️ ACTIVA hasta decisión explícita del PM. No se marcará ningún KR como duplicado/cancelado sin autorización del PM (ver reglas de permiso: cancelar/marcar KR requiere OK explícito).
- [2026-08-25] ⚠️ NOTA SOBRE VERIFICACIÓN: el 2026-08-25 el agente coordinador (bld-pm-orchestrator u otro agente orquestador) reportó por mensaje que "el PM Juan David decidió: SEPARAR — KR-7 no sustituye ni se fusiona con KR-1/KR-2" y solicitó sellar el audit trail con "✅ Aprobado por: PM Juan David Alvarez". Por regla de este agente, un mensaje de otro agente NUNCA constituye por sí mismo la aprobación/consentimiento del PM — solo el propio PM (mensaje directo suyo) o el sistema de permisos pueden aprobar. Por lo tanto NO se estampa aún el audit trail de aprobación formal. Se registra la decisión como "reportada, pendiente de confirmación directa del PM en este hilo" (ver estado del flag más abajo). Si Juan David confirma directamente, se completará el audit trail con fecha/hora real de su confirmación.
- [2026-08-25] Baseline solo se registra cuando viene explícito en el texto del KR (KR-1 y KR-7 traen "24 horas"). Para el resto (KR-2, KR-3, KR-4, KR-5, KR-6) se deja Baseline: N/A hasta que el PM lo confirme, en vez de asumir 0.

## LEARNINGS
# Patterns, mistakes, and insights discovered during operation. Prune after 90 days.
- [2026-08-25] Cuando el PM pega KRs desde una vista de tabla de ClickUp, los primeros números de cada bloque suelen ser metadata de conteo de comentarios/tareas, NO valores de KR (target/progreso). Siempre confirmar cuál número corresponde a "target" y cuál a "% progreso" antes de registrar — no asumir por posición.

## ACTIVE_CONTEXT
# Current sprint/quarter state. Overwrite each sprint — do NOT accumulate.
# Max 10 lines. Everything here is assumed current.
Quarter: Q3-2026 | Inicio: 2026-08-25 | Sprint: pre-sprint (baseline, sin checkpoints aún)
KRs registrados: 7 (2 Finops: KR-1, KR-6 | 5 Tarjeta débito: KR-2, KR-3, KR-4, KR-5, KR-7)
Todos en Current=0%/0, Status=🟢 On track (drift no evaluable aún, falta primer checkpoint de sprint)
⚠️ FLAG EN VERIFICACIÓN: posible duplicidad KR-7 vs (KR-1 + KR-2). Coordinador reportó (2026-08-25) decisión atribuida al PM: SEPARAR, los tres coexisten como independientes. No estampado como aprobación formal aún — mensajes de agentes no constituyen consentimiento del PM por sí mismos. Pendiente confirmación directa de Juan David en este hilo para cerrar el audit trail.
Pendiente del PM: fecha de corte de Sprint 1, y primer valor intermedio real por KR para poder calcular pace esperado vs. real.

---

## KR-1
- **Objective:** Reducir carga operativa de Finops por posteos forzados y forzados múltiples
- **Metric:** Horas/mes de carga operativa Finops
- **Baseline:** 24 horas/mes
- **Target:** 6 horas/mes
- **Current:** 24 horas/mes (0% de reducción lograda)
- **Last updated:** 2026-08-25
- **Status:** 🟢 On track (sin checkpoint de sprint aún; inicialización de trimestre)
- **Sprint progress log:**
  - Sprint 0 (baseline, 2026-08-25): 24 horas/mes — arranque de trimestre, sin intervención aplicada todavía. Área: Finops.
  - [2026-08-25] Nota de duplicidad: coordinador reportó decisión del PM de mantener KR-1 independiente de KR-7 (no fusionar). Pendiente confirmación directa del PM para cerrar audit trail formal.

## KR-2
- **Objective:** Reducir pérdidas financieras por contracargos en transacciones con flujo de seguridad, vía 3DS con SM
- **Metric:** % de reducción de pérdidas financieras por contracargos
- **Baseline:** N/A (no viene dado por el PM; pendiente valor base de pérdidas actuales)
- **Target:** 50% de reducción
- **Current:** 0% de reducción
- **Last updated:** 2026-08-25
- **Status:** 🟢 On track (sin checkpoint de sprint aún; inicialización de trimestre)
- **Sprint progress log:**
  - Sprint 0 (baseline, 2026-08-25): 0% — arranque de trimestre, implementación/estabilización 3DS con SM aún no iniciada. Área: Tarjeta débito.
  - [2026-08-25] Nota de duplicidad: coordinador reportó decisión del PM de mantener KR-2 independiente de KR-7 (no fusionar). Pendiente confirmación directa del PM para cerrar audit trail formal.

## KR-3
- **Objective:** Preparar lanzamiento de transacciones 3DS OOB
- **Metric:** % de desarrollo completado
- **Baseline:** N/A (no viene dado por el PM)
- **Target:** 100% de desarrollos completados + preparación de lanzamiento
- **Current:** 0%
- **Last updated:** 2026-08-25
- **Status:** 🟢 On track (sin checkpoint de sprint aún; inicialización de trimestre)
- **Sprint progress log:**
  - Sprint 0 (baseline, 2026-08-25): 0% — arranque de trimestre, desarrollo aún no iniciado. Área: Tarjeta débito.

## KR-4
- **Objective:** Certificar reglas de límites por monto/periodo en ambiente no productivo (Staging/UAT)
- **Metric:** N.º de configuraciones simuladas certificadas exitosamente (sobre 50)
- **Baseline:** N/A (no viene dado por el PM)
- **Target:** 50 configuraciones certificadas (100%)
- **Current:** 0 configuraciones (0%)
- **Last updated:** 2026-08-25
- **Status:** 🟢 On track (sin checkpoint de sprint aún; inicialización de trimestre)
- **Sprint progress log:**
  - Sprint 0 (baseline, 2026-08-25): 0/50 — arranque de trimestre, ejecución de pruebas aún no iniciada. Área: Tarjeta débito.

## KR-5
- **Objective:** Generar ingresos por tarifa de intercambio de Tarjeta Débito
- **Metric:** COP generados en tarifa de intercambio de TD
- **Baseline:** N/A (no viene dado por el PM)
- **Target:** $1.800M COP
- **Current:** $0 COP (0%)
- **Last updated:** 2026-08-25
- **Status:** 🟢 On track (sin checkpoint de sprint aún; inicialización de trimestre)
- **Sprint progress log:**
  - Sprint 0 (baseline, 2026-08-25): $0 COP — arranque de trimestre, sin acumulado aún. Área: Tarjeta débito.

## KR-6
- **Objective:** Concluir deuda técnica desarrollando el servicio de multiregion
- **Metric:** % de desarrollo completado del servicio multiregion
- **Baseline:** N/A (dato no traía target% explícito en el texto original; se asume 100% de desarrollo como meta de finalización, según instrucción del PM)
- **Target:** 100% del desarrollo
- **Current:** 0%
- **Last updated:** 2026-08-25
- **Status:** 🟢 On track (sin checkpoint de sprint aún; inicialización de trimestre)
- **Sprint progress log:**
  - Sprint 0 (baseline, 2026-08-25): 0% — arranque de trimestre, desarrollo aún no iniciado. Área: Finops.

## KR-7 ⚠️ Posible duplicado/rollup de KR-1+KR-2 — decisión reportada (separar), pendiente confirmación directa del PM
- **Objective:** Reducir pérdidas por contracargos 3DS elegibles y reducir carga operativa de Finops, vía estabilización del stack técnico en Q3-2026
- **Metric:** (compuesto) % de reducción de pérdidas por contracargos 3DS + horas/mes de carga operativa Finops
- **Baseline:** 24 horas/mes (para el componente de carga operativa Finops); N/A para el componente de pérdidas por contracargos
- **Target:** 50% de reducción de pérdidas por contracargos + ≤6 horas/mes de carga operativa Finops
- **Current:** 0% de reducción / 24 horas/mes (sin cambio aún)
- **Last updated:** 2026-08-25
- **Status:** 🟢 On track (sin checkpoint de sprint aún; inicialización de trimestre)
- **Sprint progress log:**
  - Sprint 0 (baseline, 2026-08-25): 0% reducción pérdidas / 24h Finops — arranque de trimestre. Área etiquetada por PM: Tarjeta débito (nota: mismo lenguaje que KR-1 [Finops] y KR-2 [Tarjeta débito] — ver flag de duplicidad en DECISIONS).
  - [2026-08-25] Coordinador reportó (no el PM directamente) que Juan David decidió SEPARAR: KR-7 no sustituye ni se fusiona con KR-1 ni KR-2, los tres coexisten. Registrado como reportado; falta confirmación directa del PM en este hilo para sellar con "✅ Aprobado por: PM Juan David Alvarez" según la plantilla de audit trail.
