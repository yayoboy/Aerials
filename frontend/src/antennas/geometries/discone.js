import * as THREE from 'three';

export function buildDiscone(params, conductor, color) {
  const group    = new THREE.Group();
  const coneLen  = (params.cone_length_mm ?? 185) * 0.001;
  const coneAng  = (params.cone_angle_deg ?? 60) * Math.PI / 180;
  const discR    = (params.disc_diameter_mm ?? 150) / 2 * 0.001;
  const radius   = Math.max((conductor?.radius_mm ?? 1) * 0.001, coneLen * 0.02);
  const coneR    = coneLen * Math.sin(coneAng);
  const mat      = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const discMat  = new THREE.MeshStandardMaterial({ color: 0x444444, metalness: 0.6, roughness: 0.5 });
  const nSpokes  = 8;

  // Disc
  const discGeo  = new THREE.CylinderGeometry(discR, discR, radius, 32);
  group.add(new THREE.Mesh(discGeo, discMat));

  // Cone spokes
  for (let i = 0; i < nSpokes; i++) {
    const theta = 2 * Math.PI * i / nSpokes;
    const x     = coneR * Math.cos(theta);
    const z     = coneR * Math.sin(theta);
    const p1    = new THREE.Vector3(0, coneLen, 0);
    const p2    = new THREE.Vector3(x, 0, z);
    const len   = p1.distanceTo(p2);
    const mid   = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
    const dir   = new THREE.Vector3().subVectors(p2, p1).normalize();
    const geo   = new THREE.CylinderGeometry(radius, radius, len, 6);
    const mesh  = new THREE.Mesh(geo, mat);
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
