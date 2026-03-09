import * as THREE from 'three';

export function buildVivaldi(params, conductor, color) {
  const group  = new THREE.Group();
  const length = (params.length_mm ?? 80) * 0.001;
  const apW    = (params.aperture_width_mm ?? 60) * 0.001;
  const slotW  = (params.slot_width_mm ?? 3) * 0.001;
  const sheetW = apW * 1.3;
  const t      = Math.max((conductor?.radius_mm ?? 1) * 0.002, 0.001);   // sheet thickness
  const mat    = new THREE.MeshStandardMaterial({ color, metalness: 0.9, roughness: 0.3 });

  const N = 10;
  const alpha = slotW < apW ? Math.log(apW / slotW) / length : 0;

  for (let n = 0; n < N; n++) {
    const z1   = (n / N) * length;
    const z2   = ((n + 1) / N) * length;
    const zMid = (z1 + z2) / 2;
    const swH  = (slotW / 2) * Math.exp(alpha * zMid);   // slot half-width at this step

    const stepLen = z2 - z1;
    const metaW   = sheetW / 2 - swH;   // width of each metal half-sheet
    if (metaW <= 0) continue;

    // Left piece
    const geoL = new THREE.BoxGeometry(metaW, t, stepLen);
    const mL   = new THREE.Mesh(geoL, mat);
    mL.position.set(-(swH + metaW / 2), 0, z1 + stepLen / 2);
    group.add(mL);

    // Right piece
    const geoR = new THREE.BoxGeometry(metaW, t, stepLen);
    const mR   = new THREE.Mesh(geoR, mat);
    mR.position.set(swH + metaW / 2, 0, z1 + stepLen / 2);
    group.add(mR);
  }

  // Feed sphere at narrow end
  group.add(new THREE.Mesh(
    new THREE.SphereGeometry(t * 2, 8, 8),
    new THREE.MeshStandardMaterial({ color: 0xff3333 }),
  ));

  return group;
}
