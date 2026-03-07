import * as THREE from 'three';

export function buildJPole(params, conductor, color) {
  const group    = new THREE.Group();
  const longLen  = (params.long_element_mm ?? 1000) * 0.001;
  const stubLen  = (params.stub_length_mm ?? 330) * 0.001;
  const spacing  = (params.stub_spacing_mm ?? 25) * 0.001;
  const radius   = Math.max((conductor?.radius_mm ?? 1) * 0.001, longLen * 0.02);
  const mat      = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });

  const addVCyl = (x, yStart, yEnd) => {
    const len  = Math.abs(yEnd - yStart);
    const geo  = new THREE.CylinderGeometry(radius, radius, len, 12);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(x, (yStart + yEnd) / 2, 0);
    group.add(mesh);
  };
  const addHCyl = (y, x1, x2) => {
    const len  = Math.abs(x2 - x1);
    const geo  = new THREE.CylinderGeometry(radius, radius, len, 12);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.z = Math.PI / 2;
    mesh.position.set((x1 + x2) / 2, y, 0);
    group.add(mesh);
  };

  const x1 = -spacing / 2;  // long element side
  const x2 =  spacing / 2;  // stub side

  addVCyl(x1, 0, longLen);
  addVCyl(x2, 0, stubLen);
  addHCyl(0, x1, x2);
  addHCyl(stubLen, x1, x2);

  const feedMesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 })
  );
  feedMesh.position.set(x2, stubLen * 0.25, 0);
  group.add(feedMesh);
  return group;
}
