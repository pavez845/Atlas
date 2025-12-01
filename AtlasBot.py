# =================================================================
# Agente Funcional Médico - Hospital Barros Luco (v2 - Observabilidad)
# Archivo: main_rag_agent_v2.py
# =================================================================
import streamlit as st
import os
import json
import time
import uuid
import re  # IL3.3: Para validación de inputs
from datetime import datetime
import pandas as pd
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter, defaultdict
import requests
import concurrent.futures

# IL3.2: Configuración de Logs Estructurados
import logging
import structlog

# Configuración básica de logging
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)
# Configuración para estructurar logs en JSON
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger()

# Cargar variables de entorno (mantener compatibilidad)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Variables de Entorno (adaptadas para OpenAI/Azure o GitHub inference)
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
github_token = os.getenv("GITHUB_TOKEN")
# URL que usas en .env para embeddings / inferencia GitHub
github_inference_url = os.getenv("OPENAI_EMBEDDINGS_URL") or os.getenv("GITHUB_BASE_URL")

st.set_page_config(page_title="🏥 Agente Médico Funcional v2 (Obs)", page_icon="🏥", layout="wide")

# =================================================================
# FUNCIÓN CSS DE TEMA HOSPITALARIO MEJORADA
# =================================================================
def inject_hospital_theme(logo_path: str = None):
        """Inyecta CSS para tema hospitalario oscuro y de alto contraste.

        - Paleta: azules y blanco (texto claro sobre fondo oscuro)
        - Soporta mostrar un `logo_path` en la sidebar si existe
        """
        css = """
        <style>
        :root{
            --color-50:  #F5FAFA;
            --color-100: #EBF5F6;
            --color-200: #E1F0F1;
            --color-300: #D7EBED;
            --color-400: #CCE6E8;
            --color-500: #C2E1E3;
            --color-600: #B8DCDF;
            --color-700: #AED7DA;
            --color-800: #A3D2D6;
            --color-900: #99CDD1;
            --color-950: #8EC8CD;

            --color-mid: var(--color-500);

            --brand-blue:  var(--color-50);
            --brand-blue-2: var(--color-300);
            --card:#ffffff;           /* cards blancos para legibilidad */
            --muted:#6c757d;
            --accent:var(--color-500);
            --text:#012a4a;           /* letras en color oscuro para legibilidad */
            --shadow: rgba(0,0,0,0.06);
        }
        /* Fondo app: gradiente pronunciado usando la escala de colores */
        [data-testid="stAppViewContainer"], .stApp {
            /* Gradiente simétrico: 50 -> 500 -> 50 */
            /* overlay + base gradient: overlay tints to smooth transitions */
            background-image: 
                linear-gradient(rgba(78,169,177,0.12), rgba(78,169,177,0.12)),
                linear-gradient(180deg,
                    var(--color-50) 0%,
                    var(--color-100) 8%,
                    var(--color-200) 18%,
                    var(--color-300) 28%,
                    var(--color-400) 34%,
                    var(--color-500) 36%,
                    var(--color-mid) 35%,
                    var(--color-mid) 65%,
                    var(--color-500) 64%,
                    var(--color-400) 70%,
                    var(--color-300) 78%,
                    var(--color-200) 86%,
                    var(--color-100) 94%,
                    var(--color-50) 100%
                ) !important;
            background-size: cover !important;
            color: var(--text) !important;
            background-attachment: fixed !important;
        }
        /* Sidebar */
        [data-testid="stSidebar"], .sidebar, .css-1d391kg, .css-1v3fvcr {
            background: linear-gradient(180deg, rgba(223,245,244,0.9) 0%, #ffffff 100%) !important;
            color: var(--text) !important;
        }
        /* Botones */
        .stButton>button, button[kind="primary"] {
            background-color: var(--brand-blue-2) !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            box-shadow: 0 4px 8px -2px var(--shadow) !important;
        }
        /* Cards / containers */
        .stCard, [data-testid="stVerticalBlockBorderWrapper"], .css-18e3th9, .element-container {
            background: var(--card) !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.06) !important;
            padding: 12px !important;
            color: var(--text) !important;
            border: 1px solid rgba(0,0,0,0.04) !important;
        }
        /* Métricas */
        [data-testid="stMetricValue"] { color: var(--brand-blue-2) !important; font-size: 2rem !important; }
        /* Títulos y encabezados: usar color oscuro para legibilidad (igual al chat) */
        h1, h2, h3, .css-1v0mbdj h1, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: var(--text) !important;
        }
        /* Subheaders y captions */
        .css-1hq7z6c, .stCaption, .css-1aumxhk { color: var(--text) !important; }
        /* Chat bubbles (mantener legibilidad con fondo Sea Glass) */
        .stChatMessage .message.user { background: rgba(111,153,168,0.12) !important; color: #012a4a !important; border-radius:10px 10px 0 10px; padding:10px; }
        .stChatMessage .message.assistant { background: rgba(255,255,255,0.95) !important; color: #012a4a !important; border-radius:10px 10px 10px 0; padding:10px; box-shadow:0 1px 3px rgba(0,0,0,0.04) !important; }
        /* Expander header */
        .streamlit-expanderHeader { color: var(--brand-blue) !important; font-weight: 700; }
        /* Table/ DataFrame header */
        .stDataFrame div[role="columnheader"] { background: rgba(15,120,140,0.06) !important; color: var(--text) !important; }
        /* Títulos dentro de containers y cards (p. ej. subheaders del dashboard) */
        .element-container h2, .element-container h3, .st-beta-text, .css-1v0mbdj {
            color: var(--text) !important;
        }
        /* Links */
        a { color: var(--brand-blue) !important; }
        /* Small text muted */
        .css-1offfwp, .css-1aw2w0m { color: var(--muted) !important; }
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)

        # Logo opcional en la barra lateral (ignorar silenciosamente si no existe)
        try:
                import os

                if logo_path and os.path.exists(logo_path):
                        st.sidebar.image(logo_path, width=140)
                        st.sidebar.markdown("### Hospital Barros Luco\nAgente Médico Funcional", unsafe_allow_html=True)
        except Exception:
                # no crash on missing os or image
                pass

# =================================================================
# Clase refactorizada con Trazabilidad y Seguridad (IL3.1, IL3.2, IL3.3)
# =================================================================
class ChatbotMedicoRAG:
    """Clase principal del Agente Funcional Médico con RAG."""
    def __init__(self):
        self.client = None
        self.llm_model = "gpt-4o-mini"
        self.embeddings_model = "text-embedding-3-small"
        self.documents = []
        self.embeddings = None
        self.embedding_matrix = None
        self.interaction_logs = []
        self.error_count = 0  # IL3.1: Métrica de frecuencia de errores
        # Persistencia de logs de interacción
        try:
            os.makedirs("data", exist_ok=True)
        except Exception:
            pass
        self.logs_path = os.path.join("data", "logs.json")
        # Cargar logs existentes si están presentes
        try:
            self._load_logs()
        except Exception:
            # No fallar la inicialización si la carga falla
            pass

    def initialize_client(self):
        """Inicializa el cliente OpenAI o habilita modo GitHub inference."""
        try:
            if openai_api_key:
                # Modo OpenAI / Azure (usa SDK)
                self.client = OpenAI(api_key=openai_api_key, base_url=openai_base_url)
                self.github_mode = False
                logger.info("system_init", status="success", message="Cliente OpenAI/Azure inicializado")
                return True
            elif github_token and github_inference_url:
                # Modo GitHub inference: usaremos HTTP requests directos
                self.client = None
                self.github_mode = True
                self.github_token = github_token
                self.github_inference_url = github_inference_url.rstrip("/")
                logger.info("system_init", status="success", message="Modo de inferencia GitHub habilitado")
                return True
            else:
                logger.error("system_init", status="error", message="No hay OPENAI_API_KEY ni GITHUB_TOKEN válidos")
                st.error("Falta OPENAI_API_KEY o GITHUB_TOKEN en .env")
                return False
        except Exception as e:
            logger.error("system_init", status="error", message=f"Error al inicializar cliente: {e}")
            st.error(f"Error inicializando cliente: {e}")
            return False

    def initialize_hospital_documents(self) -> bool:
        """Carga documentos por defecto."""
        try:
            docs = [
                "El Hospital Barros Luco ubicado en Santiago de Chile cuenta con los siguientes servicios: Emergencias 24/7, Cuidados Intensivos (UCI), Cardiología, Neurología, Pediatría, Ginecología y Obstetricia, Oncología, Ortopedia y Traumatología, Radiología e Imágenes, Laboratorio Clínico, Farmacia, y Rehabilitación Física.",
                "Horarios de atención: Emergencias 24 horas. Consultas externas: Lunes a Viernes 7:00 AM - 6:00 PM, Sábados 8:00 AM - 2:00 PM. Teléfono principal: (01) 234-5678. Emergencias: 911. Dirección: Av. Salud 123, Lima, Perú.",
                "Protocolo de emergencias: En caso de emergencia médica, dirigirse inmediatamente al área de Emergencias en el primer piso. El personal de triaje evaluará la urgencia. Código Azul: Paro cardiorrespiratorio. Código Rojo: Emergencia médica. Código Amarillo: Emergencia quirúrgica.",
                "Proceso de hospitalización: 1) Admisión con documento de identidad y seguro médico. 2) Evaluación médica inicial. 3) Asignación de habitación según disponibilidad. 4) Entrega de brazalete de identificación. 5) Orientación sobre normas hospitalarias. Horarios de visita: 2:00 PM - 4:00 PM y 6:00 PM - 8:00 PM.",
                "El uso de IA en radiología ayuda a detectar anomalías en imágenes médicas con mayor precisión. Nuestro Hospital Barros Luco utiliza sistemas de inteligencia artificial para análisis de radiografías, tomografías y resonancias magnéticas, lo que permite diagnósticos más rápidos y exactos.",
                "La telemedicina permite realizar consultas médicas a distancia, mejorando el acceso en zonas rurales. El Hospital Barros Luco ofrece servicios de teleconsulta para seguimiento de pacientes crónicos, consultas de especialidades y orientación médica inicial.",
            ]
            self.documents = docs
            self.embeddings = None
            self.embedding_matrix = None
            logger.info("data_load", status="success", doc_count=len(docs), message="Documentos del hospital cargados")
            return True
        except Exception as e:
            logger.error("data_load", status="error", message=f"Error inicializando documentos: {e}")
            st.warning(f"⚠ Error inicializando documentos: {e}")
            return False

    def _github_post(self, path, payload):
        """POST genérico al endpoint de inferencia GitHub y devuelve JSON o lanza excepción."""
        url = f"{self.github_inference_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_embeddings(self, documents):
        """Genera embeddings usando OpenAI SDK o GitHub inference (según modo)."""
        try:
            if getattr(self, "github_mode", False):
                start_time = time.time()
                payload = {"model": self.embeddings_model, "input": documents}
                resp = self._github_post("embeddings", payload)
                # Adaptación según formato: intentar claves comunes
                embs = [item.get("embedding") or item.get("vector") for item in resp.get("data", [])]
            else:
                if not self.client:
                    return None
                start_time = time.time()
                resp = self.client.embeddings.create(model=self.embeddings_model, input=documents)
                embs = [d.embedding for d in resp.data]
            self.embeddings = embs
            self.embedding_matrix = np.array(embs, dtype=float)
            duration = time.time() - start_time
            logger.info("tool_call", tool="embedding_generation", status="success", duration_sec=duration, doc_count=len(documents))
            return embs
        except Exception as e:
            self.error_count += 1
            logger.error("tool_call", tool="embedding_generation", status="error", error=str(e), doc_count=len(documents))
            st.warning(f"⚠ Error generando embeddings: {e}")
            return None

    def get_query_embedding(self, query):
        try:
            if getattr(self, "github_mode", False):
                payload = {"model": self.embeddings_model, "input": [query]}
                resp = self._github_post("embeddings", payload)
                emb = (resp.get("data") or [{}])[0].get("embedding") or (resp.get("data") or [{}])[0].get("vector")
                return np.array(emb, dtype=float)
            else:
                if not self.client:
                    return None
                resp = self.client.embeddings.create(model=self.embeddings_model, input=[query])
                emb = resp.data[0].embedding
                return np.array(emb, dtype=float)
        except Exception as e:
            self.error_count += 1
            logger.error("tool_call", tool="query_embedding", status="error", error=str(e))
            st.warning(f"⚠ Error obteniendo embedding de la query: {e}")
            return None

    def hybrid_search_with_metrics(self, query, top_k=3):
        """Búsqueda híbrida y registro de tiempo."""
        start = time.time()
        try:
            if not self.documents or self.embedding_matrix is None:
                logger.warning("rag_search", status="skipped", reason="No documents/embeddings available")
                return [], 0.0

            q_emb = self.get_query_embedding(query)
            if q_emb is None:
                return [], 0.0
            sims = cosine_similarity(self.embedding_matrix, q_emb.reshape(1, -1)).reshape(-1)
            q_words = set([w.strip(".,?¡!():;\"'").lower() for w in query.split() if len(w) > 2])
            results = []
            for idx, doc in enumerate(self.documents):
                doc_words = set([w.strip(".,?¡!():;\"'").lower() for w in doc.split() if len(w) > 2])
                lexical = 0.0
                if q_words:
                    lexical = len(q_words.intersection(doc_words)) / max(1, len(q_words))
                semantic = float(sims[idx])
                combined = 0.7 * semantic + 0.3 * lexical
                results.append({
                    'id': idx,
                    'document': doc,
                    'semantic_score': semantic,
                    'lexical_score': lexical,
                    'combined_score': combined
                })
            results = sorted(results, key=lambda x: x['combined_score'], reverse=True)[:top_k]
            retrieval_time = time.time() - start
            logger.info("rag_search", status="success", duration_sec=retrieval_time, top_k=top_k)  # IL3.2: Trazabilidad
            return results, retrieval_time
        except Exception as e:
            self.error_count += 1
            logger.error("rag_search", status="error", error=str(e))
            st.warning(f"⚠ Error en búsqueda híbrida: {e}")
            return [], 0.0

    def generate_response_with_metrics(self, query, context):
        """
        Genera una respuesta con el LLM usando contexto.
        Retorna (response_text, generation_time, used_context_text, tokens_used)
        """
        start = time.time()
        tokens_used = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
        try:
            prompt = f"Contexto:\n{context}\n\nPregunta: {query}\n\nResponda de forma clara y concisa:"
            if getattr(self, "github_mode", False):
                # Llamada simple al endpoint de chat/completions de GitHub (modo inferencia)
                payload = {
                    "model": self.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 600
                }
                resp = self._github_post("chat/completions", payload)
                # Adaptar según respuesta: intento de extracción común
                response_text = (resp.get("choices") or [{}])[0].get("message", {}).get("content") or (resp.get("choices") or [{}])[0].get("text")
                usage = resp.get("usage", {}) or {}
            else:
                chat_resp = self.client.chat.completions.create(  # Llamada SDK OpenAI/Azure
                    model=self.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=600
                )
                response_text = chat_resp.choices[0].message.content
                usage = getattr(chat_resp, "usage", {}) or {}

            if usage:
                tokens_used = {
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0)
                }
            generation_time = time.time() - start
            logger.info("llm_generation", status="success", duration_sec=generation_time, **tokens_used)
            return response_text or "", generation_time, context, tokens_used
        except Exception as e:
            self.error_count += 1
            logger.error("llm_generation", status="error", error=str(e), prompt_length=len(prompt))  # Error generando respuesta LLM
            generation_time = time.time() - start
            return f"Error generando respuesta: {e}", generation_time, context, tokens_used

    # -------------------------
    # IL3.3: Funciones de Seguridad y Ética
    # -------------------------
    def sanitize_input(self, user_input):
        """
        IE6: Saneamiento de input para mitigar Prompt Injection y XSS (aunque es menos relevante aquí).
        Remueve caracteres peligrosos y detecta patrones de inyección.
        """
        # Patrón simple para detectar intento de inyección de prompt
        injection_patterns = r"(\bignora\s+las\s+instrucciones\b|\bactua\s+como\b|\bdesactiva\s+el\s+filtro\b)"

        if re.search(injection_patterns, user_input, re.IGNORECASE):
            logger.warning("security_violation", type="prompt_injection", input=user_input[:50], action="blocked_sanitized")
            # Reemplazar patrones para neutralizar
            user_input = re.sub(injection_patterns, "consulta sobre el hospital", user_input, flags=re.IGNORECASE)

        # Saneamiento general de caracteres potencialmente peligrosos (ej. para XSS o inyección)
        cleaned_input = re.sub(r'[<>{}\[\]\&|;`\$]', '', user_input)

        return cleaned_input

    def ethical_check(self, query):
        """
        IE6: Filtro ético para contenido dañino o fuera de alcance médico.
        """
        prohibited_keywords = ["hackear", "suicidio", "violencia", "terrorismo", "drogas ilegales"]
        for keyword in prohibited_keywords:
            if keyword in query.lower():
                logger.warning("ethical_violation", type="harmful_content", query=query[:50], action="blocked")
                return False, "Lo siento, no puedo ayudar con solicitudes relacionadas con ese tema. Por favor, realiza una consulta sobre los servicios médicos del Hospital Barros Luco."

        # IE6: Advertencia para temas sensibles (Consejo Legal/Financiero/Específico no médico)
        sensitive_keywords = ["inversión", "abogado", "ley", "demanda"]
        for keyword in sensitive_keywords:
            if keyword in query.lower():
                return True, "Consulta sobre el Hospital Barros Luco"  # Permite la consulta pero con un tema neutral

        return True, None

    # -------------------------
    # Lógica central del Agente (ReAct-like)
    # -------------------------
    def run_agent_logic(self, query):
        """
        IE3/IL3.2: Reemplaza AgentExecutor: decide si usar RAG (documentos) o responder directo (LLM).
        """
        # IL3.3: 1. Seguridad y Ética
        cleaned_query = self.sanitize_input(query)
        is_ethical, ethical_message = self.ethical_check(cleaned_query)

        if not is_ethical:
            metrics = {'total_time': 0.0, 'faithfulness': 0.0, 'relevance': 0.0, 'context_precision': 0.0}
            self.log_interaction(query, ethical_message, metrics, [], error_occurred=True)
            return ethical_message, metrics, []

        low = cleaned_query.lower()
        rag_keywords = ["horari", "protocolo", "servicio", "emerg", "urgenc", "hospital", "teléfono", "telefono", "direcci", "ubicac", "consulta", "cita"]
        use_rag = any(k in low for k in rag_keywords)

        context_text = ""
        results = []
        rag_time = 0.0

        # IL3.2: Trazabilidad de Decisión (Simulación ReAct)
        if use_rag and self.embeddings is not None:
            logger.info("agent_decision", action="use_tool", tool="RAG_Tool", reasoning="Keyword match (hospital related)")
            results, rag_time = self.hybrid_search_with_metrics(cleaned_query, top_k=3)
            if results:
                context_text = "\n\n".join([f"Fuente {r['id']+1}: {r['document']}" for r in results])
        else:
            logger.info("agent_decision", action="llm_direct", tool="none", reasoning="General or non-hospital query")

        # Generar respuesta con (posible) contexto
        total_start = time.time()
        response, generation_time, _, tokens_used = self.generate_response_with_metrics(cleaned_query, context_text)
        total_time = (time.time() - total_start) + rag_time

        # IL3.1: Evaluaciones de Calidad (Precisión, Consistencia)
        faith = self.evaluate_faithfulness(cleaned_query, context_text, response)
        rel = self.evaluate_relevance(cleaned_query, response)
        ctx_prec = self.evaluate_context_precision(cleaned_query, results) if results else 0.0

        metrics = {
            'total_time': total_time,
            'faithfulness': faith,
            'relevance': rel,
            'context_precision': ctx_prec,
            'tokens_used': tokens_used,  # IL3.1: Uso de Recursos
            'rag_time': rag_time
        }

        # IE3: Log de interacción final
        self.log_interaction(query, response, metrics, results, error_occurred=False)

        # IE6: Adjuntar advertencia ética (si aplica)
        if ethical_message and is_ethical:
            response = f"**[Advertencia Ética/Legal]** {ethical_message}\n\n---\n\n{response}"

        return response, metrics, results

    # -------------------------
    # IL3.1: Métricas de Calidad
    # -------------------------
    def evaluate_faithfulness(self, query, context_text, response_text):
        # Heurística simple para medir consistencia con el contexto (faithfulness)
        try:
            ctx = context_text.lower()
            sentences = [s.strip() for s in response_text.split('.') if s.strip()]
            if not sentences:
                return 0.0
            overlap = sum(1 for s in sentences if s.lower()[:30] in ctx or 'servicio' in s.lower())
            score = (overlap / len(sentences)) * 10.0
            return float(max(0.0, min(10.0, score)))
        except Exception:
            return 0.0

    def evaluate_relevance(self, query, response_text):
        # Heurística simple para medir relevancia respecto a la consulta
        try:
            q_words = set([w.lower().strip(".,?¡!():;\"'") for w in query.split() if len(w) > 2])
            r_words = set([w.lower().strip(".,?¡!():;\"'") for w in response_text.split() if len(w) > 2])
            if not q_words:
                return 0.0
            overlap = len(q_words.intersection(r_words))
            score = (overlap / len(q_words)) * 10.0
            return float(max(0.0, min(10.0, score)))
        except Exception:
            return 0.0

    def evaluate_context_precision(self, query, results):
        # Mide la precisión del contexto recuperado (proporción de documentos relevantes)
        try:
            q_words = set([w.lower().strip(".,?¡!():;\"'") for w in query.split() if len(w) > 2])
            if not q_words or not results:
                return 0.0
            count = 0
            for r in results:
                content_words = set([w.lower().strip(".,?¡!():;\"'") for w in r['document'].split() if len(w) > 2])
                if q_words.intersection(content_words):
                    count += 1
            return float(count / len(results))
        except Exception:
            return 0.0

    # -------------------------
    # IL3.2: Registro de Interacciones y Logs
    # -------------------------
    def log_interaction(self, query, response, metrics, results, error_occurred):
        """IE3: Registra interacción en self.interaction_logs."""
        try:
            entry = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat(),
                'query': query,
                'response': response,
                'metrics': metrics,
                'error_occurred': error_occurred,
                'context_count': len(results) if results else 0,
                'context_scores': [r.get('combined_score') for r in results] if results else []
            }
            self.interaction_logs.append(entry)
            logger.info("interaction_end", **entry)  # Registro estructurado final (IL3.2)
            # Persist logs to disk for reproducibility (IE6 / IE10)
            try:
                self._save_logs()
            except Exception as e:
                logger.warning("log_persist_failed", error=str(e))
            return True
        except Exception as e:
            logger.error("log_error", error=str(e), message="Fallo al registrar la interacción")
            return False

    def _save_logs(self):
        """Guarda `self.interaction_logs` en `self.logs_path` como JSON."""
        try:
            # Ensure serializable: create a sanitized copy and convert non-serializable types using str()
            sanitized = []
            for e in self.interaction_logs:
                copy_e = dict(e)
                # Mask PII in query/response before persisting
                copy_e['query'] = self._mask_pii(str(copy_e.get('query', '')))
                copy_e['response'] = self._mask_pii(str(copy_e.get('response', '')))
                # Ensure metrics are serializable
                copy_e['metrics'] = copy_e.get('metrics', {})
                sanitized.append(copy_e)
            with open(self.logs_path, "w", encoding="utf-8") as fh:
                json.dump(sanitized, fh, ensure_ascii=False, indent=2, default=str)
            logger.info("logs_saved", path=self.logs_path, count=len(sanitized))
            return True
        except Exception as e:
            logger.error("logs_save_error", error=str(e))
            raise

    def _mask_pii(self, text: str) -> str:
        """Enmascara patrones simples de PII (teléfonos, correos, secuencias largas de dígitos) para evitar guardar datos sensibles."""
        try:
            # Enmascarar correos
            text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]", text)
            # Enmascarar teléfonos (7+ dígitos, con separadores)
            text = re.sub(r"(\+?\d[\d\s\-()]{6,}\d)", "[REDACTED_PHONE]", text)
            # Enmascarar secuencias largas de dígitos
            text = re.sub(r"\b\d{7,}\b", "[REDACTED_NUMBER]", text)
            return text
        except Exception:
            return text

    def _save_messages(self, path=None):
        """Guardar `st.session_state.messages` si existe en `data/messages.json`."""
        try:
            path = path or os.path.join("data", "messages.json")
            msgs = getattr(self, 'session_messages', None)
            if msgs is None and hasattr(self, 'interaction_logs'):
                # fallback: do not attempt to reconstruct messages from logs
                msgs = []
            with open(path, 'w', encoding='utf-8') as fh:
                json.dump(msgs, fh, ensure_ascii=False, indent=2, default=str)
            logger.info("messages_saved", path=path, count=len(msgs))
            return True
        except Exception as e:
            logger.error("messages_save_error", error=str(e))
            return False

    def _load_messages(self, path=None):
        """Cargar mensajes guardados si existen."""
        path = path or os.path.join("data", "messages.json")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    msgs = json.load(fh)
                # store in attribute for later saving
                self.session_messages = msgs
                logger.info("messages_loaded", path=path, count=len(msgs))
                return msgs
            except Exception as e:
                logger.error("messages_load_error", error=str(e))
                return []
        return []

    def add_external_documents(self, documents: list):
        """Añade documentos externos a la base de conocimiento y regenera embeddings.

        documents: lista de strings
        """
        try:
            if not documents:
                return False
            # append documents
            self.documents.extend(documents)
            # regenerate embeddings for all documents (simple approach)
            embs = self.get_embeddings(self.documents)
            if embs is not None:
                self.embeddings = embs
                self.embedding_matrix = self.embedding_matrix if self.embedding_matrix is not None else np.array(embs, dtype=float)
                # if get_embeddings recomputed embedding_matrix, it already updated
            # persist external docs
            try:
                ext_path = os.path.join('data', 'external_docs.json')
                with open(ext_path, 'w', encoding='utf-8') as fh:
                    json.dump({'documents': documents, 'added_at': datetime.utcnow().isoformat()}, fh, ensure_ascii=False, indent=2)
            except Exception:
                pass
            logger.info("external_docs_added", count=len(documents))
            return True
        except Exception as e:
            logger.error("external_docs_error", error=str(e))
            return False

    def _load_logs(self):
        """Carga logs desde `self.logs_path` si existe."""
        if os.path.exists(self.logs_path):
            try:
                with open(self.logs_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    self.interaction_logs = data
                    logger.info("logs_loaded", path=self.logs_path, count=len(self.interaction_logs))
                    return True
            except Exception as e:
                logger.error("logs_load_error", error=str(e))
                raise
        return False

    def clean_placeholder_documents(self) -> bool:
        # ... (código de limpieza de documentos)
        try:
            if not self.documents:
                return True
            cleaned = []
            removed = 0
            for doc in self.documents:
                if not doc or 'placeholder' in doc.lower() or 'test' in doc.lower() or len(doc.strip()) < 10:
                    removed += 1
                    continue
                cleaned.append(doc)
            if removed:
                self.documents = cleaned
                self.embeddings = None
                self.embedding_matrix = None
                logger.info("data_cleaning", removed_count=removed, message="Placeholders cleaned")
            return True
        except Exception as e:
            logger.error("data_cleaning", error=str(e), message="Error cleaning placeholder documents")
            return False

class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.user_requests = defaultdict(list)

    def is_allowed(self, user_id):
        now = time.time()
        window_start = now - 60
        reqs = [t for t in self.user_requests[user_id] if t > window_start]
        self.user_requests[user_id] = reqs
        if len(reqs) >= self.requests_per_minute:
            return False
        self.user_requests[user_id].append(now)
        return True

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def async_get_embeddings(chatbot, documents):
    """Ejecutar get_embeddings en background para no bloquear Streamlit."""
    future = _executor.submit(chatbot.get_embeddings, documents)
    return future  # future.result() cuando necesites bloquear

# =================================================================
# Streamlit UI (IE5: Dashboard) - CÓDIGO ACTUALIZADO
# =================================================================
def main():
    # inyectar tema al inicio de la app
    inject_hospital_theme(logo_path="assets/hospital_logo.png")

    if "chatbot_rag" not in st.session_state:
        chatbot = ChatbotMedicoRAG()
        st.session_state.chatbot_rag = chatbot

        if not chatbot.initialize_client():
            return

        chatbot.initialize_hospital_documents()
        try:
            embs = chatbot.get_embeddings(chatbot.documents)
            if embs is not None:
                st.session_state.chatbot_rag.embeddings = embs
                st.session_state.chatbot_rag.embedding_matrix = chatbot.embedding_matrix
                st.success("✅ Embeddings generados automáticamente para los documentos cargados")
            else:
                st.info("ℹ️ Embeddings no generados automáticamente.")
        except Exception:
            pass

        if "messages" not in st.session_state:
            st.session_state.messages = []
        # try load persisted messages
        try:
            loaded_msgs = chatbot._load_messages()
            if loaded_msgs:
                st.session_state.messages = loaded_msgs
        except Exception:
            pass

    tabs = st.tabs(["💬 Chat", "📄 Documentos", "📊 Métricas y Dashboard"])
    tab1, tab2, tab3 = tabs

    # =================================================================
    # TAB 1: CHAT (con Trazabilidad Mejorada)
    # =================================================================
    with tab1:
        st.subheader("💬 Agente Funcional Médico (HBL)")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("🏥 Pregúntame sobre horarios, servicios médicos, procedimientos..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Agente de IA procesando..."):
                    chatbot = st.session_state.chatbot_rag
                    try:
                        response, metrics, results = chatbot.run_agent_logic(prompt)
                    except Exception as e:
                        response = f"Error interno ejecutando lógica del agente: {e}"
                        metrics = {}
                        results = []
                        st.session_state.chatbot_rag.error_count += 1
                        logger.error("runtime_error", error=str(e), query=prompt[:50])

                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    # --- AÑADIR TRAZABILIDAD MEJORADA ---
                    if metrics:
                        with st.expander("🔎 Trazabilidad y Métricas de la Respuesta"):
                            st.markdown(f"**Latencia Total:** `{metrics.get('total_time', 0.0):.3f}s` (RAG: `{metrics.get('rag_time', 0.0):.3f}s`)")
                            st.markdown(f"**Tokens Usados:** `{metrics.get('tokens_used', {}).get('total_tokens', 0)}`")
                            st.markdown(f"**Faithfulness (0-10):** `{metrics.get('faithfulness', 0.0):.1f}`")
                            st.markdown(f"**Relevance (0-10):** `{metrics.get('relevance', 0.0):.1f}`")

                            if results:
                                st.subheader("Documentos Fuente (Contexto RAG):")
                                for r in results:
                                    score_color = "#28a745" if r['combined_score'] > 0.5 else "#ffc107"
                                    st.markdown(f"""
                                    <div style='background-color:#f8f9fa; padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid {score_color};'>
                                        **Score:** <span style='color:{score_color}'>{r['combined_score']:.2f}</span><br>
                                        **Contenido:** <span style='color:var(--muted); font-size:0.9em;'>{r['document']}</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("No se utilizó RAG (respuesta directa del LLM).")
                    # -----------------------------------

    # =================================================================
    # TAB 2: DOCUMENTOS (Sin cambios funcionales, sólo UI)
    # =================================================================
    with tab2:
        st.header("📄 Gestión de Documentos y Embeddings")
        st.info("Aquí puedes ver y gestionar los documentos de conocimiento del Hospital Barros Luco. Estos documentos son la base para el componente RAG.")

        st.subheader("Documentos Cargados")
        doc_df = pd.DataFrame({'ID': range(len(st.session_state.chatbot_rag.documents)), 'Contenido': st.session_state.chatbot_rag.documents})
        st.dataframe(doc_df, use_container_width=True)

        st.subheader("Estado del Embedding")
        if st.session_state.chatbot_rag.embeddings is not None:
            st.success(f"Embeddings generados para {len(st.session_state.chatbot_rag.documents)} documentos usando `{st.session_state.chatbot_rag.embeddings_model}`.")
        else:
            st.warning("Embeddings no generados o fallidos.")

        if st.button("🔄 Regenerar Embeddings"):
            with st.spinner("Generando Embeddings..."):
                st.session_state.chatbot_rag.get_embeddings(st.session_state.chatbot_rag.documents)
            try:
                st.experimental_rerun()
            except Exception:
                st.success("Embeddings generados. Recarga la página manualmente si es necesario.")
                st.stop()
        st.markdown("---")
        st.subheader("📥 Añadir documentos externos (CSV/TXT)")
        uploaded_file = st.file_uploader("Sube un CSV (columna 'content' o 'text') o un .txt", type=["csv", "txt"], accept_multiple_files=False)
        if uploaded_file is not None:
            try:
                docs_to_add = []
                if uploaded_file.name.lower().endswith('.csv'):
                    df_up = pd.read_csv(uploaded_file)
                    # try common column names
                    if 'content' in df_up.columns:
                        docs_to_add = df_up['content'].dropna().astype(str).tolist()
                    elif 'text' in df_up.columns:
                        docs_to_add = df_up['text'].dropna().astype(str).tolist()
                    else:
                        # take first text-like column
                        first_col = df_up.columns[0]
                        docs_to_add = df_up[first_col].dropna().astype(str).tolist()
                else:
                    raw = uploaded_file.getvalue().decode('utf-8')
                    # split by double-newline or by lines
                    parts = [p.strip() for p in raw.split('\n\n') if p.strip()]
                    if parts:
                        docs_to_add = parts
                    else:
                        docs_to_add = [raw]

                if docs_to_add:
                    st.write(f"Documentos detectados: {len(docs_to_add)}")
                    if st.button("➕ Agregar a la base de conocimiento"):
                        added = st.session_state.chatbot_rag.add_external_documents(docs_to_add)
                        if added:
                            st.success(f"{len(docs_to_add)} documentos agregados y embeddings regenerados (si procede).")
                            try:
                                st.experimental_rerun()
                            except Exception:
                                st.info("Recarga manual necesaria para ver cambios.")
                        else:
                            st.error("No se pudieron agregar los documentos.")
                else:
                    st.error("No se encontraron documentos procesables en el archivo.")
            except Exception as e:
                st.error(f"Error procesando archivo: {e}")

    # =================================================================
    # TAB 3: DASHBOARD (Rediseñado para Observabilidad)
    # =================================================================
    with tab3:
        st.header("📊 Dashboard de Observabilidad del Agente")
        logs = st.session_state.chatbot_rag.interaction_logs or []

        if not logs:
            st.info("No hay interacciones registradas aún. ¡Empieza a chatear!")
        else:
            df = pd.DataFrame(logs)
            df['Fecha'] = pd.to_datetime(df['timestamp'])

            # --- 1. INDICADORES DE RENDIMIENTO (IE2) ---
            st.subheader("1. Rendimiento y Uso de Recursos (IE2)")
            col_perf_1, col_perf_2, col_perf_3 = st.columns(3)

            # Cálculos
            avg_latency = df['metrics'].apply(lambda x: x.get('total_time', 0.0)).mean()
            error_rate = df['error_occurred'].sum() / len(df)
            total_tokens = df['metrics'].apply(lambda x: x.get('tokens_used', {}).get('total_tokens', 0)).sum()

            with col_perf_1:
                st.metric("Total de Consultas", len(df))
            with col_perf_2:
                st.metric("Latencia Media Total (s)", f"{avg_latency:.2f}s", delta=f"{avg_latency*1000:.0f} ms")
            with col_perf_3:
                st.metric("Total Tokens LLM Usados", f"{total_tokens:,}")

            # Gráficos de Desglose
            col_chart_1, col_chart_2 = st.columns(2)

            with col_chart_1:
                st.caption("Desglose de Latencia (Media)")
                latencies = df['metrics'].apply(lambda x: pd.Series({
                    'RAG Time': x.get('rag_time', 0.0),
                    'LLM Gen Time': x.get('total_time', 0.0) - x.get('rag_time', 0.0)
                })).clip(lower=0)

                fig_comp = px.bar(
                    latencies.mean().reset_index().rename(columns={'index': 'Componente', 0: 'Tiempo Promedio (s)'}),
                    x='Componente', y='Tiempo Promedio (s)',
                    title='Latencia Media por Componente',
                    color='Componente',
                    color_discrete_map={'RAG Time': '#0d6efd', 'LLM Gen Time': '#0b5ed7'}
                )
                st.plotly_chart(fig_comp, use_container_width=True)

            with col_chart_2:
                df['Decisión Agente'] = df['context_count'].apply(lambda x: 'Usó RAG' if x > 0 else 'LLM Directo')
                decision_counts = df['Decisión Agente'].value_counts().reset_index(name='Count')
                fig_decision = px.pie(
                    decision_counts, values='Count', names='Decisión Agente',
                    title='Uso de la Herramienta RAG (Decisión del Agente)',
                    color_discrete_sequence=['#0d6efd', '#6c757d']
                )
                fig_decision.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_decision, use_container_width=True)

            st.markdown("---")

            # --- 2. CALIDAD Y ESTABILIDAD (IE1) ---
            st.subheader("2. Calidad y Estabilidad (IE1)")
            col_qual_1, col_qual_2 = st.columns(2)

            with col_qual_1:
                st.metric("Tasa de Error Global", f"{error_rate:.1%}", delta_color="inverse")
                error_counts = df['error_occurred'].value_counts().rename({True: 'Error', False: 'Éxito'})
                if not error_counts.empty:
                    fig_error = go.Figure(data=[go.Pie(
                        labels=error_counts.index,
                        values=error_counts.values,
                        hole=.3,
                        marker={'colors': ['#0d6efd' if l == 'Éxito' else '#dc3545' for l in error_counts.index]}
                    )])
                    fig_error.update_layout(title_text="Proporción de Éxito/Error")
                    st.plotly_chart(fig_error, use_container_width=True)
                else:
                    st.info("No hay suficiente información de errores.")

            with col_qual_2:
                st.caption("Promedios de Métricas de Calidad (0-10)")
                quality_metrics = df['metrics'].apply(lambda x: pd.Series({
                    'Faithfulness': x.get('faithfulness', 0.0),
                    'Relevance': x.get('relevance', 0.0),
                    'Context Precision': x.get('context_precision', 0.0) * 10.0
                })).apply(pd.Series)

                avg_quality = quality_metrics.mean().reset_index().rename(columns={'index': 'Métrica', 0: 'Puntaje Promedio'})

                fig_quality = px.bar(avg_quality, x='Métrica', y='Puntaje Promedio',
                                     title='Puntajes Promedio de Calidad', color='Métrica',
                                     range_y=[0, 10],
                                     color_discrete_map={'Faithfulness': '#198754', 'Relevance': '#ffc107', 'Context Precision': '#0d6efd'})
                st.plotly_chart(fig_quality, use_container_width=True)

            st.markdown("---")

            # --- 3. TRAZABILIDAD Y LOGS CRUDOS (IE3) ---
            st.subheader("3. Logs de Interacción y Trazabilidad (IE3)")
            st.info("Los logs estructurados completos (JSON) están en la terminal para un análisis detallado de cada paso.")

            st.download_button(
                label="Descargar Logs de Interacción (CSV)",
                data=df.to_csv().encode('utf-8'),
                file_name=f'logs_interacciones_hbl_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
                mime='text/csv',
            )
            # Guardar / Cargar logs (JSON) - persistencia local
            col_save, col_load = st.columns([1, 2])
            with col_save:
                if st.button("💾 Guardar logs en data/logs.json"):
                    try:
                        saved = st.session_state.chatbot_rag._save_logs()
                        if saved:
                            st.success(f"Logs guardados en {st.session_state.chatbot_rag.logs_path}")
                    except Exception as e:
                        st.error(f"Error guardando logs: {e}")
            with col_load:
                uploaded = st.file_uploader("📂 Cargar logs (archivo JSON)", type=["json"])
                if uploaded is not None:
                    try:
                        loaded = json.load(uploaded)
                        if isinstance(loaded, list):
                            st.session_state.chatbot_rag.interaction_logs = loaded
                            # also persist loaded logs to disk
                            try:
                                st.session_state.chatbot_rag._save_logs()
                            except Exception:
                                pass
                            st.success("Logs cargados en la sesión y guardados localmente.")
                            try:
                                st.experimental_rerun()
                            except Exception:
                                st.info("Recarga manual necesaria para ver los cambios.")
                        else:
                            st.error("Formato inesperado: se esperaba una lista JSON de logs.")
                    except Exception as e:
                        st.error(f"Error procesando archivo: {e}")
            # Mostrar las columnas más relevantes
            # Asegurar columnas existentes antes de mostrar (evita KeyError cuando la clave fue registrada en inglés)
            if 'error_ocurrred' in df.columns:
                # typo guard: unlikely but handle
                df['error_ocurrido'] = df['error_ocurrred']
            if 'error_occurred' in df.columns and 'error_ocurrido' not in df.columns:
                df['error_ocurrido'] = df['error_occurred']
            if 'error_ocurrido' not in df.columns:
                # crear columna por compatibilidad (valor False si no existe)
                df['error_ocurrido'] = False

            subset_cols = [c for c in ['Fecha', 'query', 'Decisión Agente', 'error_ocurrido', 'metrics'] if c in df.columns]
            display_df = df[subset_cols].rename(columns={'query': 'Consulta', 'error_ocurrido': 'Error'})
            st.dataframe(display_df, height=300, use_container_width=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error("app_crash", error=str(e), traceback=tb)
        try:
            st.set_page_config(page_title="Error - Agente Médico", layout="wide")
            st.title("❌ Error al iniciar la aplicación")
            st.error("Ha ocurrido una excepción no manejada. Revisa la terminal (logs JSON) para más detalles.")
            st.subheader("Traceback (resumen)")
            st.code(tb)
        except Exception:
            pass