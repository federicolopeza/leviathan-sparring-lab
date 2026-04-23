# Leviathan Sparring Lab — keycloak-weak — Keycloak default admin + weak realm + broad redirect URIs
# operator: pin digest via scripts/pin-digests.sh at scaffold time
FROM quay.io/keycloak/keycloak:24.0.1

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Keycloak — default admin creds, weak realm, broad redirect URIs, admin console exposed"

# Weak admin credentials (intentional)
ENV KEYCLOAK_ADMIN=admin \
    KEYCLOAK_ADMIN_PASSWORD=admin \
    KC_HTTP_ENABLED=true \
    KC_HOSTNAME_STRICT=false \
    KC_HOSTNAME_STRICT_HTTPS=false

# Import pre-configured weak realm on startup
COPY realm-export.json /opt/keycloak/data/import/realm-export.json

EXPOSE 8080

HEALTHCHECK --interval=20s --timeout=10s --retries=3 \
    CMD curl -sf http://localhost:8080/health/ready || exit 1

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
CMD ["start-dev", "--import-realm"]
