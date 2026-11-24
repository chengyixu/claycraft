// From a checkout with Three.js installed, pass the two freshly exported GLBs.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { AnimationMixer, Box3, LoopOnce, Texture, Vector3 } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const expected = { Idle: 2, Walk: 1, Run: 2 / 3, Jump: 1, Wave: 1.5 };
const [courierPath, mushroomPath] = process.argv.slice(2);

async function load(path) {
  const bytes = await readFile(path);
  const loader = new GLTFLoader();
  loader.register(parser => ({
    name: 'EmbeddedPngCheck',
    async loadTexture(index) {
      const image = parser.json.images[parser.json.textures[index].source];
      assert.equal(image.mimeType, 'image/png');
      const data = Buffer.from(await parser.getDependency('bufferView', image.bufferView));
      assert.equal(data.subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
      assert.ok(data.readUInt32BE(16) >= 256 && data.readUInt32BE(20) >= 256);
      return new Texture();
    }
  }));
  const model = await loader.parseAsync(
    bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), ''
  );
  const meshes = [];
  model.scene.traverse(node => { if (node.isMesh) meshes.push(node); });
  assert.equal(meshes.length, 1);
  const [mesh] = meshes;
  assert.ok(mesh.material.vertexColors);
  assert.ok(mesh.material.normalMap, 'portable relief material');
  for (const attr of Object.values(mesh.geometry.attributes)) {
    assert.ok(attr.array.every(Number.isFinite), attr.name);
  }
  for (let index = 0; index < mesh.geometry.attributes.normal.count; index++) {
    const normal = new Vector3().fromBufferAttribute(mesh.geometry.attributes.normal, index);
    assert.ok(Math.abs(normal.length() - 1) < 0.002, 'unit normals');
  }
  const bounds = new Box3().setFromObject(model.scene, true);
  assert.ok(Math.abs(bounds.min.y) < 0.002, 'ground contact at rest');
  return { ...model, mesh };
}

const courier = await load(courierPath);
const prop = await load(mushroomPath);
assert.equal(prop.animations.length, 0);
assert.equal(prop.mesh.isSkinnedMesh, undefined);
assert.equal(courier.mesh.skeleton.bones.length, 6);
assert.deepEqual(courier.animations.map(clip => clip.name).sort(), Object.keys(expected).sort());
const mixer = new AnimationMixer(courier.scene);

function vertices() {
  courier.scene.updateMatrixWorld(true);
  const positions = courier.mesh.geometry.attributes.position;
  return Array.from({ length: positions.count }, (_, index) =>
    courier.mesh.getVertexPosition(index, new Vector3()));
}

function maxDisplacement(start, end) {
  return Math.max(...start.map((point, index) => point.distanceTo(end[index])));
}

for (const clip of courier.animations) {
  assert.ok(Math.abs(clip.duration - expected[clip.name]) < 1e-6);
  const action = mixer.clipAction(clip);
  action.setLoop(LoopOnce, 1);
  action.clampWhenFinished = true;
  action.reset().play();
  mixer.update(0);
  const start = vertices();
  mixer.update(clip.duration * 0.25);
  assert.ok(maxDisplacement(start, vertices()) > 0.005, `${clip.name} moves the skin`);
  mixer.update(clip.duration * 0.75);
  assert.ok(maxDisplacement(start, vertices()) < 0.0001, `${clip.name} ends at its first pose`);
  assert.equal(courier.mesh.parent.position.length(), 0, 'stationary actor root');
  action.stop();
}
console.log('Both assets loaded. All five clips moved the skin and returned to their first pose.');
