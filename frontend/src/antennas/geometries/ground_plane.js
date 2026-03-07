import * as THREE from 'three';

export function buildGroundPlane(params, conductor, color) {
  const group      = new THREE.Group();
  const radialLen  = (params.radial_length_mm ?? 490) * 0.001;
  const numRadials = params.num_radials ?? 4;
  const angleRad   = (params.radial_angle_deg ?? 45) * Math.PI / 180;
  const radius     = (conductor?.radius_mm ?? 1) * 0.001;
  const mat        = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });

  // Monopole element (vertical, upward)
  const monoGeo  = new THREE.CylinderGeometry(radius, radius, radialLen, 12);
  const monoMesh = new THREE.Mesh(monoGeo, mat);
  monoMesh.position.y = radialLen / 2;
  group.add(monoMesh);

  // Radials
  for (let i = 0; i < numRadials; i++) {
    const theta  = 2 * Math.PI * i / numRadials;
    const endX   = radialLen * Math.cos(angleRad) * Math.cos(theta);
    const endY   = -radialLen * Math.sin(angleRad);
    const endZ   = radialLen * Math.cos(angleRad) * Math.sin(theta);
    const p1     = new THREE.Vector3(0, 0, 0);
    const p2     = new THREE.Vector3(endX, endY, endZ);
    const len    = p1.distanceTo(p2);
    const mid    = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
    const dir    = new THREE.Vector3().subVectors(p2, p1).normalize();
    const geo    = new THREE.CylinderGeometry(radius, radius, len, 6);
    const mesh   = new THREE.Mesh(geo, mat);
    mesh.position.copy(mid);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    group.add(mesh);
  }

  const feedMesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 })
  );
  group.add(feedMesh);
  return group;
}
