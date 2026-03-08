# Docker Full-Stack Deploy — Design

**Date:** 2026-03-08
**Status:** Approved

## Goal

Avviare l'intero stack (backend Python/openEMS + frontend React/Vite) con un singolo `docker compose up`, in modalità sviluppo con hot-reload.

## Architecture

```
Browser → localhost:5173 (Vite dev server)
  └── /api/* → Vite proxy (strip /api) → http://backend:8000
                                           └── /simulate/{type}
                                           └── /  (health)
```

## Services

### backend
- Base: `Ubuntu 20.04` + openEMS compilato da sorgente
- Server: `uvicorn` con `--reload`
- Porta host: `8000`
- Volume: `./backend:/app` (hot-reload)
- Health check: `GET http://localhost:8000/` ogni 10s

### frontend
- Base: `node:20-alpine`
- Server: `vite dev --host` (espone `0.0.0.0:5173`)
- Porta host: `5173`
- Volume: `./frontend:/app` + named volume `node_modules` (isola deps del container dall'host)
- `depends_on`: backend con `condition: service_healthy`

## Files Changed

| File | Tipo | Modifica |
|------|------|----------|
| `docker-compose.yml` | modifica | aggiunge servizio frontend, health check backend, named volume |
| `frontend/Dockerfile.dev` | nuovo | image node:20-alpine, npm install, vite dev |
| `frontend/vite.config.js` | modifica | `server.host: true`, proxy `/api` → `http://backend:8000` con rewrite |
| `frontend/src/App.jsx` | modifica | URL da `http://localhost:8000/simulate/` a `/api/simulate/` |

## Key Decisions

**Vite proxy con rewrite** — il backend non ha prefisso `/api`, quindi il proxy rimuove `/api` prima di forwardare. Evita di modificare il backend.

**Named volume per node_modules** — senza questo, il bind mount `./frontend:/app` sovrascrive i `node_modules` compilati nel container con quelli dell'host (spesso assenti su macOS), causando crash del container.

**`server.host: true`** — necessario perché Vite di default ascolta solo su `127.0.0.1`; dentro Docker il container deve esporre `0.0.0.0` per essere raggiungibile dall'host.

**`depends_on: condition: service_healthy`** — il frontend aspetta che il backend risponda prima di avviarsi, evitando errori di connessione in fase di boot.

## Documentation

- `README.md` alla root: setup, prerequisiti, comandi di avvio/stop, sviluppo
- `docs/docker-architecture.md`: architettura del deploy, dettagli tecnici, troubleshooting
