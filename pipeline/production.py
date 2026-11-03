"""Reference reconstruction: qualify sources, crop-calibrate, then render once."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0,str(ROOT))

MATERIAL_NAMES = ("PE6 | Scanned obsidian leather", "PE6 | Pressed leather")
VIEWS = ("hero","leather_macro","branding_macro","corner_macro")


def write(path,data):
    path.write_text(json.dumps(data,indent=2)+"\n")


def history():
    folders = [ROOT/"references/packaging"]
    folders += [ROOT/"outputs/packaging"/name for name in ("canonical-v001","private-edition-v007",
                "private-edition-v007-benchmarks","private-edition-v008","private-edition-v009")]
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in folders for p in sorted(folder.rglob("*")) if p.is_file()}


def validate_config(c):
    p=c["leather"]
    if not 0 < p["tile_mm"] <= 1000 or p["uv_base_tile_mm"] != 32:
        raise ValueError("Invalid physical scan/metric UV scale")
    if not 0 <= p["roughness_range"][0] < p["roughness_range"][1] <= 1:
        raise ValueError("Invalid leather roughness range")
    if not 0 < c["finishing"]["deboss_depth_mm"] <= 0.3:
        raise ValueError("Deboss must remain a shallow, nonstructural surface treatment")
    if (ROOT/"outputs").resolve() not in (ROOT/c["output"]).resolve().parents:
        raise ValueError("Production output must stay below outputs/")
    if (ROOT/c["output"]).resolve()==(ROOT/c["input"]).resolve().parent:
        raise ValueError("Do not write into the source version")
    scene_name=c.get("final_scene","private_edition_calibrated.blend")
    if Path(scene_name).name!=scene_name:
        raise ValueError("Final scene must be a local filename")


def uv_audit():
    import bpy
    result={}
    for name in ("PE6 | Continuous lid leather wrap","PE6 | Continuous base leather wrap"):
        obj=bpy.data.objects[name];mesh=obj.data;uv=mesh.uv_layers["PE metric wrap"].data
        serialized=[[float(x) for x in item.uv] for item in uv]
        ratios=[]
        for face in mesh.polygons:
            if face.material_index!=0 or max(abs(v) for v in face.normal)<0.99999:
                continue
            loops=list(face.loop_indices)
            for a,b in zip(loops,loops[1:]+loops[:1]):
                distance=((obj.matrix_world@mesh.vertices[mesh.loops[a].vertex_index].co)-(obj.matrix_world@mesh.vertices[mesh.loops[b].vertex_index].co)).length
                delta=(uv[a].uv-uv[b].uv).length
                if distance>0.01 and delta>1e-6:ratios.append(distance/delta*1000)
        if not ratios:raise RuntimeError("No planar UV density samples")
        if max(abs(v-32) for v in ratios)>0.02:raise RuntimeError("Inconsistent metric UV scale")
        result[name]={"uv_sha256":hashlib.sha256(json.dumps(serialized).encode()).hexdigest(),
                      "planar_edge_samples":len(ratios),"mm_per_uv_range":[min(ratios),max(ratios)],
                      "object_scale":list(obj.scale)}
    return result


def materials(c):
    import bpy
    source=json.loads((ROOT/c["source_manifest"]).read_text())
    p=c["leather"]
    images={}
    for channel,info in source["maps"].items():
        path=ROOT/info["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest()!=info["sha256"]:
            raise RuntimeError("Source texture checksum changed: "+str(path))
        image=bpy.data.images.load(str(path),check_existing=True)
        image.colorspace_settings.name="sRGB" if channel=="color" else "Non-Color"
        image.pack()
        images[channel]=image
    for material_name in MATERIAL_NAMES:
        mat=bpy.data.materials[material_name];mat.use_nodes=True
        nodes,links=mat.node_tree.nodes,mat.node_tree.links
        nodes.clear()
        def node(kind,name,xy):
            n=nodes.new(kind);n.name=n.label=name;n.location=xy;return n
        def ramp(source_socket,name,limits,values,xy):
            n=node("ShaderNodeMapRange",name,xy);n.clamp=True
            n.interpolation_type="SMOOTHERSTEP"
            links.new(source_socket,n.inputs["Value"])
            for key,value in zip(("From Min","From Max","To Min","To Max"),(*limits,*values)):
                n.inputs[key].default_value=value
            return n.outputs["Result"]
        uv=node("ShaderNodeUVMap","Original metric wrap UV",(-1000,100));uv.uv_map="PE metric wrap"
        scale=node("ShaderNodeVectorMath","Physical source repeat",(-800,100));scale.operation="SCALE"
        scale.inputs["Scale"].default_value=p["uv_base_tile_mm"]/p["tile_mm"]
        links.new(uv.outputs["UV"],scale.inputs[0])
        maps={}
        for i,channel in enumerate(("color","roughness","normal","height")):
            n=node("ShaderNodeTexImage","Original 8K source | "+channel,(-570,600-i*280))
            n.image=images[channel];n.interpolation="Linear";n.extension="REPEAT"
            links.new(scale.outputs["Vector"],n.inputs["Vector"]);maps[channel]=n
        bsdf=node("ShaderNodeBsdfPrincipled","Private Edition leather",(650,100))
        out=node("ShaderNodeOutputMaterial","Material Output",(1000,100));links.new(bsdf.outputs["BSDF"],out.inputs["Surface"])
        gray=node("ShaderNodeRGBToBW","Natural photographic pigmentation",(-280,600))
        links.new(maps["color"].outputs["Color"],gray.inputs[0])
        dye=ramp(gray.outputs[0],"Preserve local pigment variation",p["luminance_range"],p["pigment_factors"],(-80,600))
        tint=node("ShaderNodeMixRGB","Obsidian dye",(200,600));tint.blend_type="MULTIPLY";tint.inputs[0].default_value=1
        pressed=material_name==MATERIAL_NAMES[1]
        factor=p["pressed_color_factor"] if pressed else 1
        tint.inputs[1].default_value=tuple(x*factor for x in p["color_linear"])+(1,)
        links.new(dye,tint.inputs[2]);links.new(tint.outputs[0],bsdf.inputs["Base Color"])
        rough=[v+(p["pressed_roughness_offset"] if pressed else 0) for v in p["roughness_range"]]
        rough_socket=ramp(maps["roughness"].outputs["Color"],"Calibrated satin roughness",p["roughness_source_range"],rough,(100,250))
        links.new(rough_socket,bsdf.inputs["Roughness"])
        normal=node("ShaderNodeNormalMap","Supplied OpenGL grain and pores",(50,-100));normal.space="TANGENT";normal.uv_map="PE metric wrap"
        normal.inputs["Strength"].default_value=p["pressed_normal_strength"] if pressed else p["normal_strength"]
        links.new(maps["normal"].outputs["Color"],normal.inputs["Color"])
        links.new(normal.outputs["Normal"],bsdf.inputs["Normal"])
        links.new(normal.outputs["Normal"],bsdf.inputs["Coat Normal"])
        for name,value in {"IOR":p["ior"],"Specular IOR Level":0.5,"Coat Weight":p["coat_weight"],
                           "Coat Roughness":p["coat_roughness"],"Sheen Weight":0.0,"Diffuse Roughness":0.1}.items():
            bsdf.inputs[name].default_value=value
        mat["source_url"]=source["source_url"];mat["physical_repeat_mm"]=p["tile_mm"]
        mat["source_resolution"]=8192
        mat["relief_note"]="Supplied normal contains grain and pores; height retained but not stacked into relief. No measured-depth claim."


def cameras(c):
    import bpy
    from .studio import aim
    collection=bpy.data.collections.new("STUDIO | Production reference cameras")
    bpy.context.scene.collection.children.link(collection)
    for name in VIEWS:
        old=bpy.data.objects["CAM | reference_"+name]
        obj=old.copy();obj.data=old.data.copy();obj.name=obj.data.name="CAM | production_"+name
        collection.objects.link(obj)
        if name=="hero":
            obj.data.lens=c["camera"]["lens_mm"]
            aim(obj,c["camera"]["position"],c["camera"]["target"])
        else:
            obj.data.ortho_scale=c["macro_scales_mm"][name]/1000


def finishing(c):
    import bpy
    from mathutils import Vector
    f=c["finishing"]
    wrap=bpy.data.objects["PE6 | Continuous lid leather wrap"]
    # Only the removable wrap's recessed letter floors move; silhouette and
    # canonical box vertices remain unchanged.
    ids={v for face in wrap.data.polygons if face.material_index==3 for v in face.vertices}
    front=-0.07
    floors=[i for i in ids if 0.00002 < (wrap.matrix_world@wrap.data.vertices[i].co).y-front < 0.0003]
    if not floors:
        raise RuntimeError("Expected existing shallow deboss floors")
    depth=max((wrap.matrix_world@wrap.data.vertices[i].co).y-front for i in floors)
    delta=f["deboss_depth_mm"]/1000-depth
    local=wrap.matrix_world.inverted().to_3x3()@Vector((0,delta,0))
    for i in floors:wrap.data.vertices[i].co+=local
    wrap.data.update()
    lip=wrap.modifiers["Soft compressed die lip only"]
    lip.width=f["die_lip_mm"]/1000;lip.segments=4
    thread=bpy.data.objects["PE6 | Inset leather stitching"]
    thread.data.bevel_depth=f["stitch_radius_mm"]/1000
    factor=f["stitch_length_mm"]/f["stitch_original_length_mm"]
    for spline in thread.data.splines:
        points=spline.bezier_points;center=points[2].co.copy();direction=(points[-1].co-points[0].co).normalized()
        for point in points:
            point.co+=direction*((point.co-center).dot(direction)*(factor-1))
    mat=bpy.data.objects["Box | Interior collar and reveal"].data.materials[2]
    shader=mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(*f["metal_color_linear"],1)
    shader.inputs["Anisotropic"].default_value=f["metal_anisotropy"]
    remap=mat.node_tree.nodes["Controlled brushed roughness"]
    remap.inputs["To Min"].default_value,remap.inputs["To Max"].default_value=f["metal_roughness_range"]
    return {"letter_floor_vertices":len(floors),"old_deboss_depth_mm":depth*1000,
            "new_deboss_depth_mm":f["deboss_depth_mm"],"canonical_geometry_modified":False}


def transforms():
    import bpy
    return {o.name:{"matrix_basis":[list(row) for row in o.matrix_basis],"parent_inverse":[list(row) for row in o.matrix_parent_inverse],
                    "parent":o.parent.name if o.parent else None}
            for o in bpy.data.objects if o.get("export_product") or o.get("finishing_only") or o.name.startswith("CTRL |")}


def render(c,out,name,filename,border=None,final=False):
    import bpy
    from .rendering import configure
    scene=bpy.context.scene;r=c["render"]
    size=r["hero_resolution"] if name=="hero" else r["macro_resolution"]
    profile={"resolution":size,"samples":r["final_samples"] if final else r["calibration_samples"],
             "adaptive_threshold":r["adaptive_threshold"],"denoise":True,"bit_depth":"16"}
    configure({"presets":{"production":profile}},"production","metal",lambda *args,**kwargs:None)
    scene.view_settings.view_transform=c["view_transform"];scene.view_settings.look=c["look"];scene.view_settings.exposure=c["exposure"]
    scene.cycles.max_bounces=12;scene.cycles.use_light_tree=True;scene.cycles.filter_width=r["filter_width"]
    scene.camera=bpy.data.objects["CAM | production_"+name]
    scene.render.use_border=bool(border);scene.render.use_crop_to_border=bool(border)
    if border:
        scene.render.border_min_x,scene.render.border_max_x,scene.render.border_min_y,scene.render.border_max_y=border
    path=out/filename
    if path.exists():raise FileExistsError(str(path))
    start=time.monotonic();bpy.ops.render.render(write_still=False)
    result=bpy.data.images["Render Result"]
    if final:
        scene.render.image_settings.file_format="OPEN_EXR";scene.render.image_settings.color_depth="16";scene.render.image_settings.exr_codec="ZIP"
        result.save_render(str(path.with_suffix(".exr")),scene=scene)
    scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_depth="16"
    result.save_render(str(path),scene=scene)
    record={"view":name,"path":str(path),"seconds":round(time.monotonic()-start,3),"full_frame_resolution":size,
            "samples":profile["samples"],"border":border,"metal":True,"exr":final}
    with (out/"events.jsonl").open("a") as stream:stream.write(json.dumps(record)+"\n")
    print("PRODUCTION",json.dumps(record),flush=True)


def run(stage,c):
    import bpy
    from . import locked,reference_studio
    out=ROOT/c["output"];source=ROOT/c["input"]
    if stage=="material":
        target=out/"calibration/material.blend"
        if target.exists():raise FileExistsError(str(target))
        write(out/"history_sha256.json",history())
        bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
        lock={"protected":locked.snapshot(),"transforms":transforms(),"source":str(source),"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest()}
        write(out/"geometry_lock.json",lock)
        materials(c);cameras(c)
        reference_studio.refine({"lights":c["neutral_lights"]})
        locked.verify(lock["protected"])
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=False)
        render(c,out,"hero","calibration/material_front.png",(0.62,0.87,0.38,0.63))
        render(c,out,"leather_macro","calibration/material_macro.png",(0.40,0.733333333,0.30,0.633333333))
    elif stage=="studio":
        target=out/"private_edition.blend"
        if target.exists():raise FileExistsError(str(target))
        bpy.ops.wm.open_mainfile(filepath=str(out/"calibration/material.blend"),load_ui=False,use_scripts=False)
        lock=json.loads((out/"geometry_lock.json").read_text())
        details=finishing(c)
        reference_studio.refine({"lights":c["studio_lights"]})
        locked.verify(lock["protected"])
        if transforms()!=lock["transforms"]:raise RuntimeError("Product/finishing transforms changed")
        write(out/"finishing.json",details)
        bpy.context.scene.camera=bpy.data.objects["CAM | production_hero"]
        scene=bpy.context.scene
        scene.render.resolution_x=scene.render.resolution_y=c["render"]["hero_resolution"]
        scene.render.resolution_percentage=100
        scene.cycles.samples=c["render"]["final_samples"]
        scene.cycles.adaptive_threshold=c["render"]["adaptive_threshold"]
        scene.cycles.filter_width=c["render"]["filter_width"]
        scene.view_settings.view_transform=c["view_transform"]
        scene.view_settings.look=c["look"]
        scene.view_settings.exposure=c["exposure"]
        bpy.context.scene.render.use_border=False;bpy.context.scene.render.use_crop_to_border=False
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=False)
        render(c,out,"hero","calibration/studio_edge.png",(0.43,0.68,0.65,0.90))
        render(c,out,"branding_macro","calibration/studio_branding.png",(0.30,0.80,0.20,0.70))
    elif stage=="calibrate":
        target=out/c["final_scene"]
        if target.exists():raise FileExistsError(str(target))
        bpy.ops.wm.open_mainfile(filepath=str(out/"private_edition.blend"),load_ui=False,use_scripts=False)
        bpy.data.materials[MATERIAL_NAMES[0]].node_tree.nodes["Supplied OpenGL grain and pores"].inputs["Strength"].default_value=c["leather"]["normal_strength"]
        reference_studio.refine({"lights":c["studio_lights"]})
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=False)
    elif stage=="final":
        bpy.ops.wm.open_mainfile(filepath=str(out/c["final_scene"]),load_ui=False,use_scripts=False)
        for name in VIEWS:render(c,out,name,name+".png",final=True)
    else:
        bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
        before_uv=uv_audit()
        bpy.ops.wm.open_mainfile(filepath=str(out/c["final_scene"]),load_ui=False,use_scripts=False)
        after_uv=uv_audit()
        for name in before_uv:
            if before_uv[name]["uv_sha256"]!=after_uv[name]["uv_sha256"]:
                raise RuntimeError("Approved wrap UV coordinates changed")
        write(out/"uv_validation.json",{"before":before_uv,"after":after_uv,
              "unchanged":True,"uniform_texture_repeat_mm":c["leather"]["tile_mm"]})
    if stage in ("final","verify"):
        lock=json.loads((out/"geometry_lock.json").read_text())
        fingerprint=locked.verify(lock["protected"])
        if transforms()!=lock["transforms"]:raise RuntimeError("Product transforms changed")
        if history()!=json.loads((out/"history_sha256.json").read_text()):raise RuntimeError("Previous files changed")
        for mat_name in MATERIAL_NAMES:
            mat=bpy.data.materials[mat_name];tree=mat.node_tree
            for key in ("color","roughness","normal","height"):
                n=tree.nodes["Original 8K source | "+key]
                assert n.inputs["Vector"].links[0].from_node.name=="Physical source repeat"
                assert n.image.packed_file
                assert n.image.colorspace_settings.name==("sRGB" if key=="color" else "Non-Color")
            assert not tree.nodes["Material Output"].inputs["Displacement"].is_linked
            assert abs(tree.nodes["Physical source repeat"].inputs["Scale"].default_value-c["leather"]["uv_base_tile_mm"]/c["leather"]["tile_mm"])<1e-7
        write(out/"validation.json",{"canonical_and_original_cameras_unchanged":True,"all_product_transforms_unchanged":True,
              "previous_files_unchanged":True,"protected_fingerprint":fingerprint,"source_maps_packed":True,
              "source_maps_aligned":True,"no_structural_displacement":True,"stage":stage,
              "manual_visual_approval":"pending; no numeric similarity score asserted"})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=("material","studio","calibrate","final","verify"))
    parser.add_argument("--config",type=Path,default=ROOT/"config/private_edition_production.json")
    parser.add_argument("--blender",action="store_true",help=argparse.SUPPRESS)
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else None)
    c=json.loads(args.config.read_text());validate_config(c)
    out=ROOT/c["output"]
    if args.blender:return run(args.stage,c)
    from .cli import detect_blender
    (out/"calibration").mkdir(parents=True,exist_ok=True)
    log=out/(args.stage+".log")
    if log.exists():raise FileExistsError("Stage log already exists: "+str(log))
    write(out/("config_"+args.stage+".json"),c)
    command=[detect_blender(json.loads((ROOT/"config/packaging.json").read_text())),"--background","--factory-startup","--disable-autoexec",
             "--python-exit-code","1","--python",str(Path(__file__).resolve()),"--",args.stage,"--config",str(args.config.resolve()),"--blender"]
    print("Running production",args.stage,"→",out,flush=True)
    with log.open("x") as stream:
        result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1"))
    write(out/("status_"+args.stage+".json"),{"success":result.returncode==0,"exit_code":result.returncode})
    if result.returncode:print("\n".join(log.read_text().splitlines()[-14:]))
    print("Completed" if result.returncode==0 else "Failed",args.stage,flush=True)
    raise SystemExit(result.returncode)


if __name__=="__main__":
    # Blender executes this file directly, while the host uses -m pipeline.production.
    if not __package__:__package__="pipeline"
    main()
