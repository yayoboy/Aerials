import * as THREE from 'three';

export function buildYagi(params, conductor, color) {
  const group    = new THREE.Group();
  const spacing  = (params.element_spacing_mm ?? 300) * 0.001;
  const radius   = (conductor?.radius_mm ?? 1) * 0.001;
  const matDriven   = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const matRef      = new THREE.MeshStandardMaterial({ color: 0x4488ff, metalness: 0.8, roughness: 0.4 });
  const matDir      = new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.8, roughness: 0.4 });

  const addEl = (lengthMm, z, mat) => {
    const len  = lengthMm * 0.001;
    const geo  = new THREE.CylinderGeometry(radius, radius, len, 12);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.z = Math.PI / 2;
    mesh.position.set(0, 0, z);
    group.add(mesh);
  };

  addEl(params.reflector_length_mm ?? 1050, 0, matRef);
  addEl(params.driven_length_mm ?? 1020, spacing, matDriven);
  const dirs = params.director_lengths_mm ?? [980, 960];
  dirs.forEach((dl, i) => addEl(dl, spacing * (i + 2), matDir));

  const feedMesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 })
  );
  feedMesh.position.set(0, 0, spacing);
  group.add(feedMesh);
  return group;
}
