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

export default function AntennaDiagram({ antennaType, params }) {
  const fn = DIAGRAM_MAP[antennaType];
  if (!fn) return null;
  return (
    <div style={{ width: '100%', height: '220px' }}>
      {fn(params)}
    </div>
  );
}
