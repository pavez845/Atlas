# ChatbotEV3
Evaluación 3 — Catalina Aguilar y Fernando Pavez

🏥 Agente Funcional Médico — Hospital Barros Luco (v2: Observabilidad)

Descripción
-----------
Este repositorio contiene la implementación del Agente Funcional Médico enfocado en observabilidad, trazabilidad de decisiones y controles básicos de seguridad. La aplicación principal es una interfaz Streamlit con un pipeline RAG (retrieval-augmented generation), registro estructurado de interacciones y un dashboard de métricas.

Características principales
- Agente RAG con documentos hospitalarios por defecto.
- Generación de embeddings y búsqueda híbrida (semántica + léxica).
- Controles de seguridad: saneamiento de entradas y filtro ético.
- Persistencia básica de logs en `data/logs.json` (con enmascaramiento de PII).
- Dashboard de observabilidad (latencia, tokens usados, tasas de error, calidad de respuestas).

Requisitos
----------
- Python 3.10 o superior (recomendado 3.12).
- Acceso a Internet para llamadas a la API de inferencia.
- Una clave de inferencia: `OPENAI_API_KEY` (OpenAI/Azure) o `GITHUB_TOKEN` (GitHub Models).

Instalación rápida
------------------
1. Clona el repositorio:

```powershell
git clone https://github.com/pavez845/Atlas
cd Chatbot_Ev3
```

2. Crea y activa un entorno virtual (Windows PowerShell):

```powershell
python -m venv entorno
.\entorno\Scripts\Activate.ps1
```

3. Instala dependencias:

```powershell
pip install -r requirements.txt
```

Ejecución
---------
Inicia la aplicación Streamlit (archivo principal: `AtlasBot.py`):

```powershell
streamlit run AtlasBot.py
```

Uso de variables de entorno
--------------------------
Antes de ejecutar, crea un fichero `.env` (o exporta variables) con `OPENAI_API_KEY` o `GITHUB_TOKEN` según el proveedor que vayas a usar. Hay una plantilla en `.env.example`.

Estructura del código (AtlasBot.py)
------------------------------------
El archivo `AtlasBot.py` está organizado en **8 secciones principales** para facilitar la defensa y navegación durante la evaluación:

**1. IMPORTS Y CONFIGURACIÓN**
   - Librerías estándar y terceros (Streamlit, OpenAI, Plotly, etc.)
   - Carga de variables de entorno (`.env`)

**2. LOGGING ESTRUCTURADO (IL3.2)**
   - Configuración de `structlog` para logs JSON
   - Logger global para trazabilidad de eventos

**3. TEMA UI / ESTÉTICA (IE5)**
   - Función `inject_hospital_theme()` con paleta "Sea Glass"
   - CSS personalizado para mejorar accesibilidad y branding

**4. CLASE PRINCIPAL: ChatbotMedicoRAG**
   La clase核心del agente, subdividida internamente en:
   
   - **4.1 Inicialización y Cliente**: Configuración de OpenAI/GitHub inference
   - **4.2 Documentos Base**: Carga de conocimiento hospitalario por defecto
   - **4.3 Embeddings y Recuperación**: Generación de vectores y búsqueda híbrida (semántica + léxica)
   - **4.4 Generación de Respuesta LLM**: Llamadas al modelo con métricas de tokens (IL3.1)
   - **4.5 Seguridad y Ética (IL3.3 / IE6)**: Sanitización de inputs, filtro ético, detección de inyección de prompts
   - **4.6 Lógica Central (Decisión RAG/Directo)**: Heurística de routing y orquestación de herramientas
   - **4.7 Métricas de Calidad (IL3.1)**: Cálculo de faithfulness, relevance, context precision
   - **4.7 (continuación) Persistencia y Logs (IE3/IE10)**: Guardado de interacciones con enmascaramiento de PII, **carga automática de logs al iniciar** (IE6)
   - **4.8 Extensión / Documentos Externos (IE2)**: Función para añadir docs dinámicamente desde **fuentes externas** (CSV, TXT, JSON)

**5. RATE LIMITER**
   - Control básico de frecuencia por usuario (anti-abuso)

**6. UTILIDAD ASÍNCRONA**
   - ThreadPoolExecutor para generación de embeddings en segundo plano

**7. INTERFAZ STREAMLIT**
   - **Tab 1 (Chat)**: Interfaz conversacional con trazabilidad expandible por respuesta
   - **Tab 2 (Documentos)**: Gestión de base de conocimiento y **carga de archivos externos** (CSV/TXT como fuentes externas - IE2)
   - **Tab 3 (Dashboard)**: Observabilidad (rendimiento, calidad, logs, gráficos Plotly)

**8. BLOQUE PRINCIPAL**
   - Manejo de errores global y registro de crashes

---

### Integración de Fuentes Externas (IE2)

El sistema integra **fuentes de datos internas y externas**:

**Fuentes Internas** (precargadas automáticamente):
- 10 documentos base del Hospital Barros Luco (horarios, departamentos, procedimientos administrativos)
- Ubicación: Embebidos en `initialize_hospital_documents()` (líneas 160-250 de `AtlasBot.py`)

**Fuentes Externas** (carga dinámica):
- **CSV**: Columnas `content`, `text`, o `documento` → procesadas automáticamente
- **TXT**: Texto plano → dividido por párrafos o líneas
- **JSON**: Formato `data/external_docs.json` → lista de documentos
- **Interfaz**: Tab "Documentos" → File uploader → Botón "Agregar a la base de conocimiento"
- **Proceso**: 
  1. Usuario sube archivo → parsing automático
  2. Sistema genera embeddings para nuevos documentos
  3. Matriz de embeddings se regenera (búsqueda híbrida actualizada)
  4. Documentos persisten en `data/external_docs.json`

**Ejemplo de uso** (demostrable en defensa):
```python
# Usuario sube protocolos_covid.csv con columna 'content'
# Sistema detecta 15 protocolos nuevos
# Click en "Agregar a la base de conocimiento"
# Embeddings regenerados (ahora 25 documentos totales: 10 internos + 15 externos)
# Consulta: "¿Cuál es el protocolo COVID actual?" → Responde con info del CSV
```

**Evidencia en código**:
- Función `add_external_documents()` (líneas 635-660)
- File uploader en Tab 2 (líneas 780-820)
- Persistencia en `data/external_docs.json`

**Limitación actual**: No hay integración con APIs en tiempo real (ej: sistema FHIR hospitalario). Ver `Documentacion/Mejoras.md` Sección 3.1 para roadmap de integración API externa.

---

### Guía para la defensa
- **Observabilidad (IL3.2)**: Ver sección 2 (structlog) y 4.7 (logs de interacción).
- **Seguridad (IL3.3 / IE6)**: Ver sección 4.5 (sanitize_input, ethical_check, _mask_pii).
- **Métricas de Calidad (IL3.1)**: Ver sección 4.7 (evaluate_faithfulness, evaluate_relevance, evaluate_context_precision).
- **RAG Pipeline**: Ver secciones 4.2, 4.3, 4.4 (documentos → embeddings → búsqueda → generación).
- **Dashboard (IE5)**: Ver sección 7, Tab 3 (gráficos de latencia, tokens, tasas de error, calidad).

Evidencias y entregables
-------------------------
- `AtlasBot.py`: código principal del agente (organizado por secciones para defensa).
- `main_rag_agent_ev3.py`: versión anterior del entrypoint (mantenida por compatibilidad).
- `EFT_compliance_checklist.md`: checklist mapeando la rúbrica a evidencias en el repo.
- `EFT_submission_notebook.ipynb`: notebook guía para la entrega.
- `Documentacion/`: documentos de diseño, seguridad y decisiones arquitectónicas.
- `Logs/`: ejemplos de logs generados, métricas agregadas (CSV), README de seguridad.

Contacto
-------
Autores: Catalina Aguilar y Fernando Pavez

Licencia / Avisos
-----------------
Este repositorio es una entrega académica. No incluya datos personales sensibles en `data/` al preparar la entrega. Para uso en producción, sustituir archivos `.env` por un gestor de secretos y aplicar cifrado/retención de registros.