import * as THREE from 'three';

export function buildHelix(params, conductor, color) {
  const group     = new THREE.Group();
  const helixR    = (params.diameter_mm ?? 40) / 2 * 0.001;
  const pitch     = (params.pitch_mm ?? 30) * 0.001;
  const turns     = params.turns ?? 8;
  const radius    = (conductor?.radius_mm ?? 1) * 0.001;
  const totalH    = turns * pitch;
  const stepsPerTurn = 16;
  const totalSteps   = turns * stepsPerTurn;
  const mat = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.4 });
  const gpMat = new THREE.MeshStandardMaterial({ color: 0x444444, metalness: 0.6, roughness: 0.5 });

  // Ground plane
  const gpGeo = new THREE.CylinderGeometry(helixR * 2, helixR * 2, radius, 32);
  group.add(new THREE.Mesh(gpGeo, gpMat));

  // Helix segments
  for (let i = 0; i < totalSteps; i++) {
    const t1 = 2 * Math.PI * i / stepsPerTurn;
    const t2 = 2 * Math.PI * (i + 1) / stepsPerTurn;
    const z1 = (i / totalSteps) * totalH;
    const z2 = ((i + 1) / totalSteps) * totalH;
    const p1 = new THREE.Vector3(helixR * Math.cos(t1), z1, helixR * Math.sin(t1));
    const p2 = new THREE.Vector3(helixR * Math.cos(t2), z2, helixR * Math.sin(t2));
    const len = p1.distanceTo(p2);
    const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
    const dir = new THREE.Vector3().subVectors(p2, p1).normalize();

    const geo  = new THREE.CylinderGeometry(radius, radius, len, 6);
    const mesh = new THREE.Mesh(geo, mat);
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
