# Docker Architecture

## Overview

```
Browser
  |
  | HTTP requests to localhost:5173
  v
+-------------------+
|  Vite Dev Server  |  (frontend container, port 5173)
|  localhost:5173   |
+-------------------+
  |
  | /api/* requests → proxy strips /api prefix
  v
+-------------------+
|  FastAPI Backend  |  (backend container, port 8000)
|  backend:8000     |
+-------------------+
```

All browser requests go to `localhost:5173`. Requests that match `/api/*` are transparently proxied by Vite to `http://backend:8000`, with the `/api` prefix stripped before forwarding. Static assets and the React app are served directly by Vite.

---

## Services

| Property     | backend                                      | frontend                                      |
|--------------|----------------------------------------------|-----------------------------------------------|
| Base image   | `ubuntu:20.04` (openEMS compiled from source) | `node:20-alpine`                             |
| Port         | `8000:8000`                                  | `5173:5173`                                   |
| Volumes      | `./backend:/app` (bind mount)                | `./frontend:/app` (bind mount), `node_modules` (named volume) |
| Command      | `uvicorn main:app --host 0.0.0.0 --port 8000 --reload` | `npm run dev`                      |
| Health check | `curl -f http://localhost:8000/`             | none (depends on backend being healthy)       |

---

## Proxy API

Vite's `server.proxy` configuration in `vite.config.js` rewrites requests:

```
/api/simulate/dipole  →  http://backend:8000/simulate/dipole
```

**Why this approach:**

- **Avoids CORS**: the browser never makes a cross-origin request. From the browser's perspective, both the frontend and the API are on the same origin (`localhost:5173`). No `Access-Control-Allow-Origin` headers are needed.
- **No backend changes needed**: the FastAPI app does not need to be aware of the `/api` prefix. Its routes stay as `/simulate/{antenna_type}`, `/`, etc. The Vite proxy handles the prefix translation at the network layer.
- **Works identically in development**: developers can also run `npm run dev` outside Docker and point the proxy at `http://localhost:8000` — same rewrite logic, same backend routes.

---

## Named Volume `node_modules`

The `frontend` service uses two volume mounts:

1. `./frontend:/app` — a bind mount that makes local source files available inside the container for hot-reload.
2. `node_modules:/app/node_modules` — a named volume that preserves the container's installed dependencies.

The named volume is necessary because the bind mount in step 1 would otherwise overwrite `/app/node_modules` inside the container with the host's `node_modules` directory. On a typical developer machine this directory is either missing entirely or contains packages built for the host OS (macOS/Windows), which are not compatible with the Linux container. Docker resolves the conflict by giving the named volume precedence over the bind mount at that specific path, so the container-installed, Linux-compatible packages are always used.

---

## Startup Order

1. **Backend starts** — Docker Compose brings up the `backend` container and begins running the FastAPI server with `uvicorn`.
2. **Health check passes** — Docker polls `GET http://localhost:8000/` inside the backend container at regular intervals. The backend is considered healthy once this endpoint returns HTTP 200.
3. **Frontend starts** — the `frontend` service has `depends_on: backend: condition: service_healthy`. Docker Compose does not start the Vite dev server until the backend health check has passed. This prevents the frontend from serving before the API is ready to accept requests.

---

## Troubleshooting

### Frontend does not start / connection refused

**Symptom:** browser shows "This site can't be reached" on `localhost:5173`, or the container exits immediately.

**Cause:** the backend container is not yet healthy. The frontend container will not start until the backend health check passes.

**Fix:** wait a few seconds and check backend status:
```bash
docker compose ps
docker compose logs backend
```

---

### `node_modules` missing or package errors inside the frontend container

**Symptom:** `Cannot find module '...'` errors, or Vite fails to start because dependencies are missing.

**Cause:** the named `node_modules` volume is stale or was never populated (e.g., after adding new packages to `package.json`).

**Fix:** destroy the volume and rebuild:
```bash
docker compose down -v && docker compose up --build
```

The `--build` flag forces the image to be rebuilt, which runs `npm install` and repopulates the volume with the correct packages.

---

### openEMS not found inside the backend container

**Symptom:** `ImportError: No module named 'openEMS'` or similar error in backend logs.

**Cause:** the backend image cache is out of date and does not include the openEMS installation layer.

**Fix:** force a clean rebuild of the backend image:
```bash
docker compose build --no-cache backend
docker compose up
```

---

### Code changes do not appear in the running app

**Symptom:** you edit a source file locally but the browser does not reflect the change, even after a hard refresh.

**Cause:** the bind mount may not be working correctly — Docker may not be mounting the local `src/` directory into the container.

**Fix:** verify the bind mount is active by listing the source directory inside the running container:
```bash
docker compose exec frontend ls src/
```

The output should match your local `frontend/src/` directory. If it does not, ensure the `./frontend:/app` volume is defined correctly in `docker-compose.yml` and that Docker Desktop has permission to access the project directory.

---

### Port already in use

**Symptom:** `Error: listen EADDRINUSE: address already in use 0.0.0.0:5173` or similar for port 8000.

**Cause:** another process on the host is already bound to that port.

**Fix:** find and kill the occupying process:
```bash
# For port 5173 (Vite)
lsof -ti:5173 | xargs kill -9

# For port 8000 (FastAPI)
lsof -ti:8000 | xargs kill -9
```

Then restart the stack:
```bash
docker compose up
```
