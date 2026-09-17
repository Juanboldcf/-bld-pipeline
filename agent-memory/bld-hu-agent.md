# bld-hu-agent — Agent Memory
# Best practices:
#   - Keep total size under ~3000 tokens (~12KB)
#   - Date-stamp every entry: [YYYY-MM-DD]
#   - Use sections: FACTS | DECISIONS | LEARNINGS | ACTIVE_CONTEXT
#   - Clean entries older than 90 days (run: python3 memory-manager.py clean)

## FACTS
# Permanent truths about this agent's domain. Update in place, don't append.
# Example: [2026-06-10] ClickUp workspace ID = XXXXX
- [2026-08-25] Backend actual de Issuing (Tarjeta Débito), mapeado por Intern Ron sobre bold-backend @ commit a47fa78 (origin/master), validado por PM Juan David en Slack (10/10). Versión completa con file:line: https://docs.superhuman.com/d/_dEZ9a83sgWu (puede dar 403 a terceros — pedir a Pope Davis ampliar acceso de lectura).
- [2026-08-25] TARJETA FÍSICA (client app): request/reissue enviada (session) [legacy deprecado], instant-issue request (session), activar instant-issue (session+TOTP, con fallback a activación de física ordinaria si no hay instant-issue — TODO en código), pin_enable_key (session, SIN TOTP) vs pin_change_key (session+TOTP, asimetría real), commit-pin / commit-pin-change (session), freeze/unfreeze/block permanente (session+TOTP). BLOCKED es terminal — NO hay unblock permanente para nadie. Leer datos sensibles (session+TOTP) vs no-sensibles (session). BNPL enable/disable (session, requiere status ENABLED). GET /pin (redirect issuer) y GET block-reasons son SIN auth.
- [2026-08-25] TARJETA VIRTUAL (client app): crear (session) — se crea YA ENABLED como child card de Galileo, sin paso de activación (a diferencia de física). Eliminar (session+TOTP) es el único terminal — NO existe bloqueo de virtual, solo delete (borra cuenta hija Galileo, no afecta física padre). Freeze/unfreeze y BNPL (session/session+TOTP). Límites configurables: 3 tarjetas activas y 10 creaciones/mes por depósito (no hardcoded).
- [2026-08-25] WALLETS/TOKENIZACIÓN: Apple provisioning-token es la única ruta de este grupo SIN session check; su gemela Google SÍ la tiene. Enrollment/listado/activación de tokens: session. Resuelven la tarjeta vía lookup física→virtual compartido (ambas familias tokenizables).
- [2026-08-25] BACKOFFICE (team-auth authorizer, SIN permiso por rol declarado a nivel de ruta): request/reissue física, lookup física/virtual, buscar clientes, preventive-block/remove (reversible → ENABLED) vs permanent block (terminal, sin unblock, actualiza registro instant-issue relacionado). Reissuing-reasons SIN auth. Cobro por reissue está feature-flagged.
- [2026-08-25] GAPS confirmados (= oportunidades reales de HU nuevas, no bugs pendientes de dev): (1) NO existe unblock de bloqueo permanente de física, ni cliente ni BackOffice. (2) NO existe delete/cancel de física (virtual sí tiene). (3) NO existe límite de gasto configurable por cliente, ni control por comercio/categoría, ni switch de canal. (4) NO existe endpoint de tracking de courier — solo visible vía "latest card for deposit". (5) Sin resolver: legacy POST /clients/myself/debit-cards/{id}/activate no tiene handler ni ruta desplegada — v2 instant activation es lo real en producción.
- [2026-08-25] Internal/issuer callbacks (Galileo, Idemia, Logistics, Merchants) no llevan auth de usuario. El consumer de ATM allowance hace product routing automático (Galileo free-fee vs all-fee) — NO es un límite de gasto configurado por el usuario, fácil de confundir con uno.

## DECISIONS
# Key decisions made that affect this agent's behavior. Date-stamped, never delete.
# Example: [2026-06-10] Audit trail required on all ClickUp comments — PM approval needed
- [2026-08-25] Al escribir la sección 🏗️ Cómo (Especificaciones Técnicas) de cada HU de Issuing/Tarjeta Débito, citar el endpoint real ya existente de FACTS cuando la HU lo reutilice, o marcar explícitamente "endpoint nuevo" si no aparece en el mapa — nunca asumir soporte no confirmado.

## LEARNINGS
# Patterns, mistakes, and insights discovered during operation. Prune after 90 days.
# Example: [2026-06-10] Stakeholder X prefers Slack DM over email for feedback requests

## ACTIVE_CONTEXT
# Current sprint/quarter state. Overwrite each sprint — do NOT accumulate.
# Max 10 lines. Everything here is assumed current.
# Example: Current quarter: Q3-2026 | Sprint: Sprint 12 | KR focus: Revenue +20%
