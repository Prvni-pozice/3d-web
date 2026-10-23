# Krok 1: spojí skořepinu (lak + karbon) do jednoho meshe s novou UV mapou
# a vypeče do ní světovou pozici a normálu (.npy) pro výpočet polepu v livery.py.
# blender -b -P prep.py -- <res>
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
HERE = os.path.dirname(os.path.abspath(__file__))
RES = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else 4096

common.load(os.path.join(HERE, "..", "ktm-gtx.glb"))

# Původní nápisy pryč: Badge (GTX…) + nápisový mesh s KTM / X-BOW na kapotě a střeše
for o in list(bpy.data.objects):
    # (jména objektů Blender zkracuje na 63 znaků → nápisový mesh poznáme podle materiálu „material“)
    if o.type == 'MESH' and ("Badge_Geo" in o.name or any(m and m.name == "material" for m in o.data.materials)):
        bpy.data.objects.remove(o)

shell = [o for o in bpy.data.objects if o.type == 'MESH' and any(k in o.name for k in ("Paint_Geo", "Carbon1_Geo", "KTM:Carbon1Details_Geo"))]
print("SHELL", [o.name[:40] for o in shell], [len(o.data.polygons) for o in shell])
for o in shell: print("MODS", o.name[:30], [m.type for m in o.modifiers], o.parent.name if o.parent else None)
bpy.ops.object.select_all(action='DESELECT')
for o in shell: o.select_set(True)
bpy.context.view_layer.objects.active = shell[0]
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = "Livery_Body"
me = body.data
while len(me.uv_layers): me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name="UVMap")
mat = bpy.data.materials.new("Livery"); mat.use_nodes = True
me.materials.clear(); me.materials.append(mat)
for p in me.polygons: p.material_index = 0

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.002, area_weight=0.0, scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')
print("POLYS", len(me.polygons))

# Bake: emission = pozice / normála (světové souřadnice)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
nt = mat.node_tree; nt.nodes.clear()
geo = nt.nodes.new("ShaderNodeNewGeometry")
em = nt.nodes.new("ShaderNodeEmission")
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs[0], out.inputs[0])
img_node = nt.nodes.new("ShaderNodeTexImage"); nt.nodes.active = img_node
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
for kind in ("Position", "Normal"):
    img = bpy.data.images.new(kind, RES, RES, float_buffer=True, alpha=True)
    img.generated_color = (0, 0, 0, 0)
    img_node.image = img
    for l in list(em.inputs[0].links): nt.links.remove(l)
    nt.links.new(geo.outputs[kind], em.inputs[0])
    bpy.ops.object.bake(type='EMIT', margin=12, margin_type='EXTEND', use_clear=True)
    a = np.empty(RES * RES * 4, dtype=np.float32); img.pixels.foreach_get(a)
    np.save(os.path.join(HERE, "work", f"{kind.lower()}.npy"), a.reshape(RES, RES, 4))  # řádek 0 = spodek
    print("BAKED", kind)
# Maska pokrytí UV (kde je geometrie) — bake bílé bez marginu
img = bpy.data.images.new("Cover", RES, RES, alpha=True); img.generated_color = (0, 0, 0, 1); img_node.image = img
for l in list(em.inputs[0].links): nt.links.remove(l)
em.inputs[0].default_value = (1, 1, 1, 1)
bpy.ops.object.bake(type='EMIT', margin=0, use_clear=True)
a = np.empty(RES * RES * 4, dtype=np.float32); img.pixels.foreach_get(a)
np.save(os.path.join(HERE, "work", "cover.npy"), a.reshape(RES, RES, 4)[..., 0] > 0.5)

nt.nodes.clear()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "work", "prepped.blend"))
print("DONE")
