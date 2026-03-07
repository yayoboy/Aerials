import * as THREE from 'three';

export function buildInvertedV(params, conductor, color) {
  const group      = new THREE.Group();
  const armLen     = (params.length_mm ?? 20200) / 2 * 0.001;
  const apexH      = Math.min((params.height_mm ?? 15000) * 0.001, armLen * 0.8);
  const halfAngle  = (params.apex_angle_deg ?? 120) / 2 * Math.PI / 180;
  const radius     = (conductor?.radius_mm ?? 1) * 0.001;
  const mat        = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });

  // Each arm as a rotated cylinder
  [1, -1].forEach(sign => {
    const geo  = new THREE.CylinderGeometry(radius, radius, armLen, 12);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(sign * armLen / 2 * Math.sin(halfAngle), apexH - armLen / 2 * Math.cos(halfAngle), 0);
    mesh.rotation.z = sign * halfAngle;
    group.add(mesh);
  });

  const feedMesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 3, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 })
  );
  feedMesh.position.set(0, apexH, 0);
  group.add(feedMesh);
  return group;
}
