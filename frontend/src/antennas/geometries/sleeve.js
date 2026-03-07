import * as THREE from 'three';

export function buildSleeve(params, conductor, color) {
  const group      = new THREE.Group();
  const monoLen    = (params.monopole_length_mm ?? 490) * 0.001;
  const sleeveLen  = (params.sleeve_length_mm ?? 245) * 0.001;
  const radius     = Math.max((conductor?.radius_mm ?? 1) * 0.001, monoLen * 0.02);
  const sleeveR    = radius * 4;
  const mat        = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const sleeveMat  = new THREE.MeshStandardMaterial({ color: 0x666666, metalness: 0.7, roughness: 0.4 });

  // Sleeve (outer tube, bottom portion)
  const sleeveGeo = new THREE.CylinderGeometry(sleeveR, sleeveR, sleeveLen, 16);
  const sleeveMesh = new THREE.Mesh(sleeveGeo, sleeveMat);
  sleeveMesh.position.y = sleeveLen / 2;
  group.add(sleeveMesh);

  // Monopole (inner, full length above sleeve)
  const monoGeo  = new THREE.CylinderGeometry(radius, radius, monoLen, 12);
  const monoMesh = new THREE.Mesh(monoGeo, mat);
  monoMesh.position.y = sleeveLen + monoLen / 2;
  group.add(monoMesh);

  const feedMesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 })
  );
  feedMesh.position.y = 0;
  group.add(feedMesh);
  return group;
}
