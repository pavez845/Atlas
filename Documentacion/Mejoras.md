# Propuestas de Mejora y Rediseño del Agente

Este documento propone mejoras basadas en análisis de datos observados en el dashboard de observabilidad (IE12 - Rúbrica EFT).

## 1. Análisis de Métricas Actuales (Datos Observados)

### 1.1 Rendimiento y Latencia (IE2 - Dashboard)
**Métricas observadas** (promedio de 6 interacciones de prueba):
- **Latencia total media**: 3.42s (3422 ms)
- **Tiempo RAG**: ~0.8s (generación embeddings + búsqueda)
- **Tiempo LLM**: ~2.6s (inferencia GPT-4o-mini)
- **Total tokens usados**: 983 tokens (promedio 164 tokens/consulta)

**Problemas identificados**:
1. ❌ Latencia >3s excede umbral recomendado de 2s para aplicaciones interactivas
2. ❌ 76% del tiempo se consume en llamada LLM (cuello de botella)
3. ⚠️ Búsqueda híbrida (semántica + léxica) añade 200ms vs búsqueda simple

### 1.2 Uso de Herramienta RAG (Decisión del Agente)
**Métricas observadas**:
- **100% de consultas usaron RAG** en pruebas con preguntas hospitalarias
- **0% LLM directo** (indica que la heurística de detección funciona correctamente)

**Observación positiva**: La estrategia de routing (detección de keywords médicas) es efectiva.

**Oportunidad de mejora**: Añadir telemetría para casos edge donde LLM directo sería más rápido (ej: "Hola", "Gracias").

### 1.3 Calidad de Respuestas (Métricas de Evaluación)
**Métricas observadas** (promedio):
- **Faithfulness**: 7.2/10 (adherencia al contexto RAG)
- **Relevance**: 8.1/10 (pertinencia de la respuesta)
- **Context Precision**: 0.67 (67% de documentos recuperados fueron útiles)

**Problemas identificados**:
1. ⚠️ Faithfulness <8 indica que el LLM ocasionalmente "inventa" información no presente en documentos
2. ❌ Context Precision 67% significa que 1 de cada 3 documentos recuperados es irrelevante (desperdicia tokens)

### 1.4 Estabilidad y Errores
**Métricas observadas**:
- **Tasa de error global**: 0% en pruebas controladas
- **Sin fallos críticos** registrados

**Riesgo identificado**: No hay manejo de errores para:
- Timeout de API (>30s sin respuesta)
- Rate limiting de OpenAI (429 Too Many Requests)
- Fallo en generación de embeddings

---

## 2. Propuestas de Mejora Priorizadas

### 🔴 **Prioridad 1: Crítico** (Impacto Alto + Esfuerzo Bajo)

#### Mejora 1.1: Caché de Embeddings
**Problema que resuelve**: Latencia de 800ms en generación de embeddings por consulta repetida.

**Solución propuesta**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_query_embedding(query: str) -> np.ndarray:
    # Cachea embeddings de consultas frecuentes
    return client.embeddings.create(input=query, model="text-embedding-3-small")
```

**Impacto esperado**:
- ✅ Reducción de latencia: 3.42s → **2.6s** (24% mejora)
- ✅ Ahorro de costos: ~40% menos llamadas a API de embeddings
- ✅ Esfuerzo: **2 horas** de implementación

**Métrica de éxito**: Latencia media <2.8s en dashboard (medible en Tab 3).

---

#### Mejora 1.2: Streaming de Respuestas LLM
**Problema que resuelve**: Usuario espera 2.6s sin feedback visual (mala UX).

**Solución propuesta**:
```python
for chunk in client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    stream=True  # Habilitar streaming
):
    st.write_stream(chunk.choices[0].delta.content)
```

**Impacto esperado**:
- ✅ Percepción de latencia reducida (usuario ve texto generarse en tiempo real)
- ✅ Tiempo hasta primer token: <500ms (vs 2.6s actuales)
- ✅ Esfuerzo: **3 horas** (modificar `generate_response_with_metrics`)

**Métrica de éxito**: TTFT (Time To First Token) <500ms.

---

#### Mejora 1.3: Manejo de Errores con Retry Exponential Backoff
**Problema que resuelve**: Sin resiliencia ante fallos temporales de API.

**Solución propuesta**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def call_llm_with_retry(messages):
    return client.chat.completions.create(model="gpt-4o-mini", messages=messages)
```

**Impacto esperado**:
- ✅ Tasa de error: 0% → **<0.1%** (99.9% disponibilidad)
- ✅ Esfuerzo: **1 hora** (añadir dependencia `tenacity`)

**Métrica de éxito**: Proporción Éxito/Error >99% en dashboard.

---

### 🟡 **Prioridad 2: Importante** (Impacto Alto + Esfuerzo Medio)

#### Mejora 2.1: Reranking de Documentos Recuperados
**Problema que resuelve**: Context Precision solo 67% (33% de docs irrelevantes).

**Solución propuesta**:
- Usar modelo de reranking (Cohere Rerank API o modelo local)
- Filtrar top-3 documentos después de búsqueda híbrida inicial (top-10)

**Impacto esperado**:
- ✅ Context Precision: 67% → **85%** (mejora de 27%)
- ✅ Faithfulness: 7.2 → **8.5** (menos alucinaciones)
- ✅ Reducción de tokens: 164 → **120** tokens/consulta (ahorro 27% en costos)
- ❌ Esfuerzo: **8 horas** (integración + testing)

**Métrica de éxito**: Context Precision >80% en métricas de calidad.

---

#### Mejora 2.2: Persistencia en SQLite (en vez de JSON)
**Problema que resuelve**: 
- Logs JSON crecen linealmente (2MB por 1000 interacciones)
- No permite consultas complejas ("mostrar errores del último mes")

**Solución propuesta**:
```python
import sqlite3

conn = sqlite3.connect('data/atlas.db')
conn.execute('''
    CREATE TABLE interactions (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        query TEXT,
        response TEXT,
        metrics JSON,
        error BOOLEAN
    )
''')
```

**Impacto esperado**:
- ✅ Consultas analíticas: "SELECT AVG(latency) WHERE error=1" (imposible con JSON)
- ✅ Tamaño de almacenamiento: 2MB → **0.5MB** (compresión nativa SQLite)
- ✅ Escalabilidad: Soporta >10,000 interacciones sin degradación
- ❌ Esfuerzo: **12 horas** (migración + refactorización `_save_logs`)

**Métrica de éxito**: Dashboard puede mostrar gráficos de últimos 30 días sin lag.

---

#### Mejora 2.3: Evaluación Automática con Dataset de Referencia
**Problema que resuelve**: Métricas de calidad (faithfulness, relevance) solo se calculan en tiempo real (no hay baseline).

**Solución propuesta**:
- Crear `data/eval_dataset.json` con 20 pares pregunta-respuesta gold-standard
- Ejecutar evaluación batch semanal y comparar vs baseline

**Impacto esperado**:
- ✅ Detección temprana de regresión (si faithfulness baja de 7.2 → 6.0)
- ✅ Benchmark reproducible para defensa académica
- ❌ Esfuerzo: **6 horas** (crear dataset + script de evaluación)

**Métrica de éxito**: Notebook `logs_analysis.ipynb` con comparación semanal de métricas.

---

### 🟢 **Prioridad 3: Deseable** (Impacto Medio + Esfuerzo Alto)

#### Mejora 3.1: Integración de Fuente Externa Real (API FHIR)
**Problema que resuelve**: Solo fuentes internas estáticas (documentos predef inidos).

**Solución propuesta**:
- Integrar API FHIR del sistema hospitalario (ej: disponibilidad de camas, turnos médicos)
- Actualizar documentos RAG automáticamente cada 1 hora

**Impacto esperado**:
- ✅ Información siempre actualizada (vs docs estáticos que envejecen)
- ✅ Cumple IE2 al 100% (fuentes externas reales)
- ❌ Esfuerzo: **20 horas** (coordinación con TI hospitalaria + integración)

**Métrica de éxito**: Dashboard muestra timestamp de última actualización de datos.

---

#### Mejora 3.2: Multimodal (Soporte para Imágenes Médicas)
**Problema que resuelve**: Solo texto (no puede interpretar exámenes, mapas hospitalarios).

**Solución propuesta**:
- Usar GPT-4o (multimodal) en vez de GPT-4o-mini
- Permitir subir imágenes (radiografías, mapas) en chat

**Impacto esperado**:
- ✅ Casos de uso ampliados: "Explica esta radiografía", "¿Cómo llego al pab. 3?"
- ❌ Costo: 10x más caro ($5/1M tokens vs $0.15/1M)
- ❌ Esfuerzo: **15 horas** (cambio de modelo + UI para upload de imágenes)

**Métrica de éxito**: Dashboard muestra métrica "Consultas con imagen" vs "Solo texto".

---

#### Mejora 3.3: Despliegue en Azure con Monitoreo (Application Insights)
**Problema que resuelve**: Streamlit Cloud tiene limitaciones (sin auto-scaling, logs efimeros).

**Solución propuesta**:
- Dockerizar aplicación + desplegar en Azure Container Apps
- Integrar Application Insights para telemetría avanzada (trazas distribuidas, alertas)

**Impacto esperado**:
- ✅ Disponibilidad: 99.9% SLA (vs 99% de Streamlit Cloud)
- ✅ Auto-scaling: Soporta >100 usuarios simultáneos
- ✅ Alertas proactivas: Email si latencia >5s o error rate >1%
- ❌ Costo: $50-100/mes (vs gratis en Streamlit Cloud)
- ❌ Esfuerzo: **30 horas** (DevOps + configuración)

**Métrica de éxito**: Uptime >99.9% medido en Azure Portal.

---

## 3. Roadmap de Implementación
### Sprint 1 (Semana 1-2) - Post-Entrega EFT
- [ ] Mejora 1.1: Caché de embeddings
- [ ] Mejora 1.2: Streaming de respuestas
- [ ] Mejora 1.3: Retry con backoff exponencial

**Objetivo**: Reducir latencia a <2.8s y disponibilidad >99%.

### Sprint 2 (Semana 3-4)
- [ ] Mejora 2.1: Reranking de documentos
- [ ] Mejora 2.3: Dataset de evaluación automática

**Objetivo**: Faithfulness >8.0 y Context Precision >80%.

### Sprint 3 (Mes 2)
- [ ] Mejora 2.2: Migración a SQLite
- [ ] Mejora 3.1: Integración API FHIR (si hay acceso)

**Objetivo**: Escalabilidad para >1000 interacciones.

### Fase de Producción (Mes 3-6)
- [ ] Mejora 3.3: Despliegue en Azure
- [ ] Mejora 3.2: Soporte multimodal (opcional)
- [ ] Auditoría de seguridad externa

---

## 4. Análisis de Costo-Beneficio

| Mejora | Impacto (1-10) | Esfuerzo (horas) | ROI | Prioridad |
|--------|----------------|------------------|-----|----------|
| 1.1 Caché embeddings | 8 | 2 | 🟢 Alto | 1 |
| 1.2 Streaming | 7 | 3 | 🟢 Alto | 1 |
| 1.3 Retry + backoff | 9 | 1 | 🟢 Muy Alto | 1 |
| 2.1 Reranking | 8 | 8 | 🟡 Medio | 2 |
| 2.2 SQLite | 7 | 12 | 🟡 Medio | 2 |
| 2.3 Eval automática | 6 | 6 | 🟡 Medio | 2 |
| 3.1 API FHIR | 9 | 20 | 🟠 Bajo | 3 |
| 3.2 Multimodal | 6 | 15 | 🟠 Bajo | 3 |
| 3.3 Azure deploy | 8 | 30 | 🟠 Bajo | 3 |

---

## 5. Sostenibilidad y Escalabilidad

### Sostenibilidad (Largo Plazo)
**Proyección de costos** (1000 usuarios/mes):
- **Actual**: $10/mes (solo API calls)
- **Con mejoras Fase 1-2**: $8/mes (caché reduce 20% llamadas)
- **Producción (Fase 3)**: $150/mes (Azure hosting $100 + API $50)

**Costo por interacción**:
- Actual: $0.0001 (10 centavos por 1000 consultas)
- Target: $0.00008 (mejoras 1.1 + 2.1)

### Escalabilidad (Más Usuarios)
**Capacidad actual** (Streamlit Cloud):
- Máx usuarios simultáneos: ~20
- Latencia con 50 usuarios: >10s (inaceptable)

**Capacidad con mejoras**:
- Mejora 2.2 (SQLite): Soporta 100 usuarios
- Mejora 3.3 (Azure + auto-scaling): Soporta 1000+ usuarios

---

## 6. Referencias para Implementación

- Caché LRU: https://docs.python.org/3/library/functools.html#functools.lru_cache
- Streaming Streamlit: https://docs.streamlit.io/library/api-reference/write-magic/st.write_stream
- Tenacity (retry): https://tenacity.readthedocs.io/
- Cohere Rerank: https://docs.cohere.com/docs/reranking
- SQLite con Python: https://docs.python.org/3/library/sqlite3.html
- Azure Container Apps: https://learn.microsoft.com/en-us/azure/container-apps/

---

**Conclusión**: Las mejoras priorizadas se basan directamente en métricas observadas del dashboard. Implementar Fase 1 (Mejoras 1.1-1.3) reduciría latencia en 24% y aumentaría disponibilidad a 99.9%, mejorando significativamente UX y confiabilidad del sistema.
