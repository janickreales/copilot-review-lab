# AGENTS.md — retail_margin_lakehouse

Resumen de las decisiones de diseño (detalle en `DECISIONS.md`). Aplica a cualquier agente que lea o modifique este repo.

1. **Orden de joins en `fact_margin`:** primero `dim_part_supplier` (ya filtrada), luego `silver_orders`, al final `dim_supplier`.
2. **Broadcast:** `silver_lineitem` nunca se broadcastea. Las dimensiones se unen con `safe_broadcast_join`; no usar `F.broadcast()` directo en notebooks.
3. **Filtros antes de los joins.** El join con `dim_part_supplier` usa la clave compuesta `(l_partkey, l_suppkey)`.
4. **No particionar** `fact_margin`, las tablas gold ni los reportes: su volumen no justifica `partitionBy`.
5. **SQL parametrizado:** nada de f-strings ni concatenación con valores de widgets, parámetros o config. Usar parameter markers e `IDENTIFIER(:nombre)`.
6. **Formato de notebooks:** Source (`.py` / `.sql`) por defecto; `.ipynb` solo en 01, 04 y 07, sin outputs.
7. **Configuración por ambiente:** catálogo y esquema vienen del target del bundle; nada hardcodeado.
8. **Schedules** con `timezone_id` explícito y `PAUSED` en dev.
9. **Sin secretos** en el repo.
10. **Calidad de datos:** los checks hacen fallar el task; cada tabla se cuenta una sola vez por corrida.

Además:
- Preferir expresiones nativas de Spark a UDF de Python.
- No hacer `collect()` de tablas completas al driver.
