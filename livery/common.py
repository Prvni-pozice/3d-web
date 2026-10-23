# Společné funkce pro livery skripty (Blender 4.2, spouštět přes blender -b -P)
import bpy, math, mathutils

def load(src):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    for o in list(bpy.data.objects):
        if o.name.startswith("Icosphere"):
            bpy.data.objects.remove(o)
    # Sketchfab má meshe (kola, třmeny) zavěšené na kostech _rootJoint; export z Blenderu
    # pak třmeny posune do počátku. Model není animovaný → meshe odvěsit se zachováním
    # světové polohy a kostru i prázdné uzly smazat.
    bpy.context.view_layer.update()
    for o in bpy.data.objects:
        if o.type == 'MESH':
            mw = o.matrix_world.copy()
            for m in list(o.modifiers):
                if m.type == 'ARMATURE': o.modifiers.remove(m)
            o.parent = None
            o.matrix_world = mw
    for o in list(bpy.data.objects):
        if o.type != 'MESH':
            bpy.data.objects.remove(o)

def scale_up(f=100.0):
    """Model je v jednotkách 0,01 m — pro render ho zvětši na metry (export z toho nedělat)."""
    S = mathutils.Matrix.Scale(f, 4)
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.matrix_world = S @ o.matrix_world
    bpy.context.view_layer.update()

VIEWS = {
    "front34": (5.5, -6.5, 2.5), "front34R": (-6.0, -6.5, 1.4), "nose": (-1.2, -4.2, 2.2), "photo5": (-5.2, -7.4, 2.0), "rear34": (-5.5, 6.5, 2.5), "side": (9, 0, 1.0),
    "sideL": (-9, 0, 1.0), "top": (0.01, 0, 11), "front": (0, -10, 1.2), "rear": (0, 10, 1.6),
}

def setup_render(res=(900, 560), samples=24, bg=(0.8, 0.8, 0.82)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = res
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bgn = w.node_tree.nodes["Background"]; bgn.inputs[0].default_value = (*bg, 1); bgn.inputs[1].default_value = 1.0
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 3; sun.rotation_euler = (math.radians(40), 0, math.radians(30))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 50
    return cam

def render_views(cam, out, names, tgt=(0, 0, 0.55)):
    sc = bpy.context.scene; t = mathutils.Vector(tgt)
    for name in names:
        p = mathutils.Vector(VIEWS[name]); cam.location = p
        cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f"{out}_{name}.png"
        bpy.ops.render.render(write_still=True)

# Ortografické pohledy: (pozice kamery, osa obrazu vpravo, osa obrazu nahoru)
# Auto: x = šířka (+x = levý bok auta), y = délka (předek na −y), z = nahoru
ORTHO = {
    "oside":  ((10, 0, 0.6), "y", "z"),     # levý bok, předek vlevo
    "osideR": ((-10, 0, 0.6), "-y", "z"),   # pravý bok, předek vpravo
    "otop":   ((0, 0, 10), "-y", "x"),      # shora, předek vpravo... viz render_ortho
    "ofront": ((0, -10, 0.6), "x", "z"),    # zepředu (levý bok auta vpravo)
}
ORTHO_SCALE = 5.0
ORTHO_RES = (1500, 1500)

def render_ortho(cam, out, names):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = ORTHO_RES
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = ORTHO_SCALE
    for name in names:
        p, _, _ = ORTHO[name]; p = mathutils.Vector(p); cam.location = p
        up = mathutils.Vector((0, 0, 1)) if name != "otop" else mathutils.Vector((1, 0, 0))
        tgt = mathutils.Vector((0, 0, 0.6)) if name != "otop" else mathutils.Vector((0, 0, 0))
        cam.rotation_euler = (tgt - p).to_track_quat('-Z', 'Y' if name != "otop" else 'X').to_euler()
        if name == "otop":
            cam.rotation_euler = (0, 0, math.radians(-90))  # pohled dolů, předek (−y) vlevo
        sc.render.filepath = f"{out}_{name}.png"
        bpy.ops.render.render(write_still=True)
    cam.data.type = 'PERSP'
