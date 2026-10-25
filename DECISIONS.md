# Decisiones de diseño — retail_margin_lakehouse

Registro de las decisiones técnicas del pipeline. Cada cambio que las contradiga debe justificarse en el PR.

## 1. Orden de joins en `fact_margin`
Primero se une `silver_lineitem` con `dim_part_supplier` (que ya trae solo las partes filtradas), porque es el join que más filas descarta. Después se une con `silver_orders` y al final con `dim_supplier`.

## 2. Qué se broadcastea
- `silver_lineitem` (tabla de hechos) **nunca** se broadcastea.
- Las dimensiones se unen con `safe_broadcast_join`, que fuerza broadcast solo si el lado chico no supera `broadcast_max_rows` (config). No se usa `F.broadcast()` directo en los notebooks.
- `bronze_partsupp` sin filtrar (millones de filas) no se broadcastea; el lado chico de ese join son las partes filtradas.

## 3. Filtros antes de los joins
El filtro por nombre de parte (`part_name_filter`) y el recorte por fecha de pedido se aplican antes de cualquier join. El join con `dim_part_supplier` usa la clave compuesta `(l_partkey, l_suppkey)`: con solo `l_partkey`, cada línea se multiplica por todos los proveedores de la parte.

## 4. Particionado
Las tablas gold y `fact_margin` **no se particionan**. Su volumen (decenas de miles a pocos millones de filas) generaría archivos diminutos sin beneficio de partition pruning. Se revisará si alguna supera ~1 TB.

## 5. SQL parametrizado
- Ningún valor que llegue de widgets, parámetros del job o config se interpola en texto SQL (f-strings, `format`, concatenación).
- Valores y nombres de tabla se pasan como parameter markers (`:nombre`) y, para identificadores, con `IDENTIFIER(:nombre)`.
- Catálogo y esquema se validan con `validate_identifier` antes de usarse.

## 6. Formato de notebooks
- Por defecto, formato **Source** (`.py` / `.sql`): diffs limpios y revisables.
- Se usan `.ipynb` solo en 01, 04 y 07, como parte del laboratorio de comparación de formatos. Se commitean **sin outputs** (`nbstripout`).

## 7. Configuración por ambiente
- La identidad del destino (catálogo, esquema) se define por target en `databricks.yml` y llega al notebook como parámetro del job.
- Los parámetros funcionales (fechas, umbrales, filtros) viven en `config/<env>.json`.
- No se hardcodean catálogos ni esquemas en notebooks ni en recursos del bundle.

## 8. Schedules
Todo schedule declara `timezone_id` explícito (`America/Bogota`) y queda en `PAUSED` en dev.

## 9. Secretos
Ningún token, password ni credencial en el repo. Las credenciales van en secret scopes de Databricks o en secretos de GitHub.

## 10. Calidad de datos
Los checks de `02_quality_bronze` hacen fallar el task si no pasan. Cada tabla se cuenta una sola vez por corrida y el conteo se reutiliza en todos sus checks.
