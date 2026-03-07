# Design: Multi-Antenna Support + 3D Visualization

**Date:** 2026-03-07
**Status:** Approved

---

## Obiettivo

Evolvere Aerials da simulatore di singolo dipolo a piattaforma completa per la simulazione e visualizzazione di antenne, con:
- 12 tipi di antenna
- Opzioni complete per materiale e sezione trasversale del conduttore
- Visualizzazione 3D interattiva in tempo reale (Three.js)

---

## Tipi di Antenna

| # | Tipo | Parametri chiave |
|---|------|-----------------|
| 1 | Dipolo a mezza onda | lunghezza, raggio |
| 2 | Dipolo ripiegato (Folded Dipole) | lunghezza, raggio, spaziatura |
| 3 | Monopolo su piano di massa | lunghezza, raggio, diametro groundplane |
| 4 | Yagi-Uda | freq, N direttori, spaziatura, lunghezze |
| 5 | Dipolo Inverted-V | lunghezza, angolo apice, altezza |
| 6 | Loop chiuso | forma (circolare/quadrato), perimetro, raggio filo |
| 7 | Elica (Helix) | diametro, passo, N spire, modalita' (assiale/normale) |
| 8 | Antenna a manica (Sleeve/Bazooka) | lunghezza monopolo, lunghezza manica |
| 9 | Discone | angolo cono, lunghezza, diametro disco |
| 10 | Patch Microstrip | larghezza, lunghezza, substrato (er, h) |
| 11 | Ground Plane antenna | lunghezza radiale, N radiali, angolo inclinazione |
| 12 | J-Pole | lunghezza elemento lungo, lunghezza stub, spaziatura |

---

## Opzioni Conduttore

### Materiali

| Materiale | Conduttivita' (S/m) |
|-----------|---------------------|
| Rame (Cu) | 5.8 × 10⁷ |
| Argento (Ag) | 6.3 × 10⁷ |
| Alluminio (Al) | 3.5 × 10⁷ |
| Acciaio inox | 1.4 × 10⁶ |
| Ottone | 1.6 × 10⁷ |
| Personalizzato | valore libero utente |

### Sezione Trasversale

- **Filo tondo** — raggio
- **Tubo** — diametro esterno + spessore parete
- **Nastro piatto** — larghezza + spessore
- **Profilo quadrato** — lato

### Opzioni aggiuntive
- Stagnatura/rivestimento superficiale
- Rugosita' superficiale (skin effect a frequenze elevate)

---

## Architettura

### Frontend

```
frontend/src/
├── components/
│   ├── AntennaSelector.jsx     # griglia con icona/schema per ogni tipo
│   ├── AntennaForm.jsx         # form dinamico (parametri variano per tipo)
│   ├── ConductorForm.jsx       # materiale + sezione trasversale
│   ├── S11Chart.jsx            # grafico Plotly (refactor da App.jsx)
│   └── Antenna3DView.jsx       # Three.js: geometria 3D in real-time
├── antennas/
│   ├── configs/               # schema JSON parametri per ogni tipo
│   │   ├── dipole.js
│   │   ├── yagi.js
│   │   └── ...
│   └── geometries/            # funzioni che generano mesh 3D
│       ├── dipole.js
│       ├── yagi.js
│       └── ...
└── constants/
    └── conductors.js          # materiali e proprieta'
```

### Backend

```
backend/app/
├── simulators/
│   ├── dipole.py              # esistente
│   ├── folded_dipole.py
│   ├── monopole.py
│   ├── yagi.py
│   ├── inverted_v.py
│   ├── loop.py
│   ├── helix.py
│   ├── sleeve.py
│   ├── discone.py
│   ├── patch.py
│   ├── ground_plane.py
│   └── jpole.py
├── models.py                  # Pydantic models per ogni antenna + conduttore
├── conductor.py               # materiali, sezioni, conversioni
└── router.py                  # POST /simulate/{antenna_type}
```

### API

```
POST /simulate/{antenna_type}
Body: {
  antenna_params: { ... },     # parametri specifici per tipo
  conductor: {
    material: "copper" | "silver" | "aluminum" | "steel" | "brass" | "custom",
    conductivity: float,       # solo se material == "custom"
    cross_section: "round" | "tube" | "flat" | "square",
    radius_mm: float,          # round/tube
    outer_diameter_mm: float,  # tube
    wall_thickness_mm: float,  # tube
    width_mm: float,           # flat/square
    thickness_mm: float        # flat
  }
}
Response: {
  frequencies: float[],
  s11_db: float[]
}
```

---

## 3D View (Three.js)

- Rendering geometria parametrica **in real-time** (aggiornamento live, senza attendere simulazione)
- Controlli orbita: rotate, zoom, pan
- Colore conduttore basato sul materiale (rame = arancio, alluminio = grigio chiaro, ecc.)
- Indicatori visivi: punto di alimentazione (rosso), ground plane (grigio scuro), direttori/riflettore Yagi (colori distinti)
- Layout: 3D view a sinistra, S11 chart a destra (o sopra/sotto su mobile)

---

## Fasi di Implementazione

1. **Refactor backend** — models.py + conductor.py + router.py generico
2. **Simulatori backend** — implementare tutti i 12 tipi
3. **Refactor frontend** — estrarre S11Chart, creare AntennaSelector e ConductorForm
4. **Three.js 3D view** — geometrie per tutti i tipi, aggiornamento live
5. **Integrazione e test** — collegare tutto, verifica end-to-end
