# Leviathan Sparring Lab — spring-petclinic-vuln — Spring Boot actuator all-exposed + H2 console no-auth
FROM maven:3.9-eclipse-temurin-17 AS build

ARG BUILD_COMMIT=unset
ARG COMMIT_SHA=82cb521
ENV BUILD_COMMIT=${BUILD_COMMIT}

WORKDIR /build

RUN apt-get update -qq && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/spring-projects/spring-petclinic.git /build \
    && git checkout ${COMMIT_SHA} || true

# Inject vulnerable application.properties before build
COPY application.properties /build/src/main/resources/application.properties

RUN mvn package -DskipTests -q

# --- runtime stage ---
FROM eclipse-temurin:17-jre-jammy

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Spring PetClinic — all actuator endpoints + H2 console without auth (SSRF, IDOR, deser surface)"

WORKDIR /app
COPY --from=build /build/target/*.jar app.jar

EXPOSE 8080

HEALTHCHECK --interval=20s --timeout=10s --retries=3 \
    CMD curl -sf http://localhost:8080/actuator/health || exit 1

CMD ["java", "-jar", "app.jar"]
