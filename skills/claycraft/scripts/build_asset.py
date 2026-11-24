"""Run with Blender in background mode. See references/game-assets.md."""

import argparse
import math
from pathlib import Path
import sys
import tempfile

import bpy


PALETTE = {
    "cream": (0.86, 0.65, 0.43),
    "sage": (0.27, 0.41, 0.27),
    "moss": (0.14, 0.23, 0.14),
    "ochre": (0.73, 0.37, 0.10),
    "brick": (0.53, 0.17, 0.09),
    "pink": (0.78, 0.39, 0.28),
    "cocoa": (0.19, 0.10, 0.057),
    "ink": (0.046, 0.030, 0.027),
}
JOINTS = {
    "Body": (None, (0, 0, 0.45)),
    "Head": ("Body", (0, 0, 0.84)),
    "Arm.L": ("Body", (0.23, 0, 0.76)),
    "Arm.R": ("Body", (-0.23, 0, 0.76)),
    "Leg.L": ("Body", (0.13, 0, 0.29)),
    "Leg.R": ("Body", (-0.13, 0, 0.29)),
}


def clay_piece(joint, name, center, radii, color, tilt=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=center)
    piece = bpy.context.object
    piece.name = name
    for vertex in piece.data.vertices:
        horizontal, depth, height = vertex.co
        ripple = 1 + 0.017 * math.sin(5 * horizontal + 3 * height) * math.cos(4 * depth - height)
        vertex.co = tuple(value * scale * ripple for value, scale in zip(vertex.co, radii))
    piece.rotation_euler.y = math.radians(tilt)
    for face in piece.data.polygons:
        face.use_smooth = True
    colors = piece.data.color_attributes.new(name="Clay", type="FLOAT_COLOR", domain="POINT")
    for vertex, sample in zip(piece.data.vertices, colors.data):
        variation = 1 + 0.025 * math.sin(vertex.index * 13.79)
        sample.color = (*[value * variation for value in PALETTE[color]], 1)
    if joint:
        group = piece.vertex_groups.new(name=joint)
        group.add(list(range(len(piece.data.vertices))), 1, "REPLACE")
    return piece


def courier():
    pieces = []

    def add(*args):
        pieces.append(clay_piece(*args))

    add("Body", "Smock", (0, 0, 0.57), (0.278, 0.205, 0.33), "sage")
    add("Head", "Hood", (0, 0, 1.10), (0.344, 0.27, 0.312), "sage")
    add("Head", "Face", (0, -0.156, 1.075), (0.282, 0.179, 0.239), "cream")
    add("Head", "Button nose", (0, -0.333, 1.04), (0.034, 0.018, 0.024), "cocoa")
    for side, sign in (("L", 1), ("R", -1)):
        ear_x = sign * 0.152
        lean = sign * (12 if sign == 1 else 20)
        add("Head", "Hood ear", (ear_x, 0, 1.43), (0.078, 0.062, 0.19), "sage", lean)
        add("Head", "Inset", (ear_x, -0.049, 1.45), (0.036, 0.021, 0.123), "pink", lean)
        add("Head", "Eye", (sign * 0.102, -0.322, 1.095), (0.020, 0.013, 0.042), "ink")
        add("Head", "Cheek", (sign * 0.17, -0.297, 1.035), (0.043, 0.012, 0.020), "pink")
        add("Arm." + side, "Sleeve", (sign * 0.263, 0, 0.639), (0.091, 0.095, 0.16), "moss", -sign * 12)
        add("Arm." + side, "Mitten", (sign * 0.289, -0.016, 0.50), (0.077, 0.080, 0.089), "cream")
        add("Leg." + side, "Leg", (sign * 0.13, 0, 0.20), (0.087, 0.092, 0.129), "ochre")
        add("Leg." + side, "Boot", (sign * 0.13, -0.031, 0.089), (0.110, 0.146, 0.089), "cocoa")
    add("Body", "Kerchief", (0, -0.015, 0.822), (0.222, 0.204, 0.062), "brick", -5)
    add("Body", "Strap", (-0.010, -0.187, 0.585), (0.031, 0.029, 0.276), "cocoa", -30)
    add("Body", "Pouch", (0.130, -0.178, 0.410), (0.114, 0.063, 0.089), "ochre", -8)
    add("Body", "Flap", (0.130, -0.224, 0.442), (0.110, 0.033, 0.055), "brick", -8)
    add("Body", "Clasp", (0.130, -0.257, 0.433), (0.016, 0.008, 0.016), "cream")
    return pieces


def mushroom():
    specs = [
        ("Stem", (0, 0, 0.171), (0.096, 0.10, 0.172), "cream"),
        ("Gills", (0.013, 0, 0.296), (0.222, 0.202, 0.055), "ochre"),
        ("Cap", (0.013, 0, 0.334), (0.225, 0.205, 0.114), "brick"),
    ]
    for index, (horizontal, depth) in enumerate(((-0.10, -0.09), (0.09, -0.12), (0.12, 0.07), (-0.06, 0.10), (0, 0))):
        height = 0.334 + 0.114 * math.sqrt(1 - ((horizontal - 0.013) / 0.225) ** 2 - (depth / 0.205) ** 2)
        specs.append((f"Pressed spot {index}", (horizontal, depth, height), (0.034, 0.030, 0.012), "cream"))
    return [clay_piece(None, *spec) for spec in specs]


def join_clay(pieces, name):
    bpy.ops.object.select_all(action="DESELECT")
    for piece in pieces:
        piece.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    mesh = bpy.context.object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    mesh.name = name
    material = bpy.data.materials.new("Unglazed clay")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.93
    color = material.node_tree.nodes.new("ShaderNodeVertexColor")
    color.layer_name = "Clay"
    material.node_tree.links.new(color.outputs["Color"], shader.inputs["Base Color"])
    mesh.data.materials.append(material)
    return mesh


def add_rig(mesh):
    skeleton = bpy.data.armatures.new("Courier joints")
    rig = bpy.data.objects.new("Courier", skeleton)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for name, (parent, center) in JOINTS.items():
        bone = skeleton.edit_bones.new(name)
        bone.head = center
        bone.tail = (center[0], center[1], center[2] + 0.10)
        if parent:
            bone.parent = skeleton.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh.parent = rig
    mesh.modifiers.new("Clay joints", "ARMATURE").object = rig
    return rig


def pose(clip, phase):
    turn = 2 * math.pi * phase
    swing = math.sin(turn)
    angles = {name: [0, 0, 0] for name in JOINTS}
    lift = 0
    if clip == "Idle":
        lift = 0.009 * (1 - math.cos(turn))
        angles["Head"][0] = 3 * swing
    elif clip in ("Walk", "Run"):
        stride = 31 if clip == "Walk" else 55
        lift = (0.018 if clip == "Walk" else 0.045) * swing ** 2
        angles["Body"][0] = 0 if clip == "Walk" else 9
        for side, sign in (("L", 1), ("R", -1)):
            angles["Leg." + side][0] = sign * stride * swing
            angles["Arm." + side][0] = -sign * stride * 0.78 * swing
    elif clip == "Jump":
        keys = [(0, 0, 0), (0.17, -0.035, 18), (0.33, 0.045, -24),
                (0.56, 0.10, -52), (0.78, 0.045, -18), (0.89, -0.025, 15), (1, 0, 0)]
        for (start, low, first), (end, high, last) in zip(keys, keys[1:]):
            if start <= phase <= end:
                blend = (phase - start) / (end - start)
                lift = low + blend * (high - low)
                bend = first + blend * (last - first)
                angles["Leg.L"][0] = bend
                angles["Leg.R"][0] = bend * 0.8
                angles["Arm.L"][2] = abs(bend)
                angles["Arm.R"][2] = -abs(bend)
                break
    elif clip == "Wave":
        raised = min(1, phase * 5, (1 - phase) * 5)
        angles["Arm.L"][2] = raised * (128 + 14 * math.sin(3 * turn))
        angles["Head"][2] = 7 * raised
    return lift, angles


def animate(rig):
    rig.animation_data_create()
    for clip, frames in (("Idle", 48), ("Walk", 24), ("Run", 16), ("Jump", 24), ("Wave", 36)):
        action = bpy.data.actions.new(clip)
        action.use_fake_user = True
        rig.animation_data.action = action
        for frame in range(frames + 1):
            lift, angles = pose(clip, frame / frames)
            body = rig.pose.bones["Body"]
            body.location.y = lift
            body.keyframe_insert(data_path="location", frame=frame)
            for name, degrees in angles.items():
                bone = rig.pose.bones[name]
                bone.rotation_mode = "XYZ"
                bone.rotation_euler = tuple(math.radians(angle) for angle in degrees)
                bone.keyframe_insert(data_path="rotation_euler", frame=frame)
    rig.animation_data.action = bpy.data.actions["Idle"]
    bpy.context.scene.frame_set(0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", required=True, choices=("courier", "mushroom"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if args.output.suffix.lower() != ".glb":
        parser.error("--output must end in .glb")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 24
    if args.asset == "courier":
        animate(add_rig(join_clay(courier(), "Courier clay")))
    else:
        join_clay(mushroom(), "Mushroom")
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        staged = Path(temp) / output.name
        result = bpy.ops.export_scene.gltf(
            filepath=str(staged), export_format="GLB", export_animations=args.asset == "courier",
            export_animation_mode="ACTIONS", export_frame_range=False,
        )
        if "FINISHED" not in result:
            raise RuntimeError("glTF export failed")
        staged.replace(output)


if __name__ == "__main__":
    main()
