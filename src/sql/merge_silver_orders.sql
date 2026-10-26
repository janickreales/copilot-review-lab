-- Upsert incremental de silver_lineitem desde la vista temporal
-- silver_lineitem_updates (creada por 03_silver_orders).
-- Clave de negocio de una linea de pedido: (l_orderkey, l_linenumber).

CREATE TABLE IF NOT EXISTS IDENTIFIER(:target_table) (  -- noqa: LT01
    l_orderkey BIGINT NOT NULL,
    l_linenumber INT NOT NULL,
    l_partkey BIGINT NOT NULL,
    l_suppkey BIGINT NOT NULL,
    l_quantity DECIMAL(18, 2),
    l_extendedprice DECIMAL(18, 2),
    l_discount DECIMAL(18, 2),
    l_shipdate DATE,
    net_revenue DECIMAL(38, 4),
    _ingested_at TIMESTAMP,
    _updated_at TIMESTAMP
)
COMMENT 'Lineas de pedido limpias y deduplicadas';

MERGE INTO IDENTIFIER(:target_table) AS t  -- noqa: LT01
USING silver_lineitem_updates AS s
    ON
        t.l_orderkey = s.l_orderkey
WHEN MATCHED AND s._ingested_at > t._ingested_at THEN
    UPDATE SET
        t.l_partkey = s.l_partkey,
        t.l_suppkey = s.l_suppkey,
        t.l_quantity = s.l_quantity,
        t.l_extendedprice = s.l_extendedprice,
        t.l_discount = s.l_discount,
        t.l_shipdate = s.l_shipdate,
        t.net_revenue = s.net_revenue,
        t._ingested_at = s._ingested_at,
        t._updated_at = current_timestamp()
WHEN NOT MATCHED THEN INSERT (
    l_orderkey,
    l_linenumber,
    l_partkey,
    l_suppkey,
    l_quantity,
    l_extendedprice,
    l_discount,
    l_shipdate,
    net_revenue,
    _ingested_at,
    _updated_at
) VALUES (
    s.l_orderkey,
    s.l_linenumber,
    s.l_partkey,
    s.l_suppkey,
    s.l_quantity,
    s.l_extendedprice,
    s.l_discount,
    s.l_shipdate,
    s.net_revenue,
    s._ingested_at,
    current_timestamp()
);
