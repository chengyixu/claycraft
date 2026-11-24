# Clay game assets

Use the character lineup for proportions and the brief for silhouette, equipment and palette. Work at the game's normal camera distance. Build the asset with meshes, vertex colors and matte materials. The following recipes run locally with Blender 5.0.1 and its bundled glTF exporter.

## Build the starters

From the installed `claycraft` skill directory, run:

```sh
blender -b --factory-startup --python-exit-code 1 -P scripts/build_asset.py -- --asset courier --output game/assets/courier.glb
blender -b --factory-startup --python-exit-code 1 -P scripts/build_asset.py -- --asset mushroom --output game/assets/mushroom.glb
```

On macOS the executable may be `/Applications/Blender.app/Contents/MacOS/Blender`. Use a fresh output path to keep an earlier export. Each GLB is self-contained. Both use meters, a ground-level origin, +Y up and +Z forward in glTF. The courier is about 1.62 m tall including its ears. Each asset uses one mesh and one vertex-colored material. The courier has one six-joint skin with rigidly attached clay pieces.

| Clip | Duration | Playback |
| --- | --- | --- |
| `Idle` | 2 s | Loop while standing. |
| `Walk` | 1 s | Loop while moving. |
| `Run` | ⅔ s | Loop while sprinting. |
| `Jump` | 1 s | Play once on takeoff. The clip supplies anticipation, tuck and recovery. Drive the jump arc with game physics. |
| `Wave` | 1.5 s | Play once on interaction. |

Move and turn the actor's parent from game input. All five clips keep the model origin fixed. Set looping or one-shot behavior in the engine. For example, given a loaded Three.js `gltf`, start locomotion with:

```js
const mixer = new THREE.AnimationMixer(gltf.scene);
const actions = new Map(gltf.animations.map(clip => [clip.name, mixer.clipAction(clip)]));
actions.get("Walk").play();
// In the game loop, call mixer.update(deltaSeconds).
```

For a one-shot, use `setLoop(THREE.LoopOnce, 1)`, `reset()` and `play()` on the action. Fade out the previous action and return to locomotion when the mixer emits `finished`. Use the gameplay state to decide which locomotion clip to resume.

## Sculpt another subject

Copy the script into the game's asset source directory. Replace the piece recipe in `courier()` or `mushroom()` with the requested subject. Each `clay_piece` takes a joint (or `None` for a prop), label, center, three radii, palette color and optional tilt in degrees. The recipe uses Blender coordinates with Z up and the face toward −Y. Place the lowest contact patch at ground level. For holes, flat panels or carved edges, substitute an appropriate mesh and give it the same `Clay` vertex-color attribute before joining.

Place joint pivots in `JOINTS` at the actual shoulders, hips and neck. Attach accessories to the part that carries them. For wings, tails or a different body plan, add the corresponding joints and groups. Author the requested action in `pose()` and register its name and length in `animate()`. The starter bones point up in rest pose; their local Y axis is vertical. Set the first and last pose equal for loops. Let the game controller own travel distance, collision shapes and interaction timing.

After export, load the GLB in the target engine. Play each clip, check feet against the ground, view the silhouette from the game camera, and transition between movement and one-shots. If delivering sprites, render the actual poses with an orthographic camera, fixed lighting and a shared foot pivot. Check frame timing and trim repeated loop endpoints before packing the atlas.

The source repository includes both example GLBs and a playable `examples/playground.html`. To run it from a checkout, install Three.js at the repository root (`npm install --no-save --package-lock=false three@0.185.1`), run `python3 -m http.server --bind 127.0.0.1`, and open `/examples/playground.html` on that server. Run `node tests/playback.mjs examples/courier.glb examples/mushroom.glb` to verify the geometry and baked poses. Pass fresh export paths to the same check after editing the recipes.
