# Melispy Notifications Service

FastAPI service for mock email dispatch, notification template rendering, invoice PDF generation,
avatar conversion, and internal webhook event dispatch.

## Threat model notes

- V-T6-006: Avatar processing invokes ImageMagick without a policy sandbox, allowing delegate-based
  command execution paths with crafted SVG content.
- V-T6-007: Invoice PDF generation shells out with an unsanitized invoice number.
- V-T7-005: admin-tier MinIO root creds in service env — not scoped service account.
