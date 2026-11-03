"""Manual-review sheet: native 16-bit render pixels and nearest-neighbor source crop."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def create(reference, hero, output):
    if output.exists():
        raise FileExistsError("Refusing to overwrite comparison sheet")
    original = cv2.imread(str(reference), cv2.IMREAD_COLOR)
    actual = cv2.imread(str(hero), cv2.IMREAD_UNCHANGED)
    if original is None or actual is None or actual.shape != (2048,2048,3) or actual.dtype != np.uint16:
        raise ValueError("Expected original reference and native 2048px 16-bit RGB hero")
    bounds = (30,102,550,550)
    x0,y0,x1,y1 = bounds
    crop = original[y0:y1,x0:x1]
    enlarged = np.repeat(np.repeat(crop,4,axis=0),4,axis=1).astype(np.uint16)*257
    canvas = np.zeros((2300,4300,3), dtype=np.uint16)
    canvas[314:314+enlarged.shape[0],40:2120] = enlarged
    canvas[186:2234,2236:4284] = actual
    labels = Image.new("RGB", (4300,170), "black")
    draw = ImageDraw.Draw(labels)
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf",48)
    small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf",27)
    for x,title,subtitle in [(40,"Original Perhaps reference hero","Unretouched crop, nearest-neighbor 4x enlargement"),
                             (2220,"Actual Blender / Cycles hero","Native 2048px render pixels; no grading, warping or retouching")]:
        draw.text((x,40),title,font=font,fill=(230,230,230))
        draw.text((x,104),subtitle,font=small,fill=(160,160,160))
    canvas[:170] = np.asarray(labels)[:,:,::-1].astype(np.uint16)*257
    assert np.array_equal(canvas[186:2234,2236:4284],actual)
    assert cv2.imwrite(str(output),canvas,[cv2.IMWRITE_PNG_COMPRESSION,6])
    check = cv2.imread(str(output),cv2.IMREAD_UNCHANGED)
    assert np.array_equal(check[186:2234,2236:4284],actual), "Render pixels changed in sheet"
    record = {"reference":str(reference.resolve()),"reference_sha256":hashlib.sha256(reference.read_bytes()).hexdigest(),
              "reference_crop_xyxy":bounds,"reference_scale":4,"reference_interpolation":"nearest-neighbor",
              "hero":str(hero.resolve()),"hero_sha256":hashlib.sha256(hero.read_bytes()).hexdigest(),
              "hero_scale":1,"hero_pixels_copied_exactly_16bit":True,"dimensions":[4300,2300],
              "color_changes":False,"warping":False,"automatic_similarity_scoring":False}
    output.with_suffix(".json").write_text(json.dumps(record,indent=2)+"\n")
    print(output.resolve())


def create_history(reference, renders, output):
    """Reference plus three native/integer-enlarged actual Blender renders."""
    if output.exists():
        raise FileExistsError("Refusing to overwrite comparison sheet")
    original = cv2.imread(str(reference),cv2.IMREAD_COLOR)
    if original is None or len(renders) != 3:
        raise ValueError("Expected reference and three historical/current heroes")
    enlarged = np.repeat(np.repeat(original[102:550,30:550],4,axis=0),4,axis=1).astype(np.uint16)*257
    width, stride, top = 8470,2110,190
    canvas = np.zeros((2300,width,3),dtype=np.uint16)
    canvas[top+144:top+144+enlarged.shape[0],30:2110] = enlarged
    labels = [("Original Perhaps reference","Unretouched crop, nearest-neighbor 4x; not a grain ruler")]
    provenance = {"reference":str(reference),"reference_crop_xyxy":[30,102,550,550],"reference_scale":4,
                  "reference_sha256":hashlib.sha256(reference.read_bytes()).hexdigest(),
                  "retouching":False,"warping":False,"color_adjustment":False,"similarity_scoring":False,"renders":[]}
    for i,(path,title) in enumerate(renders,1):
        actual = cv2.imread(str(path),cv2.IMREAD_UNCHANGED)
        if actual is None or actual.dtype != np.uint16 or actual.shape not in ((1024,1024,3),(2048,2048,3)):
            raise ValueError("Expected native 1024px/2048px 16-bit hero: "+str(path))
        factor = 2048//actual.shape[0]
        image = np.repeat(np.repeat(actual,factor,axis=0),factor,axis=1)
        x,y = 30+i*stride+16,top+16
        canvas[y:y+2048,x:x+2048] = image
        samples = (512,128,256)[i-1]
        subtitle = str(actual.shape[0])+"px / "+str(samples)+" samples; "+("native pixels" if factor==1 else "nearest-neighbor 2x")
        labels.append((title,subtitle))
        provenance["renders"].append({"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                                      "factor":factor,"pixel_origin_xy":[x,y]})
    heading = Image.new("RGB",(width,top),"black")
    draw = ImageDraw.Draw(heading)
    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
    font,small = ImageFont.truetype(font_path,43),ImageFont.truetype(font_path,26)
    for i,(title,subtitle) in enumerate(labels):
        draw.text((30+i*stride,35),title,font=font,fill=(230,230,230))
        draw.text((30+i*stride,110),subtitle,font=small,fill=(170,170,170))
    canvas[:top] = np.asarray(heading)[:,:,::-1].astype(np.uint16)*257
    assert cv2.imwrite(str(output),canvas,[cv2.IMWRITE_PNG_COMPRESSION,6])
    check = cv2.imread(str(output),cv2.IMREAD_UNCHANGED)
    for entry in provenance["renders"]:
        actual = cv2.imread(entry["path"],cv2.IMREAD_UNCHANGED)
        x,y = entry["pixel_origin_xy"]
        assert np.array_equal(check[y:y+2048:entry["factor"],x:x+2048:entry["factor"]],actual)
    assert np.array_equal(check[top+144:top+144+enlarged.shape[0],30:2110],enlarged)
    provenance["source_pixels_preserved"] = True
    write_path = output.with_suffix(".json")
    write_path.write_text(json.dumps(provenance,indent=2)+"\n")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference",type=Path,required=True)
    parser.add_argument("--hero",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    create(args.reference,args.hero,args.output)
