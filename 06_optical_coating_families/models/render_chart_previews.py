#!/usr/bin/env python3
"""Optional QA preview for our generated SVG subset, using preinstalled Pillow.
Not required for spectrum reproduction; no external images or paper figures.
"""
from pathlib import Path
import re,xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
for stem in ['01_spectral_atlas','02_angle_polarization']:
 root=ET.parse(ROOT/'figures'/f'{stem}.svg').getroot();im=Image.new('RGB',(int(root.attrib['width']),int(root.attrib['height'])),'white');d=ImageDraw.Draw(im)
 for e in root:
  tag=e.tag.split('}')[-1];a=e.attrib
  if tag=='rect':d.rectangle([0,0,im.width,im.height],fill=a['fill'])
  elif tag=='text':
   font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',int(a['font-size']))
   d.text((float(a['x']),float(a['y'])),e.text or '',font=font,fill=a.get('fill','#000000'),anchor='ls')
  elif tag=='polyline':
   pts=[tuple(map(float,p.split(','))) for p in a['points'].split()];d.line(pts,fill=a['stroke'],width=2)
  elif tag=='path':
   m=re.fullmatch(r'M([0-9.]+),([0-9.]+)h([0-9.]+)',a['d'])
   if not m:raise ValueError('unsupported path')
   x,y,length=map(float,m.groups());d.line([x,y,x+length,y],fill=a['stroke'])
  else:raise ValueError('unsupported generated SVG element')
 im.save(ROOT/'reviews'/f'{stem}_preview.png')
 print(stem,'preview',im.size)
