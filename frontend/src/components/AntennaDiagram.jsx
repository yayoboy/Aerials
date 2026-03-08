import { buildDiagram as dipoleDiagram }      from '../antennas/diagrams/dipole.js';
import { buildDiagram as monopoleDiagram }    from '../antennas/diagrams/monopole.js';
import { buildDiagram as foldedDiagram }      from '../antennas/diagrams/folded_dipole.js';
import { buildDiagram as yagiDiagram }        from '../antennas/diagrams/yagi.js';
import { buildDiagram as invertedVDiagram }   from '../antennas/diagrams/inverted_v.js';
import { buildDiagram as loopDiagram }        from '../antennas/diagrams/loop.js';
import { buildDiagram as helixDiagram }       from '../antennas/diagrams/helix.js';
import { buildDiagram as sleeveDiagram }      from '../antennas/diagrams/sleeve.js';
import { buildDiagram as disconeDiagram }     from '../antennas/diagrams/discone.js';
import { buildDiagram as patchDiagram }       from '../antennas/diagrams/patch.js';
import { buildDiagram as groundPlaneDiagram } from '../antennas/diagrams/ground_plane.js';
import { buildDiagram as jpoleDiagram }       from '../antennas/diagrams/jpole.js';
import { buildDiagram as moxonDiagram }       from '../antennas/diagrams/moxon.js';

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

export default function AntennaDiagram({ antennaType, params }) {
  const fn = DIAGRAM_MAP[antennaType];
  if (!fn) return null;
  return (
    <div style={{ width: '100%', height: '220px' }}>
      {fn(params)}
    </div>
  );
}
