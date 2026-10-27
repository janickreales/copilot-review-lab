import json
from datetime import date

import pytest

from src.utils.config_loader import load_config, validate_identifier

VALID = {
    "date_from": "1996-01-01",
    "date_to": "1996-12-31",
    "part_name_filter": "green",
    "broadcast_max_rows": 500000,
    "quality": {
        "max_null_ratio": 0.0,
        "max_duplicate_ratio": 0.0,
        "min_discount": 0.0,
        "max_discount": 0.1,
    },
    "report_top_n": 25,
}


@pytest.fixture
def config_dir(tmp_path):
    (tmp_path / "dev.json").write_text(json.dumps(VALID), encoding="utf-8")
    return str(tmp_path)


def test_load_config_builds_typed_config(config_dir):
    cfg = load_config("dev", "workspace", "margin_dev", config_dir)

    assert cfg.date_from == date(1996, 1, 1)
    assert cfg.quality.max_discount == 0.1
    assert cfg.table("fact_margin") == "workspace.margin_dev.fact_margin"


@pytest.mark.parametrize("bad", ["", "margin-dev", "x; DROP TABLE y", "1schema", "a.b"])
def test_validate_identifier_rejects_unsafe_names(bad):
    with pytest.raises(ValueError):
        validate_identifier(bad, "schema")


def test_load_config_rejects_unknown_env(config_dir):
    with pytest.raises(ValueError, match="Unknown env"):
        load_config("qa", "workspace", "margin_dev", config_dir)


def test_load_config_rejects_inverted_dates(tmp_path):
    inverted = {**VALID, "date_from": "1997-01-01", "date_to": "1996-01-01"}
    (tmp_path / "dev.json").write_text(json.dumps(inverted), encoding="utf-8")

    with pytest.raises(ValueError, match="after date_to"):
        load_config("dev", "workspace", "margin_dev", str(tmp_path))


def test_table_rejects_invalid_names(config_dir):
    cfg = load_config("dev", "workspace", "margin_dev", config_dir)

    with pytest.raises(ValueError):
        cfg.table("fact-margin")
