import * as THREE from 'three';

export function buildBiconical(params, conductor, color) {
  const group    = new THREE.Group();
  const coneLen  = (params.cone_length_mm ?? 250) * 0.001;
  const halfAng  = ((params.cone_angle_deg ?? 60) * Math.PI) / 180;
  const baseR    = coneLen * Math.sin(halfAng);
  const radius   = Math.max((conductor?.radius_mm ?? 1) * 0.001, coneLen * 0.015);
  const mat      = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const n        = 10;   // wires per cone

  const addWire = (x1, y1, z1, x2, y2, z2) => {
    const p1  = new THREE.Vector3(x1, y1, z1);
    const p2  = new THREE.Vector3(x2, y2, z2);
    const len = p1.distanceTo(p2);
    const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
    const dir = new THREE.Vector3().subVectors(p2, p1).normalize();
    const geo  = new THREE.CylinderGeometry(radius, radius, len, 8);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(mid);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    group.add(mesh);
  };

  for (let k = 0; k < n; k++) {
    const theta = (2 * Math.PI * k) / n;
    const bx = baseR * Math.cos(theta);
    const bz = baseR * Math.sin(theta);
    // Upper cone (apex at y=0, base at y=+coneLen)
    addWire(0, 0,        0, bx, coneLen,  bz);
    // Lower cone (apex at y=0, base at y=-coneLen)
    addWire(0, 0,        0, bx, -coneLen, bz);
  }

  // Feed sphere
  group.add(new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 }),
  ));

  return group;
}
