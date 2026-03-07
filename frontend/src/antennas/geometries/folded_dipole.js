import * as THREE from 'three';

export function buildFoldedDipole(params, conductor, color) {
  const group   = new THREE.Group();
  const length  = (params.length_mm ?? 1020) * 0.001;
  const spacing = (params.spacing_mm ?? 25) * 0.001;
  const radius  = (conductor?.radius_mm ?? 1) * 0.001;
  const mat     = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const half    = length / 2;

  const addCyl = (h, x, y) => {
    const geo  = new THREE.CylinderGeometry(radius, radius, h, 12);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(x, 0, 0);
    group.add(mesh);
  };
  const addBridge = (y, x1, x2) => {
    const len  = Math.abs(x2 - x1);
    const geo  = new THREE.CylinderGeometry(radius, radius, len, 12);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.z = Math.PI / 2;
    mesh.position.set((x1 + x2) / 2, y, 0);
    group.add(mesh);
  };

  addCyl(length, -spacing / 2, 0);  // driven element
  addCyl(length,  spacing / 2, 0);  // return element
  addBridge( half, -spacing / 2, spacing / 2);  // top bridge
  addBridge(-half, -spacing / 2, spacing / 2);  // bottom bridge

  const feedMesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 })
  );
  group.add(feedMesh);
  return group;
}
