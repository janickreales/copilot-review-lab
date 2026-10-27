---
name: databricks-bundle-conventions
description: Revisa cambios en databricks.yml y resources/*.yml (Databricks Asset Bundles) contra las convenciones del repo para jobs, schedules, parámetros y dependencias entre tasks. Úsala en todo PR que toque esos archivos.
---

# Convenciones de Databricks Asset Bundles

Revisa cada cambio en `databricks.yml` y `resources/*.yml` contra estas reglas. Publica cada incumplimiento como hallazgo propio.

## Schedules
- Todo `schedule` debe declarar `timezone_id` explícito (`America/Bogota`). Sin él, Databricks usa UTC y el job corre a otra hora. → **Medium**.
- `pause_status` debe venir de `${var.schedule_pause_status}`; en dev el job queda `PAUSED`. Un valor fijo `UNPAUSED` hace que el job de dev corra solo. → **High**.

## Parámetros
- `catalog` y `schema` siempre desde `${var.catalog}` / `${var.schema}`; nunca valores fijos. → **Medium**.

## Dependencias entre tasks
- Cada task debe declarar en `depends_on` todas las tasks que producen las tablas que lee su notebook. → **High** si falta una.
