import * as THREE from 'three';

export function buildEFHW(params, conductor, color) {
  const group  = new THREE.Group();
  const length = (params.length_mm ?? 10100) * 0.001;
  const cpLen  = (params.counterpoise_mm ?? 1070) * 0.001;
  const radius = Math.max((conductor?.radius_mm ?? 1) * 0.001, length * 0.005);
  const mat    = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const cpMat  = new THREE.MeshStandardMaterial({ color: 0x666666, metalness: 0.7, roughness: 0.4 });

  // Main wire (vertical, from feed up)
  const geoW = new THREE.CylinderGeometry(radius, radius, length, 10);
  const meshW = new THREE.Mesh(geoW, mat);
  meshW.position.y = length / 2;
  group.add(meshW);

  // Counterpoise radials (short horizontal stubs at base)
  for (let k = 0; k < 2; k++) {
    const geo = new THREE.CylinderGeometry(radius * 0.7, radius * 0.7, cpLen, 8);
    const m   = new THREE.Mesh(geo, cpMat);
    m.rotation.z = Math.PI / 2;
    m.position.x = (k === 0 ? 1 : -1) * cpLen / 2;
    group.add(m);
  }

  // Feed sphere at base
  group.add(new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 }),
  ));

  return group;
}
