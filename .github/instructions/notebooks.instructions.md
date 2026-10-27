---
applyTo: "notebooks/**"
---

# Reglas para notebooks

- Rendimiento: sin UDF de Python cuando existe una función nativa de Spark; sin `collect()` de tablas completas; sin `partitionBy` en tablas pequeñas (decisión 4 de `DECISIONS.md`).
- Los widgets que lee un notebook deben llegar como parámetro desde el job (`resources/margin_job.yml`) y desde `08_orchestrator.py`.
- En `.ipynb`, no propongas suggested changes: describe el arreglo en texto.
