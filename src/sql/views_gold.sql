-- Vistas de consumo sobre la capa gold.
-- Se ejecuta despues de fijar el catalogo y esquema actuales (00_config):
-- las referencias sin calificar se resuelven contra ese contexto, que la
-- vista guarda al crearse.

CREATE OR REPLACE VIEW v_margin_report
COMMENT 'Margen por nacion y anio, con ranking dentro de cada anio'
AS
SELECT
    g.nation,
    g.region,
    g.order_year,
    g.revenue,
    g.cost,
    g.profit,
    g.margin_pct,
    rank() OVER (PARTITION BY g.order_year ORDER BY g.profit DESC) AS profit_rank
FROM gold_margin_by_nation_year AS g;

CREATE OR REPLACE VIEW v_top_suppliers
COMMENT 'Proveedores con mayor utilidad total en el periodo cargado'
AS
SELECT
    s.s_suppkey,
    s.s_name,
    s.nation,
    g.region,
    s.profit,
    s.revenue,
    dense_rank() OVER (ORDER BY s.profit DESC) AS profit_rank
FROM gold_supplier_profit AS s
INNER JOIN gold_margin_by_nation_year AS g
    ON s.nation = g.nation;
