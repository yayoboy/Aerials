import * as THREE from 'three';

export function buildDipole(params, conductor, color) {
  const group  = new THREE.Group();
  const length = (params.length_mm ?? 475) * 0.001;
  const radius = Math.max((conductor?.radius_mm ?? 1) * 0.001, length * 0.02);
  const mat    = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });

  const half = length / 2;
  const geo1 = new THREE.CylinderGeometry(radius, radius, half, 12);
  const m1   = new THREE.Mesh(geo1, mat);
  m1.position.y = half / 2;

  const geo2 = new THREE.CylinderGeometry(radius, radius, half, 12);
  const m2   = new THREE.Mesh(geo2, mat);
  m2.position.y = -half / 2;

  const feedMesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 })
  );

  group.add(m1, m2, feedMesh);
  return group;
}
