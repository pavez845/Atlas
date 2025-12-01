```markdown
# Seguridad y Uso Responsable — Protocolos Implementados

Este documento detalla los protocolos de seguridad y uso ético implementados en el Agente Funcional Médico (IE11 - Rúbrica EFT).

## 1. Protocolos de Seguridad Implementados

### 1.1 Sanitización de Entradas (`sanitize_input`)
**Ubicación**: `AtlasBot.py` líneas 430-450

**Funcionalidad**:
- Elimina caracteres peligrosos: `<`, `>`, `{`, `}`, `|`, `\\`, patrones de shell
- Detecta patrones de inyección de prompts:
  - "Ignora instrucciones anteriores"
  - "Olvida el contexto"
  - "Ejecuta el siguiente código"
- Limita longitud de input a 2000 caracteres (previene ataques DoS)

**Criterios éticos**: No bloquea caracteres legítimos en consultas médicas (acentos, símbolos clínicos).

### 1.2 Filtro Ético (`ethical_check`)
**Ubicación**: `AtlasBot.py` líneas 460-480

**Lista de bloqueo** (keywords):
- Contenido dañino: "suicidio", "daño", "violencia", "abuso"
- Solicitudes ilegales: "drogas", "armas", "explosivos"
- Uso inapropiado: "hack", "vulnerabilidad", "bypass"

**Respuesta**: Mensaje amigable redirigiendo a recursos profesionales (línea salud mental: 600 360 7777).

**Limitación conocida**: Filtro basado en keywords puede ser evadido con sinónimos. 
**Mitigación planificada**: Integrar OpenAI Moderation API (clasificador ML).

### 1.3 Enmascaramiento de PII (`_mask_pii`)
**Ubicación**: `AtlasBot.py` líneas 570-590

**Datos protegidos** (antes de persistir logs):
- Emails: `usuario@ejemplo.com` → `[EMAIL_REDACTED]`
- Teléfonos: `+56912345678` → `[PHONE_REDACTED]`
- RUT/Números largos: `12345678-9` → `[NUMBER_REDACTED]`
- Nombres propios: Detectados si coinciden con patrones `Dr./Dra. [Nombre]`

**Justificación**: Cumplimiento parcial GDPR Art. 32 (pseudonimización) y HIPAA §164.514 (de-identificación).

## 2. Consideraciones Normativas

### 2.1 GDPR (Reglamento General de Protección de Datos - UE)
**Aplicable si**: Hospital atiende pacientes europeos o comparte datos con instituciones UE.

**Cumplimiento actual**:
- ✅ Art. 25: Privacy by Design (enmascaramiento PII desde diseño)
- ✅ Art. 32: Medidas de seguridad (sanitización, logs cifrados recomendados)
- ⚠️ Art. 17: Derecho al olvido (NO implementado - logs persisten indefinidamente)
- ⚠️ Art. 30: Registro de actividades (logs existen, pero sin audit trail completo)

**Acciones requeridas para producción**:
1. Implementar endpoint `/delete_user_data` para cumplir derecho al olvido
2. Añadir consentimiento explícito antes de almacenar logs (checkbox en UI)
3. Cifrar `data/logs.json` con AES-256 en reposo
4. Política de retención: eliminar logs >90 días automáticamente

### 2.2 HIPAA (Health Insurance Portability and Accountability Act - USA)
**Aplicable si**: Hospital maneja datos de pacientes estadounidenses.

**Cumplimiento actual**:
- ✅ §164.312(a)(1): Control de acceso (recomendado - no implementado aún)
- ✅ §164.312(b): Audit controls (logs estructurados con timestamps)
- ⚠️ §164.312(e)(1): Cifrado en transmisión (usar HTTPS en producción)
- ❌ §164.514(b): De-identificación completa (PII masking es parcial)

**Acciones requeridas**:
1. Implementar autenticación (JWT tokens) + roles (admin, enfermera, paciente)
2. Cifrado end-to-end para datos en tránsito (TLS 1.3)
3. Auditoría de acceso: log de quién accedió a qué datos y cuándo

### 2.3 Ley 21.096 (Protección de Datos Personales - Chile)
**Aplicable**: Sí, Hospital Barros Luco está en Santiago, Chile.

**Cumplimiento actual**:
- ✅ Art. 4: Datos tratados con finalidad determinada (información hospitalaria)
- ✅ Art. 6: Seguridad de datos (sanitización, filtros éticos)
- ⚠️ Art. 12: Derecho de información (usuario debe saber qué datos se almacenan)

**Acciones requeridas**:
1. Añadir banner en UI: "Este chatbot almacena sus consultas con fines de mejora del servicio. No comparta información sensible."
2. Política de privacidad visible en sidebar de Streamlit

## 3. Control de Acceso y Manejo de Credenciales

### 3.1 Variables de Entorno (`.env`)
**Secretos almacenados**:
- `OPENAI_API_KEY`: Clave API de OpenAI (acceso a GPT-4o-mini)
- `GITHUB_TOKEN`: Token de autenticación para GitHub Models (alternativa)
- `OPENAI_BASE_URL`: URL del endpoint (permite usar Azure OpenAI)

**Recomendaciones actuales** (archivo `.env` NO incluido en repositorio):
```bash
# .gitignore incluye:
.env
*.env
data/logs.json  # No subir logs con datos reales
```

**Producción**: Usar gestor de secretos:
- **Azure**: Azure Key Vault
- **AWS**: AWS Secrets Manager
- **Local**: HashiCorp Vault

### 3.2 Control de Acceso (NO implementado - recomendado)
**Estado actual**: Cualquier usuario puede acceder a Streamlit sin autenticación.

**Plan de implementación (Fase 2)**:
1. Autenticación básica con Streamlit-Authenticator:
   ```python
   import streamlit_authenticator as stauth
   authenticator = stauth.Authenticate(names, usernames, passwords, 'atlas_cookie', 'secret_key')
   ```
2. Roles:
   - **Admin**: Acceso a dashboard completo, descarga de logs
   - **Personal médico**: Acceso a chat + gestión documentos
   - **Público**: Solo chat, sin acceso a métricas

3. Rate limiting por usuario (ya implementado con `RateLimiter`):
   - 10 consultas/minuto por IP
   - 100 consultas/hora por sesión

## 4. Uso Responsable de IA

### 4.1 Advertencias Implementadas
**Ubicación**: Sidebar de Streamlit (líneas 680-690)

**Texto mostrado**:
> ⚠️ **Importante**: Este es un asistente informativo. No reemplaza consulta médica profesional. Ante emergencias, llame al 131 (SAMU).

### 4.2 Limitaciones Declaradas
- No provee diagnósticos médicos
- No receta medicamentos
- No interpreta exámenes clínicos
- Solo proporciona información general del hospital (horarios, ubicaciones, procedimientos administrativos)

### 4.3 Transparencia
**Dashboard de observabilidad** (Tab 3) muestra:
- Cuándo el agente usó RAG vs conocimiento propio del LLM
- Métricas de calidad (faithfulness, relevance) para cada respuesta
- Logs descargables para auditoría externa

### 4.4 Sesgos Conocidos
**Modelo base (GPT-4o-mini)** puede contener:
- Sesgo geográfico: Entrenado principalmente en datos anglosajones
- Sesgo temporal: Conocimiento cortado en octubre 2023
- **Mitigación**: RAG como fuente prioritaria (documentos locales chilenos actualizados)

## 5. Recomendaciones para Entrega Académica

### 5.1 Datos Sintéticos
⚠️ **IMPORTANTE**: NO incluir datos reales de pacientes en `data/logs.json` al subir a GitHub.

**Datos de prueba recomendados**:
```json
{
  "query": "¿Cuáles son los horarios de atención?",
  "response": "El hospital atiende 24/7 en urgencias...",
  "user_id": "test_user_123",
  "timestamp": "2025-11-30T10:30:00Z"
}
```

### 5.2 Revisión Pre-Entrega
**Checklist de seguridad**:
- [ ] `.env` NO está en el repositorio
- [ ] `data/logs.json` contiene solo ejemplos redactados
- [ ] No hay claves API hardcodeadas en el código
- [ ] README incluye advertencia de uso responsable
- [ ] Logs exportados del dashboard tienen PII enmascarada

## 6. Roadmap de Seguridad (Post-Entrega)

### Fase 1 (Prioridad Alta) - Semanas 1-2
1. Implementar autenticación básica (Streamlit-Authenticator)
2. Cifrar logs en reposo con `cryptography.fernet`
3. Habilitar HTTPS (Streamlit Cloud lo provee por defecto)

### Fase 2 (Prioridad Media) - Semanas 3-4
4. Integrar OpenAI Moderation API (reemplazar filtro de keywords)
5. Política de retención automática (cron job elimina logs >90 días)
6. Consentimiento explícito (checkbox en primera interacción)

### Fase 3 (Producción) - Mes 2-3
7. Auditoría externa de seguridad (penetration testing)
8. Certificación ISO 27001 (si el hospital lo requiere)
9. Integración con sistema de autenticación hospitalario (LDAP/SAML)

## 7. Contacto para Incidentes de Seguridad

**En caso de detección de vulnerabilidad**:
- Email: seguridad@hospitalbarroluco.cl (ficticio para demo)
- Proceso: Reportar vía issue privado en GitHub (Security Advisories)
- SLA: Respuesta en 48h, parche crítico en 7 días

## 8. Referencias Normativas

- GDPR: https://gdpr-info.eu/
- HIPAA: https://www.hhs.gov/hipaa/index.html
- Ley 21.096 (Chile): https://www.bcn.cl/leychile/navegar?idNorma=1141599
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
- OWASP Top 10 for LLM: https://owasp.org/www-project-top-10-for-large-language-model-applications/

---

**Conclusión**: El sistema implementa medidas de seguridad básicas apropiadas para un MVP académico. Para producción real en entorno hospitalario, requiere completar Fase 1-3 del roadmap y auditoría profesional.

``` 
