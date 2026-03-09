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
import { buildMoxon }       from './moxon.js';
import { buildTurnstile }   from './turnstile.js';
import { buildCollinear }   from './collinear.js';
import { buildEFHW }        from './efhw.js';
import { buildLPDA }        from './lpda.js';
import { buildBiconical }   from './biconical.js';
import { buildRhombic }     from './rhombic.js';
import { buildCloverleaf }  from './cloverleaf.js';
import { buildVivaldi }     from './vivaldi.js';

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
  moxon:         buildMoxon,
  turnstile:     buildTurnstile,
  collinear:     buildCollinear,
  efhw:          buildEFHW,
  lpda:          buildLPDA,
  biconical:     buildBiconical,
  rhombic:       buildRhombic,
  cloverleaf:    buildCloverleaf,
  vivaldi:       buildVivaldi,
};
