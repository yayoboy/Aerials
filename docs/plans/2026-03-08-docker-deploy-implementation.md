# Docker Full-Stack Deploy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Avviare l'intero stack (FastAPI backend + React/Vite frontend) con un singolo `docker compose up` in modalità sviluppo con hot-reload.

**Architecture:** Il frontend gira in un container node:20-alpine con Vite dev server esposto su `0.0.0.0:5173`. Le chiamate `/api/*` vengono proxiate da Vite verso `http://backend:8000` con rewrite del path. Il backend aspetta che il backend sia healthy prima di avviarsi.

**Tech Stack:** Docker Compose v3.8, node:20-alpine, Vite 7, FastAPI + uvicorn, Ubuntu 20.04 + openEMS

---

### Task 1: Crea `frontend/Dockerfile.dev`

**Files:**
- Create: `frontend/Dockerfile.dev`

**Step 1: Crea il file**

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
```

**Step 2: Verifica che la sintassi sia corretta**

```bash
docker build -f frontend/Dockerfile.dev frontend/ --no-cache --progress=plain 2>&1 | tail -5
```

Atteso: `Successfully built ...`

**Step 3: Commit**

```bash
git add frontend/Dockerfile.dev
git commit -m "feat: add Dockerfile.dev for frontend dev container"
```

---

### Task 2: Aggiorna `frontend/vite.config.js`

**Files:**
- Modify: `frontend/vite.config.js`

**Step 1: Sostituisci il contenuto del file**

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        rewrite: path => path.replace(/^\/api/, '')
      }
    }
  }
})
```

> `host: true` → Vite ascolta su `0.0.0.0` (necessario in Docker)
> `rewrite` → rimuove il prefisso `/api` prima di forwardare al backend

**Step 2: Verifica locale (opzionale, fuori Docker)**

```bash
cd frontend && npm run dev
```

Atteso: Vite si avvia, nessun errore di sintassi.

**Step 3: Commit**

```bash
git add frontend/vite.config.js
git commit -m "feat: add Vite proxy /api -> backend:8000 and host binding"
```

---

### Task 3: Aggiorna l'URL API in `frontend/src/App.jsx`

**Files:**
- Modify: `frontend/src/App.jsx:56`

**Step 1: Cambia la riga 56 — una sola modifica**

```js
// Prima (riga 56):
const res = await fetch(`http://localhost:8000/simulate/${antennaType}`, {

// Dopo:
const res = await fetch(`/api/simulate/${antennaType}`, {
```

**Step 2: Verifica che non ci siano altri URL hardcoded verso localhost:8000**

```bash
grep -r "localhost:8000" frontend/src/
```

Atteso: nessun output (nessun riferimento rimasto).

**Step 3: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: use relative /api path for simulate endpoint"
```

---

### Task 4: Aggiorna `docker-compose.yml`

**Files:**
- Modify: `docker-compose.yml`

**Step 1: Sostituisci il contenuto del file**

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - PYTHONUNBUFFERED=1
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 10s
      timeout: 5s
      retries: 5

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - node_modules:/app/node_modules
    depends_on:
      backend:
        condition: service_healthy

volumes:
  node_modules:
```

> `node_modules` named volume: evita che il bind mount `./frontend:/app` sovrascriva
> i `node_modules` compilati nel container con quelli assenti sull'host macOS.

**Step 2: Valida la sintassi del compose file**

```bash
docker compose config
```

Atteso: output YAML valido senza errori.

**Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add frontend service to docker-compose with health check"
```

---

### Task 5: Build e verifica dello stack completo

**Step 1: Build di entrambe le immagini**

```bash
docker compose build
```

> ⚠️ Il backend compila openEMS da sorgente: la **prima build richiede 30-60 minuti**.
> Le build successive usano la cache Docker e sono molto più veloci.

Atteso: `Successfully built` per entrambi i servizi.

**Step 2: Avvia lo stack**

```bash
docker compose up
```

Atteso nei log:
- `backend  | INFO:     Application startup complete.`
- `frontend | VITE v7.x.x  ready in ...ms`
- `frontend | ➜  Local:   http://localhost:5173/`

**Step 3: Verifica backend direttamente**

```bash
curl http://localhost:8000/
```

Atteso: `{"status":"ok","antennas":[...]}`

**Step 4: Verifica frontend nel browser**

Apri `http://localhost:5173` — deve caricare l'app Aerials.

**Step 5: Verifica proxy API**

```bash
curl -X POST http://localhost:5173/api/simulate/dipole \
  -H "Content-Type: application/json" \
  -d '{"antenna_params":{"length_mm":300,"gap_mm":5,"frequency_mhz":433},"conductor":{"material":"copper","cross_section":"round","radius_mm":1.0}}'
```

Atteso: JSON con `{"antenna_type":"dipole","status":"ok","results":{...}}`

**Step 6: Verifica hot-reload frontend**

Modifica un testo qualsiasi in `frontend/src/App.jsx` (es. cambia `"Aerials"` in `"Aerials 2"`), salva. Il browser deve ricaricarsi automaticamente entro 1-2 secondi.

**Step 7: Verifica hot-reload backend**

Modifica `backend/main.py` — aggiungi un campo al root endpoint:
```python
return {"status": "ok", "antennas": list(SIMULATOR_MAP.keys()), "version": "dev"}
```
Salva. Uvicorn deve mostrare `Reloading...` nei log. Verifica con `curl http://localhost:8000/`.

**Step 8: Stop stack**

```bash
docker compose down
```

---

### Task 6: Scrivi `README.md`

**Files:**
- Create: `README.md` (alla root del progetto)

**Step 1: Crea il file**

```markdown
# Aerials — Antenna Simulator

Simulatore RF di antenne basato su FDTD (openEMS). Visualizza S11 return loss e vista 3D parametrica per 12 tipi di antenna.

## Stack

- **Backend**: Python + FastAPI + openEMS (FDTD)
- **Frontend**: React 19 + Vite + Three.js + Plotly.js
- **Infrastruttura**: Docker Compose

## Prerequisiti

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installato e avviato

## Avvio rapido

```bash
git clone <repo-url>
cd aerials
docker compose up
```

Apri [http://localhost:5173](http://localhost:5173).

> **Nota:** La prima build compila openEMS da sorgente e richiede **30-60 minuti**.
> Le build successive usano la cache Docker e si avviano in pochi secondi.

## Comandi utili

| Comando | Descrizione |
|---------|-------------|
| `docker compose up` | Avvia stack in foreground (log visibili) |
| `docker compose up -d` | Avvia stack in background |
| `docker compose down` | Ferma e rimuove i container |
| `docker compose build` | Ricostruisce le immagini |
| `docker compose logs -f backend` | Segui i log del backend |
| `docker compose logs -f frontend` | Segui i log del frontend |

## Sviluppo

Lo stack avvia in modalità **hot-reload**:

- **Frontend** (`localhost:5173`): Vite rileva le modifiche in `frontend/src/` e ricarica il browser automaticamente.
- **Backend** (`localhost:8000`): uvicorn rileva le modifiche in `backend/` e riavvia il server automaticamente.

### Struttura

```
aerials/
├── backend/           # FastAPI + openEMS simulators
│   ├── app/
│   │   ├── models.py
│   │   ├── conductor.py
│   │   └── simulators/   # 12 FDTD simulators
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/          # React + Vite
│   ├── src/
│   │   ├── components/
│   │   ├── antennas/
│   │   └── App.jsx
│   ├── Dockerfile.dev
│   └── vite.config.js
└── docker-compose.yml
```

### Aggiungere un simulatore

1. Crea `backend/app/simulators/<nome>.py` con `def simulate_<nome>(params, conductor)`
2. Aggiungi l'import lazy in `backend/main.py` nella funzione `_load_simulators()`
3. Aggiungi la config frontend in `frontend/src/antennas/configs/<nome>.js`
4. Aggiungi la geometria 3D in `frontend/src/antennas/geometries/<nome>.js`

### Test backend

```bash
docker compose exec backend python -m pytest tests/ -v
```

## API

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/` | GET | Health check + lista antenne disponibili |
| `/simulate/{antenna_type}` | POST | Avvia simulazione FDTD |

Documentazione interattiva: [http://localhost:8000/docs](http://localhost:8000/docs)
```

**Step 2: Verifica che il markdown sia leggibile**

```bash
cat README.md
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with Docker setup and development guide"
```

---

### Task 7: Scrivi `docs/docker-architecture.md`

**Files:**
- Create: `docs/docker-architecture.md`

**Step 1: Crea il file**

```markdown
# Docker Architecture

## Overview

Lo stack è composto da due servizi Docker collegati tramite una rete interna gestita da Docker Compose.

```
Host (macOS/Linux/Windows)
├── localhost:5173  →  frontend container (node:20-alpine)
│                       └── Vite dev server
│                           └── /api/* proxy → http://backend:8000/*
└── localhost:8000  →  backend container (Ubuntu 20.04)
                        └── uvicorn + FastAPI + openEMS
```

## Servizi

### backend

| Campo | Valore |
|-------|--------|
| Image base | `ubuntu:20.04` |
| Porta | `8000:8000` |
| Volume | `./backend:/app` |
| Command | `uvicorn main:app --host 0.0.0.0 --port 8000 --reload` |
| Health check | `GET http://localhost:8000/` ogni 10s, 5 retry |

Il Dockerfile compila openEMS da sorgente (`/opt/openEMS`). La build richiede ~30-60 minuti la prima volta. openEMS non è disponibile su PyPI — deve essere compilato con CMake.

### frontend

| Campo | Valore |
|-------|--------|
| Image base | `node:20-alpine` |
| Porta | `5173:5173` |
| Volume | `./frontend:/app` + named volume `node_modules` |
| Command | `npm run dev` (Vite con `host: true`) |
| Dipendenza | backend `service_healthy` |

## Proxy API

Il frontend usa un proxy Vite configurato in `vite.config.js`:

```
Browser → GET/POST /api/simulate/dipole
  → Vite proxy
  → strip /api prefix
  → http://backend:8000/simulate/dipole
  → FastAPI handler
  → JSON response
```

Questo approccio:
- Evita CORS in sviluppo (tutto passa per la stessa origine `localhost:5173`)
- Non richiede modifiche al backend
- Non hardcoda porte nel codice frontend

## Named Volume `node_modules`

```yaml
volumes:
  - ./frontend:/app          # bind mount: codice sorgente sincronizzato con host
  - node_modules:/app/node_modules  # named volume: deps compilati nel container
```

Senza il named volume, il bind mount `./frontend:/app` sovrascrive `/app/node_modules`
con la directory `node_modules` dell'host (spesso vuota su macOS con Docker Desktop).
Il named volume "vince" sul bind mount per quella specifica directory.

## Ordine di avvio

```
1. backend container parte
2. healthcheck: curl http://localhost:8000/ ogni 10s
3. dopo 1 check positivo → backend è "healthy"
4. frontend container parte (depends_on: service_healthy)
5. Vite si avvia e il proxy è configurato verso backend:8000
```

## Troubleshooting

**Frontend non si avvia / "connection refused"**
→ Il backend non è ancora healthy. Aspetta che i log mostrino `Application startup complete`.

**`node_modules` mancanti nel container frontend**
→ Il named volume potrebbe essere vuoto se il container non ha mai fatto `npm install`.
→ Soluzione: `docker compose down -v && docker compose up --build`

**openEMS non trovato nel backend**
→ La build è incompleta. Ricostruisci: `docker compose build --no-cache backend`

**Modifiche al codice frontend non appaiono**
→ Verifica che il bind mount funzioni: `docker compose exec frontend ls src/`
→ Deve mostrare i file aggiornati.

**Porta 5173 o 8000 già in uso**
→ Ferma il processo che occupa la porta:
```bash
lsof -ti:5173 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```
```

**Step 2: Commit**

```bash
git add docs/docker-architecture.md
git commit -m "docs: add Docker architecture and troubleshooting guide"
```

---

## Verifica finale

Dopo tutti i task, lo stack deve:

- [ ] `docker compose build` completa senza errori
- [ ] `docker compose up` avvia entrambi i servizi
- [ ] `http://localhost:5173` mostra l'app Aerials
- [ ] Simulazione dipole completa con successo dall'UI
- [ ] Modifica a `App.jsx` → browser si ricarica (hot-reload frontend)
- [ ] Modifica a `main.py` → uvicorn si riavvia (hot-reload backend)
- [ ] `README.md` presente e leggibile
- [ ] `docs/docker-architecture.md` presente
