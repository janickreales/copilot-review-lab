"""Carga y valida la configuración del pipeline.

La identidad del destino (catálogo y esquema) llega como parámetro del job,
definido por target en databricks.yml. El resto de parámetros vive en
config/<env>.json para que dev y prod difieran solo en datos, no en código.
"""

import json
import os
import re
from dataclasses import dataclass
from datetime import date

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_VALID_ENVS = ("dev", "prod")


@dataclass(frozen=True)
class QualityThresholds:
    max_null_ratio: float
    max_duplicate_ratio: float
    min_discount: float
    max_discount: float


@dataclass(frozen=True)
class PipelineConfig:
    env: str
    catalog: str
    schema: str
    date_from: date
    date_to: date
    part_name_filter: str
    broadcast_max_rows: int
    quality: QualityThresholds
    report_top_n: int

    def table(self, name: str) -> str:
        """Nombre totalmente calificado de una tabla del pipeline."""
        validate_identifier(name, "table")
        return f"{self.catalog}.{self.schema}.{name}"


def validate_identifier(value: str, kind: str) -> str:
    """Rechaza identificadores que no sean nombres simples de Unity Catalog.

    Los nombres de catálogo, esquema y tabla terminan dentro de sentencias
    SQL; validarlos aquí evita que un parámetro del job inyecte SQL.
    """
    if not _IDENTIFIER.match(value or ""):
        raise ValueError(f"Invalid {kind} identifier: {value!r}")
    return value


def load_config(env: str, catalog: str, schema: str, config_dir: str) -> PipelineConfig:
    """Construye la configuración a partir de los parámetros del job y del JSON del ambiente."""
    if env not in _VALID_ENVS:
        raise ValueError(f"Unknown env {env!r}; expected one of {_VALID_ENVS}")
    validate_identifier(catalog, "catalog")
    validate_identifier(schema, "schema")

    path = os.path.join(config_dir, f"{env}.json")
    with open(path, encoding="utf-8") as handle:
        raw = json.load(handle)

    date_from = date.fromisoformat(raw["date_from"])
    date_to = date.fromisoformat(raw["date_to"])
    if date_from > date_to:
        raise ValueError(f"date_from {date_from} is after date_to {date_to}")

    return PipelineConfig(
        env=env,
        catalog=catalog,
        schema=schema,
        date_from=date_from,
        date_to=date_to,
        part_name_filter=raw["part_name_filter"],
        broadcast_max_rows=int(raw["broadcast_max_rows"]),
        quality=QualityThresholds(**raw["quality"]),
        report_top_n=int(raw["report_top_n"]),
    )
