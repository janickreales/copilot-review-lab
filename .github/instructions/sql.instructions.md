---
applyTo: "**/*.sql"
---

# Reglas para archivos SQL

- Toda tabla o vista creada (`CREATE TABLE`, `CREATE OR REPLACE TABLE`, `CREATE OR REPLACE VIEW`) debe llevar `COMMENT` describiendo su contenido. Es un requisito del catálogo de datos, no una cuestión de estilo: repórtalo si falta.
- Antes de un join, verifica la granularidad (clave única) de cada lado; un join que multiplica filas es un error de correctitud.
- `MERGE` siempre con la clave de negocio completa en el `ON`.
- `GRANT`: nunca `ALL PRIVILEGES`, nunca a `account users`.
