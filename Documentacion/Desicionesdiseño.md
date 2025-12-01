# Design Decisions — Agente Funcional Médico (Resumen)

Este documento justifica las decisiones técnicas tomadas en el proyecto (IE4).

## 1. Elección de modelos
- LLM: `gpt-4o-mini` seleccionado por balance entre capacidad y latencia en entornos de demostración. Se documenta la opción de cambiar a `gpt-4o` o modelos específicos de Azure si se requiere mayor precisión.
- Embeddings: `text-embedding-3-small` elegido por compatibilidad con vectores compactos y rendimiento aceptable.

## 2. Arquitectura RAG
- Componente de embeddings localmente calculado y mantenido en memoria (`self.embedding_matrix`) para búsquedas por similitud.
- Búsqueda híbrida: combinación semántica (cosine_similarity) + heurística léxica (intersección de palabras) con pesos 0.7/0.3 respectivamente.

## 3. Seguridad y privacidad
- Input sanitization (`sanitize_input`) y filtros éticos (`ethical_check`) para mitigar prompt injection y solicitudes inadecuadas.
- Persistencia de logs y mensajes con enmascaramiento PII antes de guardado (`_mask_pii`).

## 4. Observabilidad
- Uso de `structlog` para logs estructurados en JSON, métricas calculadas en `metrics` por interacción y dashboard con export CSV.

## 5. Escalabilidad y mejoras futuras
- Recomendación: migrar almacenamiento de logs y memoria a una base de datos (SQLite/Postgres) para producción.
- Pipeline de ingestión de documentos: añadir versión y control de cambios en documentos externos.

## 6. Trade-offs
- Se priorizó rapidez de desarrollo y claridad para la entrega sobre optimizaciones de costo y latencia a gran escala.
