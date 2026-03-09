import { useState, useRef, useCallback } from 'react';
import { buildDiagram as dipoleDiagram }      from '../antennas/diagrams/dipole.jsx';
import { buildDiagram as monopoleDiagram }    from '../antennas/diagrams/monopole.jsx';
import { buildDiagram as foldedDiagram }      from '../antennas/diagrams/folded_dipole.jsx';
import { buildDiagram as yagiDiagram }        from '../antennas/diagrams/yagi.jsx';
import { buildDiagram as invertedVDiagram }   from '../antennas/diagrams/inverted_v.jsx';
import { buildDiagram as loopDiagram }        from '../antennas/diagrams/loop.jsx';
import { buildDiagram as helixDiagram }       from '../antennas/diagrams/helix.jsx';
import { buildDiagram as sleeveDiagram }      from '../antennas/diagrams/sleeve.jsx';
import { buildDiagram as disconeDiagram }     from '../antennas/diagrams/discone.jsx';
import { buildDiagram as patchDiagram }       from '../antennas/diagrams/patch.jsx';
import { buildDiagram as groundPlaneDiagram } from '../antennas/diagrams/ground_plane.jsx';
import { buildDiagram as jpoleDiagram }       from '../antennas/diagrams/jpole.jsx';
import { buildDiagram as moxonDiagram }       from '../antennas/diagrams/moxon.jsx';

const DIAGRAM_MAP = {
  dipole:        dipoleDiagram,
  monopole:      monopoleDiagram,
  folded_dipole: foldedDiagram,
  yagi:          yagiDiagram,
  inverted_v:    invertedVDiagram,
  loop:          loopDiagram,
  helix:         helixDiagram,
  sleeve:        sleeveDiagram,
  discone:       disconeDiagram,
  patch:         patchDiagram,
  ground_plane:  groundPlaneDiagram,
  jpole:         jpoleDiagram,
  moxon:         moxonDiagram,
};

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 4;

export default function AntennaDiagram({ antennaType, params }) {
  const [zoom, setZoom] = useState(1);
  const containerRef = useRef(null);

  const fn = DIAGRAM_MAP[antennaType];
  if (!fn) return null;

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoom(z => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, +(z + delta).toFixed(2))));
  }, []);

  const resetZoom = () => setZoom(1);

  return (
    <div className="diagram-zoom-wrapper" style={{ height: '100%' }}>
      <div className="diagram-zoom-controls">
        <button className="zoom-btn" onClick={() => setZoom(z => Math.min(MAX_ZOOM, +(z + 0.25).toFixed(2)))}>+</button>
        <button className="zoom-btn zoom-reset" onClick={resetZoom}>{Math.round(zoom * 100)}%</button>
        <button className="zoom-btn" onClick={() => setZoom(z => Math.max(MIN_ZOOM, +(z - 0.25).toFixed(2)))}></button>
      </div>
      <div
        ref={containerRef}
        className="diagram-scroll-area"
        onWheel={handleWheel}
      >
        <div style={{ transform: `scale(${zoom})`, transformOrigin: 'top center', transition: 'transform 0.15s ease', width: '100%', height: '100%' }}>
          {fn(params)}
        </div>
      </div>
    </div>
  );
}
