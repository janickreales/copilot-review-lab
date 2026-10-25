-- DDL de soporte de la capa bronze.
-- Se ejecuta con run_sql_file(); los nombres de tabla llegan como parámetros
-- nombrados y se resuelven con IDENTIFIER(), sin interpolar texto.

CREATE TABLE IF NOT EXISTS IDENTIFIER(:ingestion_log_table) (  -- noqa: LT01
    run_id STRING NOT NULL COMMENT 'Identificador de la corrida del job',
    source_table STRING NOT NULL COMMENT 'Tabla de origen en samples.tpch',
    target_table STRING NOT NULL COMMENT 'Tabla bronze de destino',
    row_count BIGINT COMMENT 'Filas escritas en la carga',
    ingested_at TIMESTAMP COMMENT 'Momento de la carga'
)
COMMENT 'Bitacora de cargas a la capa bronze';

CREATE TABLE IF NOT EXISTS IDENTIFIER(:dq_results_table) (  -- noqa: LT01
    run_id STRING NOT NULL COMMENT 'Identificador de la corrida del job',
    table_name STRING NOT NULL COMMENT 'Tabla evaluada',
    check_name STRING NOT NULL COMMENT 'not_null, unique o range',
    column_name STRING NOT NULL COMMENT 'Columna o claves evaluadas',
    failed_rows BIGINT COMMENT 'Filas que no cumplen la regla',
    total_rows BIGINT COMMENT 'Filas evaluadas',
    threshold DOUBLE COMMENT 'Proporcion maxima de fallos tolerada',
    passed BOOLEAN COMMENT 'Resultado del check',
    failed_ratio DOUBLE COMMENT 'failed_rows / total_rows',
    checked_at TIMESTAMP COMMENT 'Momento de la evaluacion'
)
COMMENT 'Resultados de los checks de calidad sobre bronze';
