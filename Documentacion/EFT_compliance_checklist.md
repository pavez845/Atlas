# EFT ISY0101 - Compliance Checklist

Este documento mapea cada indicador de la rúbrica a evidencias existentes en el repositorio y acciones recomendadas para cumplir al 100%.

## Resumen rápido
- Proyecto: `Agente Funcional Médico - Hospital Barros Luco` (`main_rag_agent_ev3.py`)
- Autor/es: Catalina Aguilar y Fernando Pavez
- Estado general: funcional (Streamlit), RAG básico con documentos internos, métricas y logs estructurados.

## Checklist por indicador

- IE1 (Prompts) — Peso: 2% (Encargo) / 10% (Defensa)
  - Evidencia existente: el agente construye prompts dinámicos dentro de `generate_response_with_metrics` (cadena `prompt = f"Contexto:\n{context}...`).
  - Estado: Parcial
  - Acción recomendada: Añadir un archivo `prompts_examples.md` con templates de prompts, variantes (nivel de detalle, instrucciones de formato), ejemplos de evaluación A/B y justificación técnica.

- IE2 (RAG: internas + externas) — Peso: 2%
  - Evidencia existente: `initialize_hospital_documents`, `get_embeddings`, `hybrid_search_with_metrics` (RAG con fuentes internas). No hay integración con fuentes externas (APIs, web scraping, bases de datos externas).
  - Estado: Parcial
  - Acción recomendada: Documentar cómo añadir una fuente externa (p. ej. Google Drive, CSV, API hospitalaria) y, si hay tiempo, añadir una integración opcional (ej.: carga de CSV en `/data` o llamada a API mock).

- IE3 (Arquitectura LLM + Retrieval + Control de contexto) — Peso: 2%
  - Evidencia existente: `ChatbotMedicoRAG` integra LLM calls, embeddings y control de contexto (context_text). Diagramas faltan.
  - Estado: OK (funcional)
  - Acción recomendada: Añadir diagrama arquitectónico (PNG o mermaid) en `docs/architecture.png` y explicación en el informe.

- IE4 (Justificación de decisiones) — Peso: 1% (Encargo) / 10% (Defensa)
  - Evidencia existente: README menciona objetivos y métricas, pero falta justificación técnica profunda (por qué modelos, trade-offs, seguridad).
  - Estado: Parcial

- IE5 (Agentes funcionales con herramientas) — Peso: 2% (Encargo) / 10% (Defensa)
  - Evidencia existente: Implementación del agente, UI Streamlit, interacción chat, regeneración de embeddings.
  - Estado: OK


- IE6 (Memoria y recuperación de contexto) — Peso: 2% (Encargo) / 5% (Defensa)
  - Evidencia existente: No hay mecanismo persistente de memoria (solo embeddings temporales en sesión). `interaction_logs` se guarda en memoria durante la sesión pero no persiste.
  - Estado: OK
  - Se añadio Logs.json
- IE7 (Planificación y toma de decisiones) — Peso: 2% (Encargo) / 10% (Defensa)
  - Evidencia existente: Lógica básica ReAct-like (decisión `use_rag` basada en keywords) y `hybrid_search_with_metrics`.
  - Estado: OK
- IE8 (Documentación de orquestación y flujo) — Peso: 1% (Encargo) / 5% (Defensa)
  - Evidencia existente: README y comentarios en el código; falta diagrama, explicación detallada de orquestación.
  - Estado: OK

- IE9 (Métricas observabilidad: precisión, latencia, consistencia) — Peso: 1% (Encargo) / 5% (Defensa)
  - Evidencia existente: Cálculo de `total_time`, `rag_time`, `faithfulness`, `relevance`, `tokens_used` y dashboard en Streamlit.
  - Estado: OK


- IE10 (Análisis de registros) — Peso: 2% (Encargo) / 2% (Defensa)
  - Evidencia existente: `structlog` para logs JSON y dashboard que descarga logs CSV.
  - Estado: OK
- IE11 (Protocolos de seguridad y uso responsable) — Peso: 2% (Encargo) / 5% (Defensa)
  - Evidencia existente: `sanitize_input`, `ethical_check` y advertencias en README sobre uso de IA.
  - Estado: OK
- IE12 (Propuestas de mejora) — Peso: 1% (Encargo) / 5% (Defensa)
  - Evidencia existente: README menciona mejoras generales.
  - Estado: OK

- IE13-IE15 (Defensa: fundamentación, lenguaje técnico, respuestas) — Peso: 25% total en Defensa
  - Evidencia existente: Código y README que muestran diseño y métricas.
  - Estado: ok 


## Acciones inmediatas que puedo ejecutar ahora
1. Crear `EFT_compliance_checklist.md` (hecho).
2. Añadir `.env.template` con variables necesarias.
3. Crear `EFT_submission_notebook.ipynb` con plantilla para Colab que incluya: instrucciones de ejecución, resumen del proyecto, celdas para generar embeddings y visualizar métricas.
4. Crear `logs_analysis.ipynb` (opcional siguiente paso).

## Prioridad (qué entregar primero)
1. `Informe PDF` + `Colab/Notebook` (requerido por la entrega).
2. Diapositivas y notas de defensa por cada integrante.
3. Persistencia de memoria (guardar logs/interacciones) para reforzar IE6.
4. Diagramas arquitectónicos y documentación técnica para IE3, IE4, IE8.

---

Si quieres, puedo:
- Generar ahora el `.env.template` y el notebook plantilla (Colab) con celdas iniciales.
- Empezar a implementar la persistencia de `interaction_logs` (guardar en `data/logs.json`) y añadir un botón en el dashboard para exportar/importar logs.

Dime qué prefieres que haga primero: generar los materiales para entrega (notebook + PDF scaffolding + .env.template) o implementar mejoras técnicas (memoria persistente y análisis de logs).