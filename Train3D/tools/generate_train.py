#!/usr/bin/env python3
"""Train3D - station scene generator for Crayon Engine. python tools/generate_train.py (needs pillow numpy)"""
import math, os, random, sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw
import _lib as L
from _lib import Mesh, lathe, placed, colored, rotX, rotZ, MODELS, TEXTURES
random.seed(5); np.random.seed(5)

P = {"red":"#b3231c","red2":"#8e1a15","orange":"#e5891c","yellow":"#e8c52a","white":"#e6e4da","black":"#18181a","dgrey":"#3b3b3d",
     "wag":"#8c8b84","wag2":"#5d5d58","rail":"#6a5648","sleeper":"#85837e","mast":"#767b80",
     "wire":"#26282b","tree1":"#3b6a2e","tree2":"#52793a","tree3":"#2e5528","trunk":"#4a3a2a","win":"#1a222c","coach":"#d8c47c",
     "coach2":"#a8a291","lamp":"#fff3c0","rust":"#6b4630","wheel":"#222224","hut":"#9a9486","roofgrey":"#6e6f6c","bush":"#47703a"}
L.PAL=list(P.keys()); L.CI={n:i for i,n in enumerate(L.PAL)}
im=Image.new("RGB",(8,8))
for i,h in enumerate(P.values()): im.putpixel((i%8,i//8),tuple(int(h[j:j+2],16) for j in (1,3,5)))
im.resize((64,64),Image.NEAREST).save(os.path.join(TEXTURES,"palette.png"))

def pbox(m,n,c,h): L.pbox(m,n,c,h)
def cylx(m,n,r,x0,x1,y,z,seg=14):
    with placed(m,rotZ(math.pi/2),(0,y,z)):
        with colored(m,n): lathe(m,[(0,x0),(r,x0),(r,x1),(0,x1)],seg,1,30)
def cyly(m,n,r,y0,y1,x,z,seg=10):
    with placed(m,L.I3,(x,0,z)): L.cyl(m,n,r,y0,y1,seg)
def blob(m,n,c,r,sy=1.0,seg=9):
    prof=[(r*math.sin(math.pi*i/6),sy*r*-math.cos(math.pi*i/6)) for i in range(7)]
    with placed(m,L.I3,c):
        with colored(m,n): lathe(m,prof,seg,1,180)
def tquad(m,a,b,c,d):
    m.quad((a,(0,1,0),(0,0)),(b,(0,1,0),(1,0)),(c,(0,1,0),(1,1)),(d,(0,1,0),(0,1)))
def tiles(m,x0,x1,z0,z1,y,step):
    for x in np.arange(x0,x1,step):
        for z in np.arange(z0,z1,step):
            xe,ze=min(x+step,x1),min(z+step,z1)
            tquad(m,(x,y,ze),(xe,y,ze),(xe,y,z),(x,y,z))
ZF=-190.0; TX=[0.0,4.4]; RT=0.17

# ---------------- textures
def noise(w,h,sc,amp):
    n=np.random.rand(max(2,h//sc),max(2,w//sc)); i=Image.fromarray((n*255).astype('uint8')).resize((w,h),Image.BICUBIC)
    return (np.asarray(i).astype(float)/255-.5)*amp
def mk(name,base,var=30,spk=40,sc=4,size=128,extra=None):
    a=np.zeros((size,size,3))+np.array(base,float)+noise(size,size,sc,var)[...,None]+((np.random.rand(size,size)-.5)*spk)[...,None]
    i=Image.fromarray(np.clip(a,0,255).astype('uint8'))
    if extra: extra(ImageDraw.Draw(i),size)
    i.save(os.path.join(TEXTURES,name))
def ballast_x(d,s):
    for _ in range(260):
        x,y=random.randrange(s),random.randrange(s); r=random.randint(2,5); g=random.randint(70,150)
        d.ellipse([x-r,y-r*.7,x+r,y+r*.7],fill=(g,g-4,g-8),outline=(45,44,42))
mk("ballast.png",(105,102,98),40,60,3,128,ballast_x)
mk("grass.png",(62,100,48),35,50,3)
mk("ground.png",(96,88,76),25,40,6)
def plat_x(d,s):
    for k in range(0,s,32): d.line([k,0,k,s],fill=(110,110,106)); d.line([0,k,s,k],fill=(110,110,106))
mk("platform.png",(150,150,146),22,18,8,128,plat_x)
mk("tank.png",(128,130,122),26,20,10,128,lambda d,s:[d.line([x,0,x+random.randint(-3,3),s],fill=(96,76,60),width=1) for x in random.sample(range(s),18)])
sk=np.zeros((256,8,3))
for y in range(256):
    t=y/255; sk[y]=np.array([150,155,160])*(1-t)+np.array([214,216,212])*t
big=np.asarray(Image.fromarray(sk.astype('uint8')).resize((256,256)))+noise(256,256,24,26)[...,None]
Image.fromarray(np.clip(big,0,255).astype('uint8')).save(os.path.join(TEXTURES,"sky.png"))

# ---------------- ground
m=Mesh(); tiles(m,-90,90,ZF-20,30,-0.12,12); m.save("ground.obj")
g=Mesh()
for a,b in [(-2.2,-1.7),(2.3,2.7),(6.2,7.4)]: tiles(g,a,b,ZF,6,0.02,2)
g.save("grass.obj")
b=Mesh()
for cx in TX:
    for z in np.arange(ZF,6,4.0):
        ze=min(z+4,6)
        tquad(b,(cx-1.7,.1,ze),(cx+1.7,.1,ze),(cx+1.7,.1,z),(cx-1.7,.1,z))
        for s in (-1,1): tquad(b,(cx+s*1.7,.1,ze),(cx+s*2.3,0,ze),(cx+s*2.3,0,z),(cx+s*1.7,.1,z))
b.save("ballast.obj")
sp=Mesh(); x1,y=-2.3,.95
tiles(sp,-9,x1,ZF,6,y,1.6)
for z in np.arange(ZF,6,4.0):
    ze=min(z+4,6); tquad(sp,(x1,y,ze),(x1,y,z),(x1,0,z),(x1,0,ze))
sp.save("platform.obj")
sm=Mesh(); lathe(sm,[(180,-30),(180,0),(175,45),(144,100),(72,150),(0,160)],24,-1,180); sm.save("sky.obj")

# ---------------- props
m=Mesh()
for cx in TX:
    for s in (-.84,.84): pbox(m,"rail",(cx+s,.2,(ZF+6)/2),(.035,.09,(6-ZF)/2))
    for z in np.arange(ZF,6,.72): pbox(m,"sleeper",(cx,.17,z),(1.3,.07,.13))
pbox(m,"yellow",(-2.55,.955,(ZF+6)/2),(.18,.005,(6-ZF)/2))
for z in np.arange(-6,ZF,-32):
    for x in (-6.2,10.5): pbox(m,"mast",(x,4.4,z),(.14,4.4,.14))
    pbox(m,"mast",(2.2,8.0,z),(8.7,.1,.1)); pbox(m,"mast",(2.2,8.5,z),(8.7,.07,.07))
    for k in range(-8,9): pbox(m,"mast",(2.2+k*.5,8.25,z),(.03,.25,.03))
    for cx in TX: pbox(m,"black",(cx,7.4,z),(.05,.7,.05))
for cx in TX:
    pbox(m,"wire",(cx,6.9,(ZF+6)/2),(.015,.015,(6-ZF)/2)); pbox(m,"wire",(cx+.3,6.3,(ZF+6)/2),(.015,.015,(6-ZF)/2))
for x in (-6.2,10.5): pbox(m,"wire",(x,8.7,(ZF+6)/2),(.012,.012,(6-ZF)/2))
rnd=random.Random(8)
for i in range(70):
    side=rnd.choice([-1,1]); x=side*rnd.uniform(15,45)+(8 if side>0 else -4); z=-rnd.uniform(20,170); h=rnd.uniform(5,10)
    cyly(m,"trunk",.25,0,h*.55,x,z,6)
    for j in range(rnd.randint(3,5)):
        blob(m,rnd.choice(["tree1","tree2","tree3"]),(x+rnd.uniform(-2,2),h*.6+rnd.uniform(0,h*.5),z+rnd.uniform(-2,2)),rnd.uniform(2,3.6),.8)
for i in range(60): blob(m,"bush",(rnd.choice([-1,1])*rnd.uniform(9,16)+3,.4,-rnd.uniform(5,120)),rnd.uniform(.8,1.6),.6)
pbox(m,"hut",(-6.5,2.2,-70),(1.8,1.25,3.5)); pbox(m,"roofgrey",(-6.5,3.55,-70),(2.1,.12,3.8))
pbox(m,"mast",(1.9,3.0,-38),(.05,3.0,.05)); pbox(m,"black",(1.9,5.6,-38),(.18,.4,.12))
m.save("props.obj")

# ---------------- rolling stock
def bogie_at(m,cx,z):
    pbox(m,"black",(cx,.78,z),(.95,.13,1.55))
    for dz in (-1.0,1.0):
        for s in (-.84,.84): cylx(m,"wheel",.5,cx+s-.07,cx+s+.07,.65,z+dz,14)
        cylx(m,"dgrey",.09,cx-.84,cx+.84,.65,z+dz,6)
    for dz in (-1.0,1.0):
        for s in (-1,1): pbox(m,"dgrey",(cx+s*.9,.7,z+dz),(.07,.1,.3))
cx=TX[1]; ZO=3.0
# tank wagon (near, right of frame)
t=Mesh(); t.stack.append((L.I3,(0,0,ZO))); Ln=9.4; z0=-1.0; zc=z0-Ln/2; r=1.2
with placed(t,rotX(math.pi/2),(cx,2.25,zc)):
    lathe(t,[(0,-Ln/2+.3),(r*.7,-Ln/2+.3),(r,-Ln/2+.9),(r,Ln/2-.9),(r*.7,Ln/2-.3),(0,Ln/2-.3)],22,1,50)
t.save("tank.obj")
w=Mesh(); w.stack.append((L.I3,(0,0,ZO)))
pbox(w,"dgrey",(cx,1.0,zc),(1.2,.17,Ln/2+.2)); pbox(w,"wag2",(cx,1.28,zc),(.55,.18,Ln/2-.3))
for dz in (-Ln/2+1.4,Ln/2-1.4):
    pbox(w,"wag2",(cx,1.15,zc+dz),(1.35,.3,.12))
    for s in (-1,1): pbox(w,"rust",(cx+s*1.0,1.9,zc+dz),(.06,.9,.07))
pbox(w,"dgrey",(cx,3.67,zc),(.1,.1,Ln/2-1.5)); pbox(w,"dgrey",(cx,3.78,zc),(.5,.12,.5)); pbox(w,"wag2",(cx,3.9,zc),(.28,.1,.28))
for s in (-.2,.2): pbox(w,"dgrey",(cx-1.05,2.3,zc+Ln/2-.2+s),(.04,1.4,.035))
for k in range(9): pbox(w,"dgrey",(cx-1.05,1.2+k*.27,zc+Ln/2-.2),(.04,.03,.22))
for z in (-Ln/2+1.1,Ln/2-1.1): bogie_at(w,cx,zc+z)
with placed(w,L.I3,(cx-1.3,1.2,zc+Ln/2-.6)): cylx(w,"dgrey",.22,-.06,.06,0,0,10)
w.save("wagon.obj")

# box wagon + loco + coaches
m=Mesh(); m.stack.append((L.I3,(0,0,ZO)))
z0=-11.0; Ln=10.8; zc=z0-Ln/2
pbox(m,"dgrey",(cx,1.0,zc),(1.25,.17,Ln/2+.2)); pbox(m,"wag",(cx,2.55,zc),(1.3,1.45,Ln/2-.3))
pbox(m,"wag2",(cx,4.05,zc),(1.15,.1,Ln/2-.3)); pbox(m,"roofgrey",(cx,4.18,zc),(.8,.07,Ln/2-.5))
for s in (-1,1):
    for k in range(-3,4): pbox(m,"wag2",(cx+s*1.31,2.55,zc+k*Ln/7),(.03,1.45,.08))
    pbox(m,"wag2",(cx+s*1.32,2.7,zc),(.03,.08,Ln/2-.4)); pbox(m,"dgrey",(cx+s*1.33,2.55,zc),(.03,1.1,.9))
for z in (-Ln/2+1.3,Ln/2-1.3): bogie_at(m,cx,zc+z)
# locomotive
z0=-22.4; Ln=19.0; zc=z0-Ln/2; hw=1.55
pbox(m,"black",(cx,1.0,zc),(1.35,.18,Ln/2)); pbox(m,"dgrey",(cx,.7,zc),(1.0,.3,Ln/2-2.4))
hz0,hz1=z0-3.4,z0-Ln; hl=(hz0-hz1)/2; hc=(hz0+hz1)/2
pbox(m,"red",(cx,2.2,hc),(hw,.95,hl)); pbox(m,"orange",(cx,3.05,hc),(hw-.05,.35,hl)); pbox(m,"red2",(cx,3.45,hc),(hw-.4,.1,hl-.4))
for s in (-1,1):
    pbox(m,"yellow",(cx+s*(hw+.01),2.15,hc),(.01,.25,hl-.1))
    for k in range(7):
        zz=hc+hl*.9-k*(hl*1.8/6.5); pbox(m,"dgrey",(cx+s*(hw+.02),2.4,zz),(.01,.55,.28)); pbox(m,"black",(cx+s*(hw+.03),2.4,zz),(.01,.45,.18))
for k in range(3):
    zz=hz1+hl*.4+k*hl*.6; cyly(m,"dgrey",.5,3.55,3.75,cx,zz,12); cyly(m,"black",.4,3.75,3.8,cx,zz,12)
pbox(m,"dgrey",(cx,3.9,hz1+3),(.45,.3,.7))
cz0=z0; cz1=z0-3.4; cc=(cz0+cz1)/2
pbox(m,"red",(cx,2.75,cc),(1.6,1.45,1.7)); pbox(m,"orange",(cx,4.35,cc),(1.55,.2,1.7))
pbox(m,"roofgrey",(cx,4.62,cc),(1.45,.08,1.6)); pbox(m,"yellow",(cx,4.72,cc),(.4,.08,.7))
for s in (-1,1):
    pbox(m,"win",(cx+s*1.61,3.7,cz0-1.0),(.02,.45,.5)); pbox(m,"win",(cx+s*1.61,3.7,cz0-2.45),(.02,.45,.4))
    pbox(m,"white",(cx+s*1.62,3.0,cc),(.01,.07,1.5)); pbox(m,"yellow",(cx+s*1.62,2.2,cc),(.01,.25,1.6))
    for k in range(10): pbox(m,"white",(cx+s*(hw+.25),2.9,hc+hl-k*hl/4.5),(.02,.45,.02))
    pbox(m,"white",(cx+s*(hw+.25),3.4,hc),(.02,.02,hl)); pbox(m,"dgrey",(cx+s*(hw+.1),1.2,hc),(.1,.04,hl))
pbox(m,"win",(cx,3.7,cz0+.01),(1.3,.5,.02))
pbox(m,"lamp",(cx,4.45,cz0+.04),(.2,.1,.05)); pbox(m,"lamp",(cx-.7,1.55,cz0+.05),(.18,.15,.05)); pbox(m,"lamp",(cx+.7,1.55,cz0+.05),(.18,.15,.05))
for z in (z0-2.6,z0-Ln+2.6):
    pbox(m,"black",(cx,.82,z),(.95,.13,2.2))
    for dz in (-1.5,0,1.5):
        for s in (-.84,.84): cylx(m,"wheel",.5,cx+s-.07,cx+s+.07,.65,z+dz,14)
        cylx(m,"dgrey",.09,cx-.84,cx+.84,.65,z+dz,6)
# coaches
z=-42.0
for c in ["coach","coach","coach2","coach","coach","coach2","coach","coach"]:
    Ln=18.5; zc=z-Ln/2
    pbox(m,"dgrey",(cx,.95,zc),(1.35,.15,Ln/2)); pbox(m,c,(cx,2.4,zc),(1.45,1.35,Ln/2-.1)); pbox(m,"roofgrey",(cx,3.85,zc),(1.2,.12,Ln/2-.2))
    for s in (-1,1):
        for k in range(10): pbox(m,"win",(cx+s*1.46,2.7,z-1.8-k*(Ln-3.6)/9),(.02,.4,.45))
        pbox(m,"red",(cx+s*1.46,1.75,zc),(.01,.1,Ln/2-.2))
    for dz in (-Ln/2+2,Ln/2-2): bogie_at(m,cx,zc+dz)
    z-=19.2
m.save("train.obj")
print("done")
