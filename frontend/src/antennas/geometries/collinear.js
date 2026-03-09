import * as THREE from 'three';

export function buildCollinear(params, conductor, color) {
  const group   = new THREE.Group();
  const elemLen = (params.element_length_mm ?? 1026) * 0.001;
  const n       = params.num_elements ?? 4;
  const total   = n * elemLen;
  const radius  = Math.max((conductor?.radius_mm ?? 1) * 0.001, total * 0.008);
  const mat     = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const ringMat = new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.6, roughness: 0.5 });

  // Main wire (upper half)
  const geoU = new THREE.CylinderGeometry(radius, radius, total / 2, 12);
  const meshU = new THREE.Mesh(geoU, mat);
  meshU.position.y = total / 4;
  group.add(meshU);

  // Main wire (lower half)
  const geoL = new THREE.CylinderGeometry(radius, radius, total / 2, 12);
  const meshL = new THREE.Mesh(geoL, mat);
  meshL.position.y = -total / 4;
  group.add(meshL);

  // Separator rings at element boundaries
  for (let i = 1; i < n; i++) {
    const y = -total / 2 + i * elemLen;
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(radius * 2.5, radius * 0.8, 6, 16),
      ringMat,
    );
    ring.rotation.x = Math.PI / 2;
    ring.position.y = y;
    group.add(ring);
  }

  // Feed sphere at centre
  group.add(new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 }),
  ));

  return group;
}
