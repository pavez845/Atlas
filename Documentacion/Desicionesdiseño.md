# Decisiones de Diseño — Agente Funcional Médico (Hospital Barros Luco)

Este documento justifica las decisiones técnicas tomadas en el proyecto (IE4 - Rúbrica EFT).

## 1. Elección de modelos

### LLM Principal: `gpt-4o-mini`
**Justificación:**
- **Costo**: ~$0.15 por 1M tokens (entrada) vs $5.00 de GPT-4o → reducción de 97% en costos
- **Latencia**: Tiempo de respuesta promedio 2-3s vs 5-8s de modelos más grandes
- **Capacidad**: Suficiente para tareas de información hospitalaria (no requiere razonamiento complejo de GPT-4)
- **Contexto**: 128k tokens permite manejar múltiples documentos hospitalarios

**Trade-off aceptado**: Menor precisión en razonamiento médico complejo a cambio de viabilidad económica para demostración académica.

### Embeddings: `text-embedding-3-small`
**Justificación:**
- **Dimensionalidad**: 1536 dimensiones (vs 3072 de `-large`) reduce memoria en 50%
- **Rendimiento**: Suficiente para corpus pequeño (~10-50 documentos hospitalarios)
- **Costo**: ~$0.02 por 1M tokens vs $0.13 de `-large`

**Trade-off aceptado**: Ligera pérdida de precisión semántica a cambio de menor consumo de recursos.

## 2. Arquitectura RAG: Híbrida (Semántica 70% + Léxica 30%)

### Decisión: Búsqueda dual combinada
**Justificación:**
- **Semántica (cosine similarity)**: Captura relaciones conceptuales ("dolor de cabeza" ≈ "migraña")
- **Léxica (keyword matching)**: Asegura coincidencias exactas ("urgencias", "laboratorio clínico")
- **Pesos 70/30**: Balanceados empíricamente tras pruebas manuales (semántica prioritaria pero léxica como refuerzo)

**Alternativas consideradas:**
- Solo semántica: Fallaba en términos médicos específicos
- Solo léxica: Incapaz de manejar sinónimos o formulaciones alternativas
- BM25 + vectorial: Requiere dependencias adicionales (Elasticsearch/Whoosh), excesivo para MVP

### Almacenamiento en memoria (numpy array)
**Justificación:**
- Dataset pequeño (<100 documentos) permite embeddings en RAM
- Latencia de búsqueda <50ms vs >200ms con bases vectoriales (Pinecone/Weaviate)
- Simplifica deployment (sin infraestructura externa)

**Trade-off aceptado**: No escala a miles de documentos, pero suficiente para caso de uso hospitalario acotado.

## 3. Seguridad y Privacidad

### Sanitización de inputs (`sanitize_input`)
**Justificación:**
- Previene inyección de prompts maliciosos ("Ignora instrucciones anteriores...")
- Remueve caracteres peligrosos para evitar ejecución de código
- Balance: No bloquea caracteres legítimos en consultas médicas (acentos, símbolos)

### Filtro ético (`ethical_check`)
**Justificación:**
- Lista de bloqueo basada en keywords ("suicidio", "daño", "ilegal")
- Previene uso malintencionado del agente
- **Limitación conocida**: Fácil de evadir con reformulaciones → en producción usar modelos de moderación (OpenAI Moderation API)

### Enmascaramiento PII (`_mask_pii`)
**Justificación:**
- Cumplimiento parcial GDPR/HIPAA: redacta emails, teléfonos, RUTs antes de persistir logs
- **Trade-off**: Logs menos útiles para debugging vs protección de datos sensibles

## 4. Observabilidad y Trazabilidad

### Logs estructurados (structlog + JSON)
**Justificación:**
- Formato JSON permite parsing automático para análisis (Pandas, ELK stack)
- Timestamps ISO 8601 para correlación temporal
- **Alternativa descartada**: Logs de texto plano (difícil de analizar programáticamente)

### Métricas calculadas por interacción
- **Latencia (total_time, rag_time)**: Identifica cuellos de botella (embeddings vs LLM)
- **Tokens (prompt_tokens, completion_tokens)**: Control de costos (~$0.0001 por interacción)
- **Calidad (faithfulness, relevance, context_precision)**: Evalúa adherencia a contexto RAG

**Trade-off**: Cómputo adicional (~100ms) para métricas vs beneficio en debugging/optimización.

## 5. Trazabilidad de Datos

### Fuentes de información
- **Internas**: 10 documentos base del Hospital Barros Luco (horarios, departamentos, procedimientos)
- **Externas**: Carga dinámica de CSV/TXT vía interfaz Streamlit
- **Versionado**: Actualmente no implementado → mejora futura (metadata con timestamps)

### Persistencia
- **Logs**: `data/logs.json` (carga automática al iniciar)
- **Mensajes**: `data/messages.json` (historial de chat por sesión)
- **Documentos externos**: `data/external_docs.json`

**Limitación**: Archivos JSON no soportan consultas complejas → migrar a SQLite en producción.

## 6. Escalabilidad y Limitaciones del Modelo

### Limitaciones conocidas de GPT-4o-mini
1. **Alucinaciones**: Puede generar información médica falsa si no hay contexto RAG suficiente
   - **Mitigación**: Métricas de faithfulness, advertencias en UI
2. **Contexto limitado**: Aunque soporta 128k tokens, rendimiento degrada con >20k
   - **Mitigación**: Limitar retrieval a top-3 documentos más relevantes
3. **Sin conocimiento actualizado**: Corte de entrenamiento en 2023
   - **Mitigación**: RAG como fuente única de verdad para info hospitalaria actual

### Plan de escalabilidad
- **Fase actual**: 10-100 usuarios simultáneos (suficiente para piloto hospitalario)
- **Producción**: Requiere:
  - Base de datos vectorial (Pinecone/Weaviate)
  - Caché de embeddings (Redis)
  - Load balancer + rate limiting por usuario
  - Costo estimado: $500-1000/mes para 1000 usuarios activos

## 7. Trade-offs Globales del Proyecto

| Decisión | Beneficio | Costo/Limitación |
|----------|-----------|--------------------|
| GPT-4o-mini | 97% más barato | Menor precisión en razonamiento complejo |
| RAG híbrido | Mayor recall | 30% más lento que semántico puro |
| Embeddings en RAM | Latencia <50ms | No escala >1000 docs |
| Logs JSON | Trazabilidad completa | 2MB por 1000 interacciones |
| Streamlit | Desarrollo rápido (1 semana) | No apto para móvil nativo |
| Sin autenticación | Prototipo simple | Inseguro para producción real |

## 8. Consideraciones de Requerimientos Organizacionales

### Caso: Hospital Barros Luco (Consultas de Información General)
**Requerimientos identificados:**
1. Respuestas rápidas (<5s) a consultas frecuentes (horarios, ubicación de departamentos)
2. Disponibilidad 24/7 (reducir carga en recepción)
3. Bajo costo operativo (hospital público con presupuesto limitado)
4. Seguridad: No divulgar datos de pacientes

**Cómo las decisiones técnicas abordan estos requerimientos:**
- **Latencia**: GPT-4o-mini + embeddings en RAM → promedio 3.4s
- **Disponibilidad**: Streamlit Cloud (99.9% uptime) + fallback a LLM directo si RAG falla
- **Costo**: ~$10/mes para 1000 consultas (vs $50,000/mes de asistente humano 24/7)
- **Seguridad**: PII masking + ethical filters + advertencia de "solo información general"

## 9. Conclusión
**Filosofía de diseño**: "Viable Minimum Product" priorizando:
1. Funcionalidad core completa (RAG + observabilidad)
2. Costo mínimo para demostración académica
3. Claridad de código para defensa oral
4. Facilidad de extensión (arquitectura modular en `ChatbotMedicoRAG`)

**Próximos pasos** (ver `Mejoras.md` para roadmap detallado):
- Migrar a base de datos relacional (SQLite)
- Añadir autenticación básica (usuarios hospitalarios)
- Integrar API real del sistema hospitalario (FHIR)
- Desplegar en Azure/AWS con monitoreo (Application Insights)
