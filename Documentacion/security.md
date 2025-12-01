# Security and Responsible Use (Resumen)

Este documento resume los protocolos de seguridad implementados (IE11) y pasos recomendados.

Implemented:
- `sanitize_input` to remove potentially dangerous characters and neutralize prompt-injection patterns.
- `ethical_check` to block harmful or out-of-scope queries.
- PII masking in log persistence (`_mask_pii`) for emails, phone numbers and long digit sequences.

Recommendations:
- Do not include real patient data in `data/` during submission. Use synthetic or redacted examples.
- For production, use secure secret management (Key Vault, AWS Secrets Manager) instead of `.env` files.
- Encrypt logs at rest and apply RBAC for access to stored logs.
- Add consent and data retention policies in `security.md` for formal documentation.
