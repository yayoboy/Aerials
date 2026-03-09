import * as THREE from 'three';

const SEGS = 16;

function loopPoints(loopR, phiK, tiltDeg, zOffset) {
  const tilt = (tiltDeg * Math.PI) / 180;
  const cp = Math.cos(phiK), sp = Math.sin(phiK);
  const st = Math.sin(tilt),  ct = Math.cos(tilt);

  const cx = loopR * st * cp;
  const cy = loopR * ct;
  const cz = loopR * st * sp;

  // e_a: from centre back to junction
  const eax = -st * cp, eay = -ct, eaz = -st * sp;
  // e_b: perpendicular within the blade plane
  const ebx = ct * cp, eby = -st, ebz = ct * sp;

  const pts = [];
  for (let i = 0; i <= SEGS; i++) {
    const t  = (2 * Math.PI * i) / SEGS;
    const co = Math.cos(t), si = Math.sin(t);
    pts.push(new THREE.Vector3(
      cx + loopR * (co * eax + si * ebx),
      cy + loopR * (co * eay + si * eby) + zOffset,
      cz + loopR * (co * eaz + si * ebz),
    ));
  }
  return pts;
}

export function buildCloverleaf(params, conductor, color) {
  const group   = new THREE.Group();
  const loopR   = ((params.loop_diameter_mm ?? 16.5) / 2) * 0.001;
  const tiltDeg = params.tilt_deg ?? 40;
  const radius  = Math.max((conductor?.radius_mm ?? 1) * 0.001, loopR * 0.12);
  const mat     = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });

  const addSeg = (p1, p2) => {
    const len = p1.distanceTo(p2);
    if (len < 1e-6) return;
    const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
    const dir = new THREE.Vector3().subVectors(p2, p1).normalize();
    const geo  = new THREE.CylinderGeometry(radius, radius, len, 6);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(mid);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    group.add(mesh);
  };

  const zOff = radius * 3;   // small offset above feed point
  for (let k = 0; k < 3; k++) {
    const phiK = (2 * Math.PI * k) / 3;
    const pts  = loopPoints(loopR, phiK, tiltDeg, zOff);
    for (let i = 0; i < pts.length - 1; i++) addSeg(pts[i], pts[i + 1]);
  }

  // Feed sphere at base
  group.add(new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 }),
  ));

  return group;
}
