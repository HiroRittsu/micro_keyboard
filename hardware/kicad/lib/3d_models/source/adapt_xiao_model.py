"""Adapt Seeed's XIAO nRF52840 v15 STEP to standard, pinless SMD.
Source is the official Sense STEP linked in docs/components/xiao_nrf52840.md.
Usage: python adapt_xiao_model.py SOURCE.step OUTPUT.step
Requires cadquery==2.8.0. No dimensions are scaled.
"""
import sys,json,hashlib
from pathlib import Path
import cadquery as cq
src,dst=map(Path,sys.argv[1:3])
solids=cq.importers.importStep(str(src)).solids().vals()
# Source v15 uses X for board length, Y for height, Z for width.
# Rotate cyclically: X'=Z, Y'=X, Z'=Y. Place board underside on Z=0.
assembly=cq.Assembly(name='XIAO_nRF52840_standard_SMD')
board=solids[60].BoundingBox()
shift=(-board.zmin, -board.xmin+0.082, -board.ymin)
for i,s in enumerate(solids):
 # MSM261D3526H1CPM microphone body, detail and six solder contacts.
 if 76<=i<=83: continue
 s=s.rotate((0,0,0),(1,1,1),120).translate(shift)
 color=(.08,.09,.09) if i==60 else (.67,.69,.7) if i in [18,24,25] else (.18,.19,.2) if i in [10,22,33] else (.65,.58,.36)
 assembly.add(s,name=f'seed_part_{i:02d}',color=cq.Color(*color))
assembly.save(str(dst))
b=assembly.toCompound().BoundingBox()
meta={'source_url':'https://files.seeedstudio.com/wiki/XIAO-BLE/seeed-studio-xiao-nrf52840-3d-model.zip','source_file':src.name,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_solids':len(solids),'removed_solids':list(range(76,84)),'reason':'Remove Sense microphone MSM261D3526H1CPM and contacts; standard external envelope. Shield interior not modeled.','axis_rotation_deg':120,'axis':[1,1,1],'translation_mm':shift,'model_bbox_mm':dict(zip(['xmin','xmax','ymin','ymax','zmin','zmax'],[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax])),'notes':['Manufacturer model dated 2023-06-02; not a measured current revision.','Colors are assigned for visualization; no bitmap markings.','Parent PCB thickness is separate from module thickness.']}
dst.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(meta,ensure_ascii=False))
