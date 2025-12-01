```markdown
# Seguridad y Uso Responsable (Resumen)

Este documento resume los protocolos de seguridad implementados (IE11) y las recomendaciones para su manejo.

Implementado:
- `sanitize_input`: elimina caracteres potencialmente peligrosos y neutraliza patrones de prompt-injection.
- `ethical_check`: bloquea consultas dañinas o fuera del alcance médico.
- Enmascaramiento de PII en la persistencia de logs (`_mask_pii`) para correos electrónicos, teléfonos y secuencias largas de dígitos.

Recomendaciones:
- No incluir datos reales de pacientes en `data/` al preparar la entrega. Usar ejemplos sintéticos o redactados.
- En producción, utilizar un gestor de secretos seguro (Key Vault, AWS Secrets Manager, etc.) en lugar de ficheros `.env`.
- Cifrar los logs en reposo y aplicar control de acceso/roles (RBAC) para limitar quién puede acceder a los registros.
- Añadir políticas de consentimiento y retención de datos en `security.md` para cumplir requisitos regulatorios.

``` 
