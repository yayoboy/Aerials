import { buildDipole }      from './dipole.js';
import { buildFoldedDipole } from './folded_dipole.js';
import { buildMonopole }    from './monopole.js';
import { buildYagi }        from './yagi.js';
import { buildInvertedV }   from './inverted_v.js';
import { buildLoop }        from './loop.js';
import { buildHelix }       from './helix.js';
import { buildSleeve }      from './sleeve.js';
import { buildDiscone }     from './discone.js';
import { buildPatch }       from './patch.js';
import { buildGroundPlane } from './ground_plane.js';
import { buildJPole }       from './jpole.js';

export const GEOMETRY_BUILDERS = {
  dipole:        buildDipole,
  folded_dipole: buildFoldedDipole,
  monopole:      buildMonopole,
  yagi:          buildYagi,
  inverted_v:    buildInvertedV,
  loop:          buildLoop,
  helix:         buildHelix,
  sleeve:        buildSleeve,
  discone:       buildDiscone,
  patch:         buildPatch,
  ground_plane:  buildGroundPlane,
  jpole:         buildJPole,
};
