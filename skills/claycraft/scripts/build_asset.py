"""Run with Blender in background mode. See references/game-assets.md."""

import argparse
import math
from pathlib import Path
import sys
import tempfile

import bpy
import numpy as np
from mathutils import Vector, noise
from mathutils.bvhtree import BVHTree


PALETTE = {
    "cream": (0.69, 0.43, 0.245),
    "sage": (0.19, 0.257, 0.115),
    "moss": (0.079, 0.13, 0.060),
    "wheat": (0.70, 0.50, 0.279),
    "linen": (0.51, 0.34, 0.184),
    "hair": (0.194, 0.081, 0.028),
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


def finish(piece, joint, color):
    for face in piece.data.polygons:
        face.use_smooth = True
    colors = piece.data.color_attributes.new(name="Clay", type="FLOAT_COLOR", domain="POINT")
    for vertex, sample in zip(piece.data.vertices, colors.data):
        value = noise.noise_vector(vertex.co * 27)[0]
        variation = 0.95 + 0.13 * value
        sample.color = (*[channel * variation for channel in PALETTE[color]], 1)
    if joint:
        group = piece.vertex_groups.new(name=joint)
        group.add(list(range(len(piece.data.vertices))), 1, "REPLACE")
    return piece


def clay_piece(joint, name, center, radii, color, tilt=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=18, location=center)
    piece = bpy.context.object
    piece.name = name
    for vertex in piece.data.vertices:
        horizontal, depth, height = vertex.co
        ripple = 1 + 0.017 * math.sin(5 * horizontal + 3 * height) * math.cos(4 * depth - height)
        vertex.co = tuple(value * scale * ripple for value, scale in zip(vertex.co, radii))
    piece.rotation_euler.y = math.radians(tilt)
    return finish(piece, joint, color)


def thrown(joint, name, rings, color, folds=0, drape=0):
    """Shape a closed clay shell from offset elliptical cross sections."""
    count = 48
    points, faces = [], []
    for level, (height, width, depth, offset_x, offset_y) in enumerate(rings):
        for step in range(count):
            angle = math.tau * step / count
            scallop = math.cos(7 * angle + 0.35 * level)
            radius = 1 + folds * scallop + 0.012 * math.sin(3 * angle + height * 2)
            hem = drape * (0.75 * math.sin(angle) + 0.25 * scallop)
            points.append((offset_x + width * radius * math.cos(angle),
                           offset_y + depth * radius * math.sin(angle),
                           height + hem * (1 - level / (len(rings) - 1))))
            if level:
                bottom = (level - 1) * count + step
                adjacent = (level - 1) * count + (step + 1) % count
                faces.append((bottom, adjacent, adjacent + count, bottom + count))
    faces.extend([tuple(reversed(range(count))), tuple(range(len(points) - count, len(points)))])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], faces)
    mesh.update()
    piece = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(piece)
    uv = mesh.uv_layers.new()
    for face in mesh.polygons:
        steps = [mesh.loops[index].vertex_index % count for index in face.loop_indices]
        seam = len(steps) == 4 and max(steps) - min(steps) > 1
        for index, step in zip(face.loop_indices, steps):
            vertex = mesh.loops[index].vertex_index
            uv.data[index].uv = ((count if seam and step == 0 else step) / count,
                                 (vertex // count) / (len(rings) - 1))
    return finish(piece, joint, color)


def strand(joint, name, points, width, color):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 5
    curve.bevel_depth = width
    curve.bevel_resolution = 2
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for knot, position in zip(spline.bezier_points, points):
        knot.co = position
        knot.handle_left_type = knot.handle_right_type = "AUTO"
    spline.bezier_points[0].radius = spline.bezier_points[-1].radius = 0.42
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(obj, do_unlink=True)
    piece = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(piece)
    return finish(piece, joint, color)


def courier():
    pieces = []

    def add(*args):
        pieces.append(clay_piece(*args))

    def shell(joint, name, rings, color, **kwargs):
        pieces.append(thrown(joint, name, rings, color, **kwargs))

    def line(joint, name, points, width, color):
        pieces.append(strand(joint, name, points, width, color))

    shell("Body", "Linen tunic", [(0.249,.230,.173,0,0),(.264,.248,.191,0,0),
          (.30,.252,.193,0,0),(.51,.219,.175,0,0),(.72,.213,.16,0,0),(.81,.14,.12,0,0)], "linen", folds=.045, drape=.013)
    shell("Body", "Travel cape", [(.49,.293,.188,0,.01),(.507,.310,.203,0,.01),
          (.548,.307,.205,0,.01),(.67,.278,.188,0,0),(.78,.244,.16,0,0),
          (.834,.184,.139,0,0),(.843,.148,.125,0,0)], "sage", folds=.072, drape=-.115)
    add("Head", "Hair at nape", (0,.018,1.035), (.296,.232,.245), "hair")
    add("Head", "Face", (0,-.074,1.015), (.263,.204,.24), "cream")
    for index, (angle, reach, sweep) in enumerate([(-1.52,.105,-.021),(-1.13,.12,-.035),(-.73,.092,-.045),
              (-.37,.086,-.035),(.04,.093,.049),(.46,.080,.048),(.89,.095,.046),(1.28,.127,.019)]):
        root_x = .270 * math.sin(angle)
        root_y = -.016 - .218 * math.cos(angle)
        top = 1.166 + .018 * math.cos(angle)
        rings = []
        for level, width in [(0,.006),(.20,.033),(.48,.052),(.75,.055),(1,.035)]:
            rings.append((top-(1-level)*reach,width,width*.65,
                          root_x+sweep*(1-level)**1.5,root_y-.018*math.sin(level*math.pi)))
        shell("Head",f"Swept lock {index}",rings,"hair")
    shell("Head", "Slouched leaf cap", [(1.117,.290,.229,0,.013),(1.137,.316,.259,0,.012),
          (1.195,.322,.26,0,.015),(1.256,.29,.241,-.012,.018),
          (1.34,.241,.212,-.039,.025),(1.432,.162,.151,-.087,.028),
          (1.489,.111,.100,-.149,.019),(1.511,.077,.070,-.212,.015),
          (1.496,.050,.051,-.264,.012),(1.453,.024,.022,-.296,.010),
          (1.436,.007,.009,-.299,.010)], "moss", folds=.042, drape=.026)
    shell("Head", "Rolled hat band", [(1.148,.314,.257,0,.012),(1.158,.336,.277,0,.012),
          (1.181,.341,.280,0,.012),(1.201,.335,.274,0,.015),(1.212,.313,.255,0,.015)], "sage", drape=.024)
    add("Head","Leaf pin",(.206,-.203,1.247),(.044,.016,.098),"ochre",28)
    line("Head","Leaf midrib",[(.163,-.219,1.171),(.206,-.228,1.245),(.247,-.209,1.315)],.006,"wheat")
    add("Head", "Pinched nose", (0,-.271,1.008), (.033,.027,.023), "cream")
    for side, sign in (("L", 1), ("R", -1)):
        add("Head", "Eye", (sign*.094,-.265,1.034), (.016,.010,.040), "ink")
        add("Head", "Ear", (sign*.251,-.064,1.022), (.050,.036,.065), "cream",sign*16)
        add("Arm." + side, "Sleeve", (sign * 0.263, 0, 0.639), (0.091, 0.095, 0.16), "moss", -sign * 12)
        add("Arm." + side, "Mitten", (sign * 0.289, -0.016, 0.50), (0.077, 0.080, 0.089), "cream")
        add("Leg." + side, "Leg", (sign * 0.13, 0, 0.20), (0.087, 0.092, 0.129), "ochre")
        foot = sign*.126
        shell("Leg."+side,"Boot with flattened sole",[(.001,.091,.133,foot,-.033),(.018,.107,.151,foot,-.04),
              (.060,.111,.149,foot,-.04),(.097,.103,.133,foot,-.033),(.127,.083,.092,foot,0),
              (.164,.085,.091,foot,0),(.17,.076,.080,foot,0)],"cocoa")
        for index in range(2):
            height=.094+index*.024
            line("Leg."+side,"Boot lace",[(foot-.041,-.107+index*.012,height),(foot,-.121+index*.015,height+.004),
                 (foot+.042,-.104+index*.014,height+.008)],.006,"linen")
    add("Body", "Kerchief", (0,-.015,.816), (.198,.165,.058), "brick", -5)
    add("Body", "Scarf end", (-.123,-.168,.734), (.051,.026,.096), "brick", -24)
    line("Body","Leather sling",[(-.207,-.089,.781),(-.156,-.164,.713),(-.022,-.194,.598),(.117,-.197,.485),(.226,-.143,.421)],.022,"cocoa")
    shell("Body","Mail satchel",[(.329,.103,.040,.140,-.177),(.341,.124,.055,.14,-.18),
          (.385,.128,.058,.14,-.180),(.460,.123,.056,.14,-.180),(.476,.115,.046,.14,-.180)],"brick")
    add("Body","Bag flap",(.140,-.223,.439),(.125,.030,.056),"cocoa",-4)
    add("Body","Wax seal",(.143,-.253,.422),(.022,.009,.022),"ochre")
    line("Body","Envelope flap",[(.063,-.218,.496),(.129,-.223,.470),(.198,-.217,.505)],.005,"linen")
    add("Body","Folded letter",(.132,-.201,.483),(.089,.017,.032),"wheat",-4)
    for index in range(15):
        angle = math.pi + .26 + index * .187
        horizontal, depth = math.cos(angle), math.sin(angle)
        center = (.335*horizontal,.012+.276*depth,1.169+.009*depth)
        line("Head","Hand-pressed band stitch",[(center[0]-.008*depth,center[1]+.008*horizontal,center[2]-.004),
              (center[0]+.008*depth,center[1]-.008*horizontal,center[2]+.004)],.0035,"linen")
    line("Body","Placket",[(-.079,-.161,.265),(-.070,-.184,.37),(-.060,-.176,.475)],.006,"cocoa")
    for height in (.304,.365,.427):
        add("Body","Wooden tunic button",(-.047,-.187,height),(.011,.006,.012),"ochre")
    return pieces


def mushroom():
    pieces = [
        thrown(None, "Bent stem", [(.001,.064,.061,-.018,0),(.024,.082,.079,-.018,0),
               (.067,.070,.068,-.019,0),(.17,.049,.046,-.008,0),(.25,.046,.048,.019,0),
               (.30,.069,.067,.032,0)], "wheat", folds=.06),
        thrown(None, "Gilled underside", [(.26,.040,.041,.026,0),(.268,.144,.137,.027,0),
               (.287,.206,.188,.026,0),(.302,.209,.19,.026,0)], "linen", folds=.02),
        thrown(None, "Fluted cap", [(.285,.185,.172,.028,0),(.29,.212,.192,.027,0),
               (.302,.220,.198,.023,0),(.331,.199,.179,.018,0),(.392,.128,.115,.009,0),
               (.423,.058,.054,-.004,0),(.43,.012,.012,-.008,0)], "brick", folds=.028, drape=.016),
    ]
    for index in range(18):
        angle = index * 2.39996
        radial = .17 * math.sqrt((index + .4) / 18)
        width = .014 + .008 * math.sin(index * 1.93)
        horizontal, depth = radial*math.cos(angle), radial*.9*math.sin(angle)
        height = float(np.interp(radial,[0,.052,.117,.193,.218],[.432,.425,.394,.334,.302]))
        pieces.append(clay_piece(None, "Cap fleck", (horizontal+.006,depth,height),
                                 (width,width*.8,.010),"wheat"))
    return pieces


def clay_surface(material, shader):
    size = 512
    random = np.random.default_rng(311)
    grain = random.standard_normal((size, size))
    frequency = np.fft.fftfreq(size)
    spectrum = frequency[:, None] ** 2 + frequency[None, :] ** 2
    transform = np.fft.fft2(grain)

    def softened(scale):
        blurred = np.fft.ifft2(transform * np.exp(-spectrum * scale**2)).real
        return blurred / blurred.std()

    fine = softened(7)
    pressed = softened(31)
    height = .19 * fine + .72 * pressed - 1.7 * np.maximum(fine - .85, 0)**1.6
    slopes = [(np.roll(height, 1, axis) - np.roll(height, -1, axis)) * .52 for axis in (1, 0)]
    normals = np.stack([*slopes, np.ones_like(height)], axis=-1)
    normals /= np.linalg.norm(normals, axis=-1, keepdims=True)
    pixels = np.ones((size, size, 4), dtype=np.float32)
    pixels[:, :, :3] = .5 + .5 * normals
    image = bpy.data.images.new("Pressed stoneware grain", width=size, height=size, alpha=False)
    image.colorspace_settings.name = "Non-Color"
    image.pixels.foreach_set(pixels.ravel())
    image.pack()
    tree = material.node_tree
    texture = tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    relief = tree.nodes.new("ShaderNodeNormalMap")
    relief.inputs["Strength"].default_value = .24
    tree.links.new(texture.outputs["Color"], relief.inputs["Color"])
    tree.links.new(relief.outputs["Normal"], shader.inputs["Normal"])


def join_clay(pieces, name):
    bpy.ops.object.select_all(action="DESELECT")
    for piece in pieces:
        piece.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    mesh = bpy.context.object
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    mesh.name = name
    surface = mesh.data
    tree = BVHTree.FromPolygons([vertex.co for vertex in surface.vertices],
                                [face.vertices[:] for face in surface.polygons])
    colors = surface.color_attributes["Clay"].data
    directions = []
    for index in range(24):
        vertical = (index + .5) / 24
        angle = index * 2.39996323
        radius = math.sqrt(1 - vertical**2)
        directions.append(Vector((radius*math.cos(angle),radius*math.sin(angle),vertical)))
    for vertex, sample in zip(surface.vertices, colors):
        normal = vertex.normal
        rotation = normal.to_track_quat("Z","Y")
        start = vertex.co + normal * .001
        shelter = 0
        for direction in directions:
            distance = tree.ray_cast(start, rotation @ direction, .085)[3]
            if distance is not None:
                shelter += 1 - distance / .085
        shade = 1 - .68 * shelter / len(directions)
        sample.color = (*[channel * shade for channel in sample.color[:3]],1)
    material = bpy.data.materials.new("Unglazed clay")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.93
    color = material.node_tree.nodes.new("ShaderNodeVertexColor")
    color.layer_name = "Clay"
    material.node_tree.links.new(color.outputs["Color"], shader.inputs["Base Color"])
    clay_surface(material, shader)
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
        angles["Head"][0] = 3 * swing
        angles["Head"][1] = 4 * (1 - math.cos(turn))
        angles["Arm.L"][0] = 2.5 * swing
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
