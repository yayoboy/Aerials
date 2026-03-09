import * as THREE from 'three';

export function buildLPDA(params, conductor, color) {
  const group  = new THREE.Group();
  const f      = params.frequency_mhz ?? 150;
  const tau    = params.tau ?? 0.90;
  const sigma  = params.sigma ?? 0.15;
  const n      = params.num_elements ?? 6;
  const lam    = 299792.458 / f;    // mm
  const nCenter = Math.floor(n / 2);

  // Element half-lengths (longest first)
  const halfLengths = Array.from({ length: n }, (_, i) =>
    (lam / 2 / 2) * Math.pow(tau, i - nCenter)
  ).sort((a, b) => b - a);

  // Z positions along boom
  const zPos = [0];
  for (let i = 0; i < n - 1; i++) {
    zPos.push(zPos[zPos.length - 1] + 2 * sigma * halfLengths[i]);
  }

  const maxHalf = halfLengths[0];
  const radius  = Math.max((conductor?.radius_mm ?? 1) * 0.001, maxHalf * 0.001 * 0.02);
  const scale   = 0.001;   // mm → m

  const matDriven = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const matEl     = new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.7, roughness: 0.4 });
  const matBoom   = new THREE.MeshStandardMaterial({ color: 0x444444, metalness: 0.9, roughness: 0.3 });

  // Boom
  const boomLen = (zPos[n - 1]) * scale;
  const boomGeo = new THREE.CylinderGeometry(radius * 0.6, radius * 0.6, boomLen, 8);
  const boomMesh = new THREE.Mesh(boomGeo, matBoom);
  boomMesh.rotation.x = Math.PI / 2;
  boomMesh.position.z = boomLen / 2;
  group.add(boomMesh);

  // Elements
  const drivenIdx = n - 1;
  halfLengths.forEach((hl, i) => {
    const len = hl * 2 * scale;
    const z   = zPos[i] * scale;
    const mat = i === drivenIdx ? matDriven : matEl;
    const geo = new THREE.CylinderGeometry(radius, radius, len, 10);
    const m   = new THREE.Mesh(geo, mat);
    m.rotation.z = Math.PI / 2;
    m.position.set(0, 0, z);
    group.add(m);
  });

  // Feed sphere at driven element
  const feedSphere = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 }),
  );
  feedSphere.position.z = zPos[drivenIdx] * scale;
  group.add(feedSphere);

  return group;
}
