# ClayCraft

[ClayCraft](skills/claycraft/SKILL.md) is an agent skill for making handmade miniature clay assets. Its Blender workflow builds colored meshes and animation clips locally. It needs no image generator or API key.

| Game asset | What you get |
| --- | --- |
| [Woodland courier](examples/courier.glb) | A rabbit-hooded figure with a satchel, a six-joint rig, and `Idle`, `Walk`, `Run`, `Jump` and `Wave` clips. |
| [Spotted mushroom](examples/mushroom.glb) | A static prop with the same palette, scale and material treatment. |

Import the GLBs directly into a game. The courier animates in place so your controller can set its speed, direction and jump height.

To play the example from the repository root:

```sh
npm install --no-save --package-lock=false three@0.185.1
python3 -m http.server --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/examples/playground.html`. Use the arrow keys to move, hold Shift to run, press Space to jump, or select an individual clip.

Follow [Game assets](skills/claycraft/references/game-assets.md) to rebuild the examples or adapt the shapes, palette, joints and actions to a different brief.
