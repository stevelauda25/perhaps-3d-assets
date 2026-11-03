"""Trace only flat ink silhouettes from the already downloaded official photo.
No photographic illumination or surface texture is transferred to the asset.
Requires local cv2/numpy; run with python3, not Blender Python.
"""
from pathlib import Path
import cv2,json,numpy as np
P=Path(__file__).resolve().parent
im=cv2.imread(str(P.parents[1]/'references/casio-f91w/F-91W-1_06.jpg'))
regions={'CASIO':(430,335,700,400,'white',7.2,1.45,-5.45,10.5),'F-91W model':(825,335,1090,405,'yellow',6.55,1.28,6.1,10.5),'Alarm chronograph':(620,455,1155,510,'yellow',15.25,1.03,4.,7.05),'Water':(370,980,600,1034,'white',6.,1.13,-8.,-10.05),'Resist':(910,980,1145,1034,'white',6.1,1.13,8.1,-10.05),'WR logo':(625,975,870,1045,'red',6.,1.74,0.,-10.05),'signal':(408,574,499,614,'lcd',2.,.9,-8.95,3.85),'bell':(518,565,575,626,'lcd',1.4,1.55,-5.5,3.7)}
out={}
for name,(x0,y0,x1,y1,col,w,h,x,y) in regions.items():
 b,g,r=cv2.split(cv2.GaussianBlur(im[y0:y1,x0:x1],(5,5),.8).astype(float))
 if col=='white':mask=np.minimum(np.minimum(r,g),b)>125
 elif col=='yellow':mask=(r>120)&(g>95)&(b<g*.8)
 elif col=='red':mask=(r>100)&(r>g*1.8)&(r>b*1.5)
 else:mask=np.maximum(np.maximum(r,g),b)<85
 cs,_=cv2.findContours(mask.astype('uint8')*255,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
 smooth=[]
 for c in cs:
  if cv2.contourArea(c)<=3:continue
  a=c[:,0,:].astype(float)
  for _ in range(3):a=(np.roll(a,2,0)+4*np.roll(a,1,0)+6*a+4*np.roll(a,-1,0)+np.roll(a,-2,0))/16
  smooth.append(cv2.approxPolyDP(a.astype('float32')[:,None,:],.18,True)[:,0,:])
 pts=np.concatenate(smooth);lo=pts.min(0);hi=pts.max(0)
 out[name]={'color':col,'w':w,'h':h,'x':x,'y':y,'contours':[[[(float(a)-float(lo[0]))/float(hi[0]-lo[0])-.5,.5-(float(b)-float(lo[1]))/float(hi[1]-lo[1])] for a,b in c] for c in smooth]}
(P/'verified_graphics_contours.json').write_text(json.dumps(out,separators=(',',':')))
print('Traced',len(out),'verified ink groups')
