# Krok 3: přiřadí texturu polepu skořepině a buď vyrenderuje náhledy, nebo exportuje GLB.
# blender -b -P build.py -- render <outprefix> [views]
# blender -b -P build.py -- export <out.glb>
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:]
mode = argv[0]

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "work", "prepped.blend"))
body = bpy.data.objects["Livery_Body"]
mat = body.data.materials[0]; nt = mat.node_tree; nt.nodes.clear()
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
out = nt.nodes.new("ShaderNodeOutputMaterial")
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(os.path.join(HERE, "work", "livery.jpg"))
tex.image.colorspace_settings.name = "sRGB"
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(bsdf.outputs[0], out.inputs[0])
mr = nt.nodes.new("ShaderNodeTexImage")
mr.image = bpy.data.images.load(os.path.join(HERE, "work", "livery_mr.png"))
mr.image.colorspace_settings.name = "Non-Color"
sep = nt.nodes.new("ShaderNodeSeparateColor")
nt.links.new(mr.outputs["Color"], sep.inputs[0])
nt.links.new(sep.outputs[1], bsdf.inputs["Roughness"])   # G = roughness
nt.links.new(sep.outputs[2], bsdf.inputs["Metallic"])    # B = metallic

if mode == "render":
    common.scale_up()
    cam = common.setup_render(samples=int(os.environ.get("SAMPLES", 24)))
    views = argv[2].split(",") if len(argv) > 2 else ["front34", "rear34", "side", "sideL", "top"]
    persp = [v for v in views if not v.startswith("o")]
    common.render_views(cam, argv[1], persp)
    ortho = [v for v in views if v.startswith("o")]
    if ortho: common.render_ortho(cam, argv[1], ortho)
elif mode == "export":
    tex.image.pack(); mr.image.pack()
    bpy.ops.export_scene.gltf(filepath=argv[1], export_format='GLB', export_image_format='AUTO',
                              export_apply=False, export_yup=True)
    print("EXPORTED", argv[1])
