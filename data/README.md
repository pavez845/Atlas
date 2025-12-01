# data/

Carpeta de datos en tiempo de ejecución generados por la aplicación. No se recomienda incluir estos archivos en el control de versiones (añadir `data/` a `.gitignore` si procede).

Contenido principal
- `logs.json`: volcado persistente de `interaction_logs` generado por el agente. Cada entrada es un objeto JSON con los campos:
  - `id`, `timestamp`, `query`, `response`, `metrics`, `error_occurred`, `context_count`, `context_scores`.

Uso
- El dashboard de Streamlit incluye un botón para guardar los logs actuales en `data/logs.json` y un cargador para restaurar un archivo JSON en la sesión.
- Para incluir logs en la entrega, exporta desde el dashboard como CSV o adjunta `data/logs.json` (siempre redacted o sintético).

Recomendaciones de seguridad
- No subir `data/logs.json` que contenga datos reales de pacientes. Antes de compartir, asegúrate de que el contenido está anonimizado o sintetizado.
