# Melispy Admin Service

Internal admin panel service for Melispy v3. External access is expected to be
protected by Cloudflare Access in later phases; service-local checks currently
require an authenticated admin principal except for public branding reads and
the intentionally vulnerable internal-action path.
