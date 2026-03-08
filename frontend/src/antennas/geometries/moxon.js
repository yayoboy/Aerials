import * as THREE from 'three';

export function buildMoxon(params, conductor, color) {
  const group  = new THREE.Group();
  const A      = (params.element_length_mm ?? 990) * 0.001;
  const B      = (params.tail_length_mm    ?? 171) * 0.001;
  const C      = (params.feed_gap_mm       ??  27) * 0.001;
  const radius = Math.max((conductor?.radius_mm ?? 1) * 0.001, A * 0.008);
  const lam    = 299792.458 / ((params.frequency_mhz ?? 144) * 1000);
  const D      = Math.max(lam * 0.005, 0.001);
  const depth  = B + D + B;

  const mat  = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const feed = new THREE.MeshStandardMaterial({ color: 0xff3333 });

  function addWire(x1, y1, z1, x2, y2, z2, material) {
    const dx = x2-x1, dy = y2-y1, dz = z2-z1;
    const len = Math.sqrt(dx*dx + dy*dy + dz*dz);
    if (len < 1e-6) return;
    const geo = new THREE.CylinderGeometry(radius, radius, len, 8);
    const mesh = new THREE.Mesh(geo, material);
    mesh.position.set((x1+x2)/2, (y1+y2)/2, (z1+z2)/2);
    mesh.lookAt(new THREE.Vector3(x2, y2, z2));
    mesh.rotateX(Math.PI / 2);
    group.add(mesh);
  }

  // Driven element (left and right halves)
  addWire(-A/2, 0, 0, -C/2, 0, 0, mat);
  addWire( C/2, 0, 0,  A/2, 0, 0, mat);
  // Left tail
  addWire(-A/2, 0, 0, -A/2, -B, 0, mat);
  // Right tail
  addWire( A/2, 0, 0,  A/2, -B, 0, mat);
  // Reflector
  addWire(-A/2, -depth, 0, A/2, -depth, 0, mat);
  // Reflector left tail
  addWire(-A/2, -depth+B, 0, -A/2, -depth, 0, mat);
  // Reflector right tail
  addWire( A/2, -depth+B, 0,  A/2, -depth, 0, mat);

  // Feed point
  const feedGeo = new THREE.SphereGeometry(radius * 3, 8, 8);
  group.add(new THREE.Mesh(feedGeo, feed));

  return group;
}
