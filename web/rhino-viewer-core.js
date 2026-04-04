export const RHINO_PERSPECTIVE_VIEW = {
  cameraLocation: [75827.83332287203, 106712.91762143679, 178833.77506231458],
  target: [-13160.295659804426, -84989.21938530335, -36990.56388282409],
  up: [-0.30082775285948155, -0.6480563615999264, 0.6996610717335787],
  lensLength: 28.469715868903915,
};

export const createRhinoViewerController = ({
  mountSelector,
  emptyStateSelector,
}) => {
  const mount = document.querySelector(mountSelector);
  const emptyState = document.querySelector(emptyStateSelector);

  let THREERef = null;
  let scene = null;
  let camera = null;
  let renderer = null;
  let controls = null;
  let loader = null;
  let currentModel = null;

  const encodePath = (path) => {
    const [pathname, search = ""] = path.split("?");
    const encodedPath = pathname
      .split("/")
      .map((segment) =>
        segment === "." || segment === ".." || segment === ""
          ? segment
          : encodeURIComponent(segment),
      )
      .join("/");

    return search ? `${encodedPath}?${search}` : encodedPath;
  };

  const clearCurrentModel = () => {
    if (!currentModel) {
      return;
    }

    scene.remove(currentModel);
    currentModel.traverse((child) => {
      if (child.geometry) {
        child.geometry.dispose();
      }

      if (Array.isArray(child.material)) {
        child.material.forEach((material) => material.dispose());
      } else if (child.material) {
        child.material.dispose();
      }
    });
    currentModel = null;
  };

  const lensLengthToFov = (lensLength) => {
    const filmWidth = 36;
    const radians = 2 * Math.atan(filmWidth / (2 * lensLength));
    return THREERef.MathUtils.radToDeg(radians);
  };

  const applyRhinoPerspectiveView = (view) => {
    const location = new THREERef.Vector3(...view.cameraLocation);
    const target = new THREERef.Vector3(...view.target);
    const up = new THREERef.Vector3(...view.up).normalize();
    const distance = location.distanceTo(target);

    camera.position.copy(location);
    camera.up.copy(up);
    camera.fov = lensLengthToFov(view.lensLength);
    camera.near = Math.max(distance / 1000, 0.1);
    camera.far = Math.max(distance * 10, 5000);
    camera.updateProjectionMatrix();
    camera.lookAt(target);

    controls.target.copy(target);
    controls.minDistance = Math.max(distance * 0.02, 10);
    controls.maxDistance = Math.max(distance * 4, 1000);
    controls.update();
  };

  const fitCameraToObject = (object) => {
    const box = new THREERef.Box3().setFromObject(object);
    const size = box.getSize(new THREERef.Vector3());
    const center = box.getCenter(new THREERef.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    const distance = maxDim * 1.25 || 50;

    camera.position.set(center.x + distance, center.y + distance * 0.7, center.z + distance);
    camera.near = Math.max(distance / 100, 0.1);
    camera.far = Math.max(distance * 20, 5000);
    camera.updateProjectionMatrix();

    controls.target.copy(center);
    controls.minDistance = Math.max(maxDim * 0.02, 10);
    controls.maxDistance = Math.max(maxDim * 8, 1000);
    controls.update();
  };

  const fitCameraToCurrentModel = () => {
    if (!currentModel) {
      return false;
    }

    fitCameraToObject(currentModel);
    return true;
  };

  const styleGhPreviewSubset = (namePrefix) => {
    let styledCount = 0;
    const palette = {
      GH_WEB_PREVIEW_tower_white_a: { r: 0.98, g: 0.97, b: 0.93, opacity: 1.0 },
      GH_WEB_PREVIEW_tower_pink_a: { r: 0.93, g: 0.63, b: 0.68, opacity: 1.0 },
      GH_WEB_PREVIEW_site_yellow: { r: 0.92, g: 0.92, b: 0.52, opacity: 0.9 },
      GH_WEB_PREVIEW_site_green: { r: 0.47, g: 0.95, b: 0.67, opacity: 0.9 },
      GH_WEB_PREVIEW_site_extra: { r: 0.62, g: 0.83, b: 1.0, opacity: 0.85 },
    };

    scene.traverse((child) => {
      if (!child) {
        return;
      }

      const name = child.name || child.userData?.attributes?.name || "";
      const attributes = child.userData?.attributes;
      const drawColor = attributes?.drawColor;

      if (!name.startsWith(namePrefix) || !child.material) {
        return;
      }

      const forcedStyle = palette[name] || null;

      const applyMaterial = (material) => {
        if (!material || typeof material !== "object") {
          return;
        }

        if (material.color) {
          if (forcedStyle) {
            material.color.setRGB(forcedStyle.r, forcedStyle.g, forcedStyle.b);
          } else if (drawColor) {
            material.color.setRGB(
              drawColor.r / 255,
              drawColor.g / 255,
              drawColor.b / 255,
            );
          } else {
            material.color.setRGB(0.82, 0.82, 0.82);
          }
        }

        const opacity = forcedStyle
          ? forcedStyle.opacity
          : ((drawColor?.a ?? 255) / 255);

        material.transparent = opacity < 0.999;
        material.opacity = opacity;
        material.depthWrite = material.opacity >= 0.999;
        if ("roughness" in material) {
          material.roughness = 0.92;
        }
        if ("metalness" in material) {
          material.metalness = 0.0;
        }
        material.needsUpdate = true;
      };

      if (Array.isArray(child.material)) {
        child.material = child.material.map((material) =>
          material?.clone ? material.clone() : material,
        );
        child.material.forEach(applyMaterial);
      } else {
        child.material = child.material?.clone ? child.material.clone() : child.material;
        applyMaterial(child.material);
      }

      styledCount += 1;
    });

    return styledCount;
  };

  const stylePublishedModel = () => {
    if (!currentModel) {
      return 0;
    }

    let styledCount = 0;
    const palette = {
      GH_WEB_PREVIEW_tower_white_a: { r: 0.98, g: 0.97, b: 0.93, opacity: 1.0 },
      GH_WEB_PREVIEW_tower_pink_a: { r: 0.93, g: 0.63, b: 0.68, opacity: 1.0 },
      GH_WEB_PREVIEW_site_yellow: { r: 0.92, g: 0.92, b: 0.52, opacity: 0.9 },
      GH_WEB_PREVIEW_site_green: { r: 0.47, g: 0.95, b: 0.67, opacity: 0.9 },
      GH_WEB_PREVIEW_site_extra: { r: 0.62, g: 0.83, b: 1.0, opacity: 0.85 },
    };

    currentModel.traverse((child) => {
      if (!child?.material) {
        return;
      }

      const name = child.name || child.userData?.attributes?.name || "";
      const drawColor = child.userData?.attributes?.drawColor || null;
      const forcedStyle = palette[name] || null;

      const applyMaterial = (material) => {
        if (!material || typeof material !== "object") {
          return;
        }

        if (material.color) {
          if (forcedStyle) {
            material.color.setRGB(forcedStyle.r, forcedStyle.g, forcedStyle.b);
          } else if (drawColor) {
            material.color.setRGB(
              drawColor.r / 255,
              drawColor.g / 255,
              drawColor.b / 255,
            );
          } else {
            material.color.setRGB(0.9, 0.9, 0.9);
          }
        }

        const opacity = forcedStyle
          ? forcedStyle.opacity
          : ((drawColor?.a ?? 255) / 255);

        material.transparent = opacity < 0.999;
        material.opacity = opacity;
        material.depthWrite = material.opacity >= 0.999;
        if ("roughness" in material) {
          material.roughness = 0.92;
        }
        if ("metalness" in material) {
          material.metalness = 0.0;
        }
        material.needsUpdate = true;
      };

      if (Array.isArray(child.material)) {
        child.material = child.material.map((material) =>
          material?.clone ? material.clone() : material,
        );
        child.material.forEach(applyMaterial);
      } else {
        child.material = child.material?.clone ? child.material.clone() : child.material;
        applyMaterial(child.material);
      }

      styledCount += 1;
    });

    return styledCount;
  };

  const fitCameraToNamedSubset = (namePrefix) => {
    const matches = [];
    scene.traverse((child) => {
      if (!child || !child.name) {
        return;
      }
      if (child.name.startsWith(namePrefix)) {
        matches.push(child);
      }
    });

    if (matches.length === 0) {
      return false;
    }

    const box = new THREERef.Box3();
    for (const match of matches) {
      box.expandByObject(match);
    }

    const size = box.getSize(new THREERef.Vector3());
    const center = box.getCenter(new THREERef.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    const distance = maxDim * 1.6 || 50;

    camera.position.set(center.x + distance, center.y - distance * 1.1, center.z + distance * 0.8);
    camera.near = Math.max(distance / 100, 0.1);
    camera.far = Math.max(distance * 20, 5000);
    camera.updateProjectionMatrix();
    controls.target.copy(center);
    controls.minDistance = Math.max(maxDim * 0.02, 10);
    controls.maxDistance = Math.max(maxDim * 8, 1000);
    controls.update();
    return true;
  };

  const loadModel = async (rawPath) => {
    if (!loader) {
      throw new Error("Viewer not initialized");
    }

    const encodedPath = encodePath(rawPath);

    return new Promise((resolve, reject) => {
      loader.load(
        encodedPath,
        (object) => {
          clearCurrentModel();
          currentModel = object;
          scene.add(object);
          emptyState.hidden = true;
          fitCameraToObject(object);
          resolve(object);
        },
        undefined,
        (error) => {
          emptyState.hidden = false;
          reject(error);
        },
      );
    });
  };

  const init = async () => {
    const THREE = await import("./vendor/three/build/three.module.js");
    const { OrbitControls } = await import(
      "./vendor/three/examples/jsm/controls/OrbitControls.js"
    );
    const { Rhino3dmLoader } = await import(
      "./vendor/three/examples/jsm/loaders/3DMLoader.js"
    );

    THREERef = THREE;

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    mount.appendChild(renderer.domElement);

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf7f2e9);

    camera = new THREE.PerspectiveCamera(
      45,
      mount.clientWidth / mount.clientHeight,
      0.1,
      5000,
    );
    camera.position.set(40, 40, 40);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(0, 0, 0);

    scene.add(new THREE.HemisphereLight(0xffffff, 0xb6b6b6, 1.3));
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.4);
    directionalLight.position.set(20, 30, 10);
    scene.add(directionalLight);

    const grid = new THREE.GridHelper(200, 20, 0xb85c38, 0xd7d1c6);
    grid.position.y = -0.01;
    scene.add(grid);

    loader = new Rhino3dmLoader();
    loader.setLibraryPath("./vendor/rhino3dm/");

    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
      window.requestAnimationFrame(animate);
    };

    window.addEventListener("resize", () => {
      const width = mount.clientWidth;
      const height = mount.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    });

    animate();
  };

  return {
    init,
    loadModel,
    applyRhinoPerspectiveView,
    fitCameraToNamedSubset,
    fitCameraToCurrentModel,
    styleGhPreviewSubset,
    stylePublishedModel,
  };
};
