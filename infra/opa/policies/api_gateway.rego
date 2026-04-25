package melispy.api_gateway

# Phase 5 fills this with full RBAC + ABAC policies.
# Default: deny all. Each allow rule added incrementally per endpoint group.

default allow := false

# Placeholder: uncomment and expand in Phase 5
# allow {
#   valid_token
#   authorized_scope
#   tenant_owns_resource
# }
