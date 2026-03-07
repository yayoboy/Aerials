import * as THREE from 'three';

export function buildLoop(params, conductor, color) {
  const group  = new THREE.Group();
  const perim  = (params.perimeter_mm ?? 21400) * 0.001;
  const side   = perim / 4;
  const radius = Math.max((conductor?.radius_mm ?? 1) * 0.001, side * 0.02);
  const mat    = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const half   = side / 2;

  const addSeg = (x, y, length, rotZ) => {
    const geo  = new THREE.CylinderGeometry(radius, radius, length, 12);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.z = rotZ;
    mesh.position.set(x, y, 0);
    group.add(mesh);
  };

  addSeg(0,     half,  side, 0);             // top
  addSeg(0,    -half,  side, 0);             // bottom
  addSeg( half, 0,     side, Math.PI / 2);   // right
  addSeg(-half, 0,     side, Math.PI / 2);   // left

  const feedMesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 })
  );
  feedMesh.position.set(-half, 0, 0);
  group.add(feedMesh);
  return group;
}
