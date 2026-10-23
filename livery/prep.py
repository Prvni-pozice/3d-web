# Krok 1: spojí skořepinu (lak + karbon) do jednoho meshe s novou UV mapou
# a vypeče do ní světovou pozici a normálu (.npy) pro výpočet polepu v livery.py.
# Totéž pro vnější sklo (pruh KTM X-BOW nahoře na čelním skle).
# blender -b -P prep.py -- <res>
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
HERE = os.path.dirname(os.path.abspath(__file__))
RES = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else 4096
GLASS_RES = 1024


def unwrap(obj, mat_name):
    """Nahradí UV jednou novou mapou (smart project + husté balení) a dá objektu nový prázdný materiál."""
    me = obj.data
    while len(me.uv_layers): me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name="UVMap")
    mat = bpy.data.materials.new(mat_name); mat.use_nodes = True
    me.materials.clear(); me.materials.append(mat)
    for p in me.polygons: p.material_index = 0
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.002, area_weight=0.0, scale_to_bounds=True)
    bpy.ops.uv.select_all(action='SELECT')  # bez výběru UV pack nic nedělá
    bpy.ops.uv.pack_islands(rotate=True, margin=0.0015, shape_method='CONCAVE', margin_method='FRACTION')
    bpy.ops.object.mode_set(mode='OBJECT')
    return mat


def bake_maps(obj, mat, res, prefix):
    """Emission bake světové pozice, normály a masky pokrytí do work/<prefix>*.npy (řádek 0 = spodek)."""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
    nt = mat.node_tree; nt.nodes.clear()
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    img_node = nt.nodes.new("ShaderNodeTexImage"); nt.nodes.active = img_node
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj

    def grab(img):
        a = np.empty(res * res * 4, dtype=np.float32); img.pixels.foreach_get(a)
        return a.reshape(res, res, 4)

    for kind in ("Position", "Normal"):
        img = bpy.data.images.new(prefix + kind, res, res, float_buffer=True, alpha=True)
        img.generated_color = (0, 0, 0, 0)
        img_node.image = img
        for l in list(em.inputs[0].links): nt.links.remove(l)
        nt.links.new(geo.outputs[kind], em.inputs[0])
        bpy.ops.object.bake(type='EMIT', margin=12, margin_type='EXTEND', use_clear=True)
        np.save(os.path.join(HERE, "work", f"{prefix}{kind.lower()}.npy"), grab(img))
        print("BAKED", prefix, kind)
    # maska pokrytí UV (kde je geometrie) — bílá bez marginu
    img = bpy.data.images.new(prefix + "Cover", res, res, alpha=True); img.generated_color = (0, 0, 0, 1); img_node.image = img
    for l in list(em.inputs[0].links): nt.links.remove(l)
    em.inputs[0].default_value = (1, 1, 1, 1)
    bpy.ops.object.bake(type='EMIT', margin=0, use_clear=True)
    np.save(os.path.join(HERE, "work", f"{prefix}cover.npy"), grab(img)[..., 0] > 0.5)
    nt.nodes.clear()


common.load(os.path.join(HERE, "..", "ktm-gtx.glb"))

# Původní nápisy pryč: Badge (GTX…) + nápisový mesh s KTM / X-BOW na kapotě a střeše
for o in list(bpy.data.objects):
    # (jména objektů Blender zkracuje na 63 znaků → nápisový mesh poznáme podle materiálu „material“)
    if o.type == 'MESH' and ("Badge_Geo" in o.name or any(m and m.name == "material" for m in o.data.materials)):
        bpy.data.objects.remove(o)

# Skořepina
shell = [o for o in bpy.data.objects if o.type == 'MESH' and any(k in o.name for k in ("Paint_Geo", "Carbon1_Geo", "KTM:Carbon1Details_Geo"))]
print("SHELL", [o.name[:40] for o in shell], [len(o.data.polygons) for o in shell])
bpy.ops.object.select_all(action='DESELECT')
for o in shell: o.select_set(True)
bpy.context.view_layer.objects.active = shell[0]
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = "Livery_Body"
bake_maps(body, unwrap(body, "Livery"), RES, "")

# Vnější sklo (čelní + boční okna; zadní červené sklo a vnitřní sklo zůstávají)
glass = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.materials
         and o.data.materials[0].name.endswith("Window_Material1") and "WindowInside" not in o.name]
print("GLASS", [o.name[:50] for o in glass], [len(o.data.polygons) for o in glass])
glass = glass[0]
glass.name = "Livery_Glass"
bake_maps(glass, unwrap(glass, "LiveryGlass"), GLASS_RES, "glass_")

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "work", "prepped.blend"))
print("DONE")
