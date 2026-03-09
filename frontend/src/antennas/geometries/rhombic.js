import * as THREE from 'three';

export function buildRhombic(params, conductor, color) {
  const group   = new THREE.Group();
  const legLen  = (params.leg_length_mm ?? 20000) * 0.001;
  const halfAng = ((params.apex_angle_deg ?? 60) / 2 * Math.PI) / 180;
  const xSide   = legLen * Math.sin(halfAng);
  const zMid    = legLen * Math.cos(halfAng);
  const zRear   = 2 * zMid;
  const radius  = Math.max((conductor?.radius_mm ?? 1) * 0.001, legLen * 0.006);
  const mat     = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const tMat    = new THREE.MeshStandardMaterial({ color: 0xcc4444, metalness: 0.6, roughness: 0.5 });

  const addWire = (x1, y1, z1, x2, y2, z2, m = mat) => {
    const p1  = new THREE.Vector3(x1, y1, z1);
    const p2  = new THREE.Vector3(x2, y2, z2);
    const len = p1.distanceTo(p2);
    const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
    const dir = new THREE.Vector3().subVectors(p2, p1).normalize();
    const geo  = new THREE.CylinderGeometry(radius, radius, len, 8);
    const mesh = new THREE.Mesh(geo, m);
    mesh.position.copy(mid);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    group.add(mesh);
  };

  // Four legs
  addWire(0, 0, 0,      -xSide, 0, zMid);
  addWire(0, 0, 0,       xSide, 0, zMid);
  addWire(-xSide, 0, zMid, 0, 0, zRear);
  addWire( xSide, 0, zMid, 0, 0, zRear);

  // Feed sphere (front)
  group.add(new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 }),
  ));

  // Termination resistor (rear) — shown as a small coloured block
  const termGeo = new THREE.BoxGeometry(radius * 5, radius * 5, radius * 5);
  const termMesh = new THREE.Mesh(termGeo, tMat);
  termMesh.position.set(0, 0, zRear);
  group.add(termMesh);

  return group;
}
