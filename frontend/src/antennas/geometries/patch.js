import * as THREE from 'three';

export function buildPatch(params, conductor, color) {
  const group   = new THREE.Group();
  const w       = (params.width_mm ?? 38) * 0.001;
  const l       = (params.length_mm ?? 29) * 0.001;
  const h       = (params.substrate_height_mm ?? 1.6) * 0.001;
  const subMat  = new THREE.MeshStandardMaterial({ color: 0x2a5a2a, transparent: true, opacity: 0.6 });
  const gpMat   = new THREE.MeshStandardMaterial({ color: 0x444444, metalness: 0.6 });
  const patchMat = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.3 });

  // Ground plane
  const gpGeo = new THREE.BoxGeometry(w * 1.5, 0.0002, l * 1.5);
  const gp    = new THREE.Mesh(gpGeo, gpMat);
  gp.position.y = 0;
  group.add(gp);

  // Substrate
  const subGeo = new THREE.BoxGeometry(w * 1.5, h, l * 1.5);
  const sub    = new THREE.Mesh(subGeo, subMat);
  sub.position.y = h / 2;
  group.add(sub);

  // Patch
  const patchGeo = new THREE.BoxGeometry(w, 0.0002, l);
  const patch    = new THREE.Mesh(patchGeo, patchMat);
  patch.position.y = h;
  group.add(patch);

  const feedMesh = new THREE.Mesh(
    new THREE.SphereGeometry(0.001, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 })
  );
  feedMesh.position.set(0, h / 2, -l / 2);
  group.add(feedMesh);
  return group;
}
