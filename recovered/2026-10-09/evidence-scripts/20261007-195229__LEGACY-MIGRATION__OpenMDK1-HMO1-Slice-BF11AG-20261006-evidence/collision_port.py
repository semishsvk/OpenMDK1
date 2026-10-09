import struct
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
class Collision:
 def __init__(self,data,nodes,faces,vertices):
  self.data,self.nodes,self.faces,self.vertices=data,nodes,faces,vertices
 def triangle(self,point,normal,indices):
  # 0x42de60: project away dominant normal, count crossings on negative X ray.
  nx,ny,nz=map(abs,normal)
  axes=(1,2) if nx>ny and nx>nz else ((0,2) if ny>=nx and ny>nz else (0,1))
  xy=[]
  for index in indices:
   v=struct.unpack_from('<3f',self.data,self.vertices+12*index)
   xy.append(tuple(f32(v[k]-point[k]) for k in axes))
  count=0
  for i in range(3):
   x,y=xy[i];xx,yy=xy[(i+1)%3]
   if (y<0)==(yy<0):continue
   if x>=0 and xx>=0:count+=1;continue
   if x<0 and xx<0:continue
   # Mirrors x87 expression at 0x42DFE4: ((xx-x)*y)/(yy-y) compared with x.
   if ((xx-x)*y)/(yy-y)<x:count+=1
  return count%2==1
 def query(self,start,end):
  self.trace=[];self.face_trace=[];self.hit=None
  def leaf(node,field,point,normal):
   count,first=struct.unpack_from('<Hh',self.data,self.nodes+44*node+field)
   for fi in range(first,first+count):
    assert 0<=fi<399
    off=self.faces+36*fi
    if self.data[off+32]&32:continue
    self.face_trace.append(fi)
    if self.triangle(point,normal,struct.unpack_from('<3H',self.data,off)):
     self.hit=(node,fi,point);return True
   return False
  def walk(node):
   while node>=0:
    assert node<248
    self.trace.append(node)
    off=self.nodes+44*node
    nx,ny,nz,d=struct.unpack_from('<4f',self.data,off);normal=(nx,ny,nz)
    ds=f32(ny*start[1]+nx*start[0]+nz*start[2]+d)
    de=f32(ny*end[1]+nx*end[0]+nz*end[2]+d)
    neg,pos=struct.unpack_from('<2h',self.data,off+16)
    child=neg if ds<0 else pos
    if child>=0 and walk(child):return True
    if ds*de<0:
     denom=f32((end[1]-start[1])*ny+(end[0]-start[0])*nx+(end[2]-start[2])*nz)
     t=f32(-ds/denom) if denom else 1.0
     point=tuple(f32(start[k]+(end[k]-start[k])*t) for k in range(3))
     if leaf(node,20,point,normal) or leaf(node,24,point,normal):return True
     node=pos if ds<0 else neg
    else:return False
   return False
  walk(0)
  return self.hit
