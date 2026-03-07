// frontend/src/components/Antenna3DView.jsx
import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GEOMETRY_BUILDERS } from '../antennas/geometries/index.js';
import { MATERIALS } from '../constants/conductors.js';

export default function Antenna3DView({ antennaType, params, conductor }) {
  const mountRef   = useRef(null);
  const sceneRef   = useRef(null);
  const cameraRef  = useRef(null);
  const rendRef    = useRef(null);
  const ctrlRef    = useRef(null);
  const antennaRef = useRef(null);
  const frameRef   = useRef(null);

  // One-time Three.js setup
  useEffect(() => {
    const el = mountRef.current;
    const w  = el.clientWidth  || 400;
    const h  = el.clientHeight || 300;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d1117);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(50, w / h, 0.001, 100);
    camera.position.set(0.3, 0.3, 0.8);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    el.appendChild(renderer.domElement);
    rendRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    ctrlRef.current = controls;

    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dir = new THREE.DirectionalLight(0xffffff, 1.2);
    dir.position.set(2, 4, 3);
    scene.add(dir);

    const grid = new THREE.GridHelper(2, 20, 0x222222, 0x222222);
    scene.add(grid);

    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      const w = el.clientWidth, h = el.clientHeight;
      if (w === 0 || h === 0) return;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    const resizeObserver = new ResizeObserver(onResize);
    resizeObserver.observe(el);

    return () => {
      cancelAnimationFrame(frameRef.current);
      resizeObserver.disconnect();
      controls.dispose();
      renderer.dispose();
      if (el.contains(renderer.domElement)) el.removeChild(renderer.domElement);
    };
  }, []);

  // Rebuild geometry on props change
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    if (antennaRef.current) {
      antennaRef.current.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
          if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
          else obj.material.dispose();
        }
      });
      scene.remove(antennaRef.current);
      antennaRef.current = null;
    }

    const builder = GEOMETRY_BUILDERS[antennaType];
    if (!builder) return;

    const matDef = MATERIALS.find(m => m.id === (conductor?.material ?? 'copper'));
    const color  = new THREE.Color(matDef?.color ?? '#b87333');
    const group  = builder(params, conductor, color);

    // Auto-scale group to fit in ~0.5 unit bounding box
    const box  = new THREE.Box3().setFromObject(group);
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    if (maxDim > 0) {
      const scale = 0.5 / maxDim;
      group.scale.setScalar(scale);
    }
    // Center the group
    box.setFromObject(group);
    const center = box.getCenter(new THREE.Vector3());
    group.position.sub(center);

    scene.add(group);
    antennaRef.current = group;
  }, [antennaType, params, conductor]);

  return (
    <div
      ref={mountRef}
      style={{ width: '100%', height: '100%', minHeight: '300px' }}
    />
  );
}
