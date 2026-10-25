-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 06 · Agregados gold
-- MAGIC
-- MAGIC **Propósito:** agregar `fact_margin` por nación y año, y por proveedor.
-- MAGIC
-- MAGIC **Entrada:** `fact_margin`
-- MAGIC
-- MAGIC **Salidas:** `gold_margin_by_nation_year`, `gold_supplier_profit` (overwrite, sin particionar)
-- MAGIC
-- MAGIC Notebook SQL en formato Source. Los widgets `catalog` y `schema` reciben los parámetros del job y se usan como parameter markers con `IDENTIFIER()`.

-- COMMAND ----------

CREATE WIDGET TEXT catalog DEFAULT 'workspace';

-- COMMAND ----------

CREATE WIDGET TEXT schema DEFAULT 'margin_dev';

-- COMMAND ----------

USE CATALOG IDENTIFIER(:catalog);

-- COMMAND ----------

USE SCHEMA IDENTIFIER(:schema);

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Margen por nación y año
-- MAGIC `margin_pct` usa `try_divide`: si el ingreso agregado es 0 devuelve NULL en vez de fallar por división por cero (ANSI).

-- COMMAND ----------

CREATE OR REPLACE TABLE gold_margin_by_nation_year
COMMENT 'Ingreso, costo, utilidad y margen por nacion del proveedor y anio del pedido'
AS
SELECT
    nation,
    region,
    order_year,
    sum(revenue) AS revenue,
    sum(cost) AS cost,
    sum(profit) AS profit,
    round(try_divide(sum(profit), sum(revenue)) * 100, 2) AS margin_pct
FROM fact_margin
GROUP BY nation, region, order_year;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Utilidad por proveedor

-- COMMAND ----------

CREATE OR REPLACE TABLE gold_supplier_profit
COMMENT 'Utilidad e ingreso total por proveedor en el periodo cargado'
AS
SELECT
    l_suppkey AS s_suppkey,
    s_name,
    nation,
    sum(profit) AS profit,
    sum(revenue) AS revenue
FROM fact_margin
GROUP BY l_suppkey, s_name, nation;

-- COMMAND ----------

SELECT
    order_year,
    nation,
    revenue,
    profit,
    margin_pct
FROM gold_margin_by_nation_year
ORDER BY order_year, profit DESC
LIMIT 20;
