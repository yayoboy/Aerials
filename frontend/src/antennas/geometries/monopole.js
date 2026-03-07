import * as THREE from 'three';

export function buildMonopole(params, conductor, color) {
  const group    = new THREE.Group();
  const length   = (params.length_mm ?? 237.5) * 0.001;
  const gpRadius = (params.groundplane_mm ?? 300) / 2 * 0.001;
  const radius   = (conductor?.radius_mm ?? 1) * 0.001;
  const mat      = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const gpMat    = new THREE.MeshStandardMaterial({ color: 0x444444, metalness: 0.6, roughness: 0.5 });

  // Ground plane disc
  const gpGeo = new THREE.CylinderGeometry(gpRadius, gpRadius, radius, 32);
  const gp    = new THREE.Mesh(gpGeo, gpMat);
  gp.position.y = 0;

  // Monopole element
  const monoGeo = new THREE.CylinderGeometry(radius, radius, length, 12);
  const mono    = new THREE.Mesh(monoGeo, mat);
  mono.position.y = length / 2;

  const feedMesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 })
  );
  feedMesh.position.y = 0;

  group.add(gp, mono, feedMesh);
  return group;
}
