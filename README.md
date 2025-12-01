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
Inicia la aplicación Streamlit (archivo principal actual: `main_rag_agent_ev3.py`):

```powershell
streamlit run main_rag_agent_ev3.py
```

Uso de variables de entorno
--------------------------
Antes de ejecutar, crea un fichero `.env` (o exporta variables) con `OPENAI_API_KEY` o `GITHUB_TOKEN` según el proveedor que vayas a usar. Hay una plantilla en `.env.example`.

Evidencias y entregables
-------------------------
- `main_rag_agent_ev3.py`: código de la aplicación y del agente.
- `EFT_compliance_checklist.md`: checklist mapeando la rúbrica a evidencias en el repo.
- `EFT_submission_notebook.ipynb`: notebook guía para la entrega.
- `Documentacion/`: documentos de diseño, seguridad y decisiones arquitectónicas.

Contacto
-------
Autores: Catalina Aguilar y Fernando Pavez

Licencia / Avisos
-----------------
Este repositorio es una entrega académica. No incluya datos personales sensibles en `data/` al preparar la entrega. Para uso en producción, sustituir archivos `.env` por un gestor de secretos y aplicar cifrado/retención de registros.