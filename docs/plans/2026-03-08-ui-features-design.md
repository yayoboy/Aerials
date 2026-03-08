# UI Features v3 — Design

**Date:** 2026-03-08
**Status:** Approved

## Features

1. **Frequenza → Lunghezza automatica** — derivazione in tempo reale delle misure teoriche al cambio di frequenza
2. **Diagramma SVG costruttivo** — schema tecnico con quote, feed point e spaziature
3. **Tooltip contestuali glossario** — definizioni inline al hover su sigle tecniche
4. **Antenna Moxon** — nuova antenna (backend FDTD + frontend completo)

---

## Feature 1: Frequenza → Lunghezza automatica

### Comportamento
Quando `frequency_mhz` cambia, i campi lunghezza si aggiornano automaticamente al valore teorico. Se l'utente modifica manualmente un campo lunghezza, il valore resta invariato fino al prossimo cambio di frequenza.

### Implementazione

Ogni config antenna riceve una funzione `derivedFromFreq(freqMhz)` che restituisce un oggetto con i campi da aggiornare. `AntennaForm.jsx` rileva il cambio di `frequency_mhz` e chiama questa funzione.

λ_mm = 299792.458 / freqMhz

### Formule per antenna

| Antenna | Campi derivati | Formule |
|---------|---------------|---------|
| Dipolo | `length_mm` | λ/2 |
| Monopolo | `length_mm` | λ/4 |
| Folded Dipole | `length_mm` | λ/2 |
| Inverted V | `length_mm` | λ/2 |
| Sleeve | `monopole_length_mm`, `sleeve_length_mm` | λ/4, λ/8 |
| Ground Plane | `radial_length_mm` | λ/4 |
| Loop | `perimeter_mm` | λ |
| Yagi | `driven_length_mm`, `reflector_length_mm` | λ/2, λ/2 × 1.05 |
| Discone | `cone_length_mm` | λ/4 |
| J-Pole | `long_element_mm`, `stub_length_mm` | 3λ/4, λ/4 |
| Helix | `diameter_mm` | λ/π |
| Patch | `width_mm`, `length_mm` | formula Pozar (dipende da εr) |
| Moxon | `element_length_mm`, `tail_length_mm`, `gap_mm` | vedi Feature 4 |

### File modificati
- `frontend/src/antennas/configs/*.js` — aggiunta `derivedFromFreq`
- `frontend/src/components/AntennaForm.jsx` — chiama `derivedFromFreq` al cambio di frequency_mhz

---

## Feature 2: Diagramma SVG costruttivo

### Componente
`frontend/src/components/AntennaDiagram.jsx` — SVG inline React, nessuna libreria aggiuntiva.

Posizione: nuovo `glass-panel` nel main content, dopo S11Chart.

### Contenuto del diagramma
- Geometria proporzionale (non in scala 1:1, ma proporzioni corrette)
- Quote con frecce ↔ e valori in mm
- Etichetta λ-fraction (es. "λ/2 = 475 mm")
- Feed point evidenziato con colore accent
- Spaziatura del feed point (gap tra i due elementi al punto di alimentazione)

### Struttura file
```
frontend/src/antennas/diagrams/
  dipole.js
  folded_dipole.js
  monopole.js
  yagi.js
  inverted_v.js
  loop.js
  helix.js
  sleeve.js
  discone.js
  patch.js
  ground_plane.js
  jpole.js
  moxon.js
```

Ogni file esporta `function buildDiagram(params) → ReactElement (SVG)`.

### File nuovi
- `frontend/src/components/AntennaDiagram.jsx`
- `frontend/src/antennas/diagrams/*.js` (13 file)

### File modificati
- `frontend/src/App.jsx` — aggiunge `<AntennaDiagram>`

---

## Feature 3: Tooltip contestuali glossario

### Componente
`frontend/src/components/Glossary.jsx` — wrappa testo con tooltip al hover.

```jsx
<Glossary term="S11">S11</Glossary>
```

### Dizionario
`frontend/src/constants/glossary.js`

| Termine | Definizione |
|---------|-------------|
| S11 | Coefficiente di riflessione — misura quanta potenza viene riflessa all'ingresso |
| dB | Decibel — scala logaritmica. S11 < −10 dB = buon adattamento |
| FDTD | Finite-Difference Time-Domain — metodo numerico per simulare la propagazione EM |
| λ | Lunghezza d'onda = c / f (c = 299.792 km/s) |
| MHz | Megahertz — milioni di cicli al secondo |
| GHz | Gigahertz — miliardi di cicli al secondo |
| SWR | Standing Wave Ratio — rapporto d'onda stazionaria, ideale = 1:1 |
| Feed point | Punto di alimentazione — dove il cavo coassiale si connette all'antenna |
| Return Loss | Perdita di ritorno = −S11 in dB. Più alto = meglio |
| Resonance | Frequenza di risonanza — dove S11 è minimo e l'antenna è più efficiente |
| εr | Permittività relativa del substrato (patch antenna) |

### Dove applicato
- `S11Chart.jsx` — asse Y label, titolo pannello
- `AntennaSpecs.jsx` — label "Lunghezza d'onda", "Frequenza"
- Header pannelli in `App.jsx`

### File nuovi
- `frontend/src/components/Glossary.jsx`
- `frontend/src/constants/glossary.js`

### File modificati
- `frontend/src/components/S11Chart.jsx`
- `frontend/src/components/AntennaSpecs.jsx`

---

## Feature 4: Antenna Moxon

### Descrizione
Il rettangolo Moxon è un'antenna compatta a 2 elementi derivata dal dipolo ripiegato. Larghezza ≈ 0.4762λ, profondità ridotta rispetto a una Yagi.

### Dimensioni teoriche (da formula VE3SQB / L.B. Cebik)

```
  ←————————— A ————————————→
  ┣━━━━━━━━━━━━━━━━━━━━━━━━━┫  elemento irradiante
  ↕ C (gap feed)
  ┃                         ┃  < C = gap feed
  ↕ D (gap gap)
  ┣━━━━━━━━━━━━━━━━━━━━━━━━━┫  riflettore (con coda B)
  ←——— B ———→   ←——— B ———→

A = 0.4762λ       larghezza totale
B = tail length   dipende da λ e fattore k
C = feed gap      spazio tra i due elementi al centro
D = element gap   distanza tra gli stub laterali
```

Formula: A, B, C, D derivate da λ con coefficienti empirici (Cebik):
- A = 0.4762λ
- B = 0.0820λ
- C = 0.0130λ (feed gap)
- D = 0.0710λ (gap totale - C)

### Backend
- `backend/app/simulators/moxon.py` — simulatore FDTD openEMS
- `backend/app/models.py` — aggiunge `MoxonParams`
- `backend/main.py` — aggiunge import lazy in `_load_simulators()`

### Frontend
- `frontend/src/antennas/configs/moxon.js`
- `frontend/src/antennas/geometries/moxon.js` — Three.js 3D view
- `frontend/src/antennas/diagrams/moxon.js` — SVG costruttivo
- `frontend/src/antennas/configs/index.js` — aggiunge moxon

### Parametri Moxon
```python
class MoxonParams(BaseModel):
    frequency_mhz:    float = 144.0
    element_length_mm: float = 990.0   # A = 0.4762λ
    tail_length_mm:   float = 171.0    # B = 0.0820λ
    feed_gap_mm:      float = 27.0     # C = 0.0130λ
```
