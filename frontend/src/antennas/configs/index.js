import dipole       from './dipole.js';
import foldedDipole from './folded_dipole.js';
import monopole     from './monopole.js';
import yagi         from './yagi.js';
import invertedV    from './inverted_v.js';
import loop         from './loop.js';
import helix        from './helix.js';
import sleeve       from './sleeve.js';
import discone      from './discone.js';
import patch        from './patch.js';
import groundPlane  from './ground_plane.js';
import jpole        from './jpole.js';
import moxon        from './moxon.js';
import turnstile    from './turnstile.js';
import collinear    from './collinear.js';
import efhw         from './efhw.js';
import lpda         from './lpda.js';
import biconical    from './biconical.js';
import rhombic      from './rhombic.js';
import cloverleaf   from './cloverleaf.js';
import vivaldi      from './vivaldi.js';

export const ANTENNA_CONFIGS = [
  dipole, foldedDipole, monopole, yagi, invertedV, loop,
  helix, sleeve, discone, patch, groundPlane, jpole, moxon,
  turnstile, collinear, efhw, lpda, biconical, rhombic, cloverleaf, vivaldi,
];

export const ANTENNA_MAP = Object.fromEntries(
  ANTENNA_CONFIGS.map(c => [c.id, c])
);
