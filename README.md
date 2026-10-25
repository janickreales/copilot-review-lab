# copilot-review-lab · retail_margin_lakehouse

Proyecto Databricks de laboratorio para probar GitHub Copilot code review (ver `plan-pruebas-v2.md` en la carpeta de investigación).

Pipeline medallion sobre `samples.tpch`: calcula ingreso, costo, utilidad y margen por nación, año y proveedor, para las partes cuyo nombre contiene un filtro configurable.

## Estructura

| Ruta | Contenido |
|---|---|
| `databricks.yml` | Bundle con targets `dev` y `prod` y variables `env`, `catalog`, `schema` |
| `resources/margin_job.yml` | Job `margin_pipeline` (DAG de 8 tasks) y job `margin_pipeline_orchestrated` (un notebook que ejecuta los demás) |
| `config/<env>.json` | Fechas, filtros y umbrales por ambiente |
| `src/utils/` | Librería compartida: config, helpers de Spark, calidad, logging |
| `src/sql/` | DDL de bronze, MERGE de silver, vistas gold |
| `notebooks/` | 9 notebooks: 5 `.py` (Source), 3 `.ipynb`, 1 `.sql` (Source) |
| `tests/` | pytest + chispa (Spark local) |
| `DECISIONS.md` | Decisiones de diseño |

## Flujo de datos

```
samples.tpch ──01──▶ bronze_* ──02 (calidad)──┬─03──▶ silver_orders, silver_lineitem ─┐
                                              └─04──▶ dim_part_supplier, dim_supplier ┴─05──▶ fact_margin
fact_margin ──06 (SQL)──▶ gold_margin_by_nation_year, gold_supplier_profit ──07──▶ v_margin_report, v_top_suppliers, rpt_margin_top_nations
```

| Notebook | Formato | Depende de | Cómo |
|---|---|---|---|
| `00_config` | .py | `src/utils/config_loader`, `config/*.json` | import; task `setup` del job |
| `01_ingest_bronze` | .ipynb | 00, `src/sql/ddl_bronze.sql` | `%run`, `run_sql_file` |
| `02_quality_bronze` | .py | 00, `src/utils/quality`, celda `%sql` | `%run`, import |
| `03_silver_orders` | .py | 00, `src/utils/spark_helpers`, `src/sql/merge_silver_orders.sql` | `%run`, import, `run_sql_file` |
| `04_dim_supplier_part` | .ipynb | 00, `safe_broadcast_join`, celdas `%sql` | `%run`, import |
| `05_fact_margin` | .py | 00, 03, 04 (tablas), `safe_broadcast_join` | `%run`, import, task value `fact_rows` |
| `06_gold_aggregates` | .sql | 05 (tabla), widgets `catalog`/`schema` | parameter markers |
| `07_export_report` | .ipynb | 00, 06 (tablas), `src/sql/views_gold.sql`, task value de 05 | `%run`, `run_sql_file`, `taskValues.get` |
| `08_orchestrator` | .py | 00, 01–07 | `dbutils.notebook.run` |

## F0 — Preparación (pasos que haces tú)

1. **Repo en GitHub.** Crear `copilot-review-lab` (decisión D1 del plan: público recomendado). El repo local ya está inicializado en `main`, sin commits. Primer commit y push:
   ```bash
   git add . && git commit -m "Baseline del laboratorio"
   git remote add origin https://github.com/<tu-usuario>/copilot-review-lab.git
   git push -u origin main
   ```
   El tag `baseline-v1` se crea **después** de cumplir el checklist de "Baseline del laboratorio" (más abajo): `git tag baseline-v1 && git push origin baseline-v1`.
2. **Databricks Free Edition.** Crear un PAT (User settings → Developer → Access tokens) y un perfil local:
   ```bash
   databricks auth login --host https://<tu-workspace>.cloud.databricks.com --profile lab
   ```
3. **Ajustes de Copilot (capturas de pantalla para la evidencia):**
   - github.com/settings/copilot/features → Privacy → entrenamiento con tus datos: **Disabled**.
   - Copilot settings → Code review → esfuerzo por defecto: **Lite** explícito.
   - Revisión automática personal: **apagada** (se enciende en F6).
4. **Saldo de créditos inicial: 1,500.** Desde aquí, protocolo §5.1 del plan: saldo antes y después de **cada** acción de Copilot.
5. **Secretos para CI (opcional):** `DATABRICKS_HOST` y `DATABRICKS_TOKEN` en Settings → Secrets → Actions, para que corra `bundle validate`.

## Despliegue y corrida

```bash
databricks bundle validate -t dev -p lab
databricks bundle deploy -t dev -p lab
databricks bundle run margin_pipeline -t dev -p lab
```

Dev carga solo 1996 (`config/dev.json`) para que la corrida sea liviana en Free Edition.

## Validaciones pendientes en el workspace

Estas construcciones no se pudieron probar fuera de Databricks; confirmarlas en la primera corrida:

- `06_gold_aggregates.sql`: `CREATE WIDGET` + `USE CATALOG IDENTIFIER(:catalog)` con los parámetros del job.
- Celdas `%sql` dentro de los `.ipynb` (04).
- `sys.path` hacia la raíz del bundle desde `notebooks/` (00) en serverless.
- `dbutils.notebook.run` con rutas relativas sin extensión (08).

## Baseline del laboratorio

`main` es la línea base limpia, etiquetada `baseline-v1`. Antes de empezar las pruebas debe cumplir:

- [ ] CI en verde (ruff, sqlfluff, pytest; `bundle validate` si hay secretos).
- [ ] `bundle deploy` + `run` con todas las tasks en `SUCCESS`.
- [ ] Una revisión Lite de Copilot sin comentarios de severidad media o alta (si los hay, corregir, repetir y mover el tag).

**Reglas del laboratorio:**
- Toda rama de prueba sale de `baseline-v1`.
- `main` no tiene `.github/copilot-instructions.md`, `AGENTS.md` ni skills: F1 es el control sin instrucciones.
- Los outputs de notebooks se eliminan con `nbstripout`. La rama del defecto S4 (PII ficticia en outputs) se commitea con `--no-verify` a propósito.
