# Leviathan Sparring Lab — dotnet-goat — ASP.NET Core with insecure deser + SSRF + file upload
FROM mcr.microsoft.com/dotnet/sdk:8.0-bookworm-slim AS build

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

WORKDIR /src
COPY DotnetGoat.csproj ./
RUN dotnet restore

COPY . .
RUN dotnet publish -c Release -o /out

# --- runtime stage ---
FROM mcr.microsoft.com/dotnet/aspnet:8.0-bookworm-slim

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description=".NET ASP.NET Core — insecure deserialization, SSRF, file upload, IDOR, JWT misconfig"

WORKDIR /app
COPY --from=build /out .

# Disable HTTPS redirection — lab only uses HTTP
ENV ASPNETCORE_URLS=http://+:8080 \
    ASPNETCORE_ENVIRONMENT=Development \
    JWT_SECRET=lab-weak-jwt-secret-000000000000

EXPOSE 8080

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:8080/health || exit 1

ENTRYPOINT ["dotnet", "DotnetGoat.dll"]
