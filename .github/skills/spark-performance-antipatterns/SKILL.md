---
name: spark-performance-antipatterns
description: Revisa cambios en notebooks y código PySpark/Delta de este repo en busca de antipatrones de rendimiento de Spark (particionado de tablas pequeñas, UDF de Python, broadcast del lado grande, collect y count repetidos). Úsala en todo PR que toque notebooks/ o src/utils/.
---

# Antipatrones de rendimiento en Spark/Delta

Revisa cada línea cambiada contra esta lista. Si encuentras uno, publícalo como hallazgo propio (no lo agrupes con otros) y cita la regla.

## 1. `partitionBy` en tablas pequeñas — siempre reportar
- `fact_margin`, las tablas gold y los reportes (`rpt_*`) **no se particionan** (decisión 4 de `DECISIONS.md`).
- Cualquier `.partitionBy(...)` sobre esas tablas es un hallazgo **Medium**, aunque la escritura funcione.
- No propongas "arreglos" que hagan funcionar el particionado (por ejemplo, agregar `overwriteSchema`). El arreglo correcto es quitar `partitionBy` y volver a `write_delta`.

## 2. UDF de Python con equivalente nativo
- Una `@F.udf` que hace aritmética, casts o funciones de texto disponibles en `pyspark.sql.functions` es un hallazgo **Medium**: pierde las optimizaciones de Catalyst y serializa cada fila entre la JVM y Python.

## 3. Broadcast del lado grande
- `silver_lineitem` nunca se broadcastea; las dimensiones se unen con `safe_broadcast_join`. Un `F.broadcast()` directo en un notebook es un hallazgo.

## 4. Acciones redundantes
- `collect()` de una tabla completa al driver → **High**.
- Llamar `.count()` varias veces sobre el mismo DataFrame → **Medium**.
