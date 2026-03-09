import * as THREE from 'three';

export function buildTurnstile(params, conductor, color) {
  const group  = new THREE.Group();
  const arm    = (params.arm_length_mm ?? 510) * 0.001;
  const radius = Math.max((conductor?.radius_mm ?? 1) * 0.001, arm * 0.025);
  const mat    = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });

  const addArm = (x1, y1, z1, x2, y2, z2) => {
    const p1  = new THREE.Vector3(x1, y1, z1);
    const p2  = new THREE.Vector3(x2, y2, z2);
    const len = p1.distanceTo(p2);
    const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
    const dir = new THREE.Vector3().subVectors(p2, p1).normalize();
    const geo  = new THREE.CylinderGeometry(radius, radius, len, 10);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(mid);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    group.add(mesh);
  };

  // X-axis dipole
  addArm(-arm, 0, 0,  0, 0, 0);
  addArm(   0, 0, 0,  arm, 0, 0);
  // Y-axis dipole (rotated 90°)
  addArm(0, -arm, 0,  0, 0, 0);
  addArm(0,    0, 0,  0, arm, 0);

  // Feed sphere at centre
  group.add(new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 }),
  ));

  return group;
}
