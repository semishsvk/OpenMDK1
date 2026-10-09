extends RefCounted
var ir:Dictionary
var start:Vector3
var finish:Vector3
var result:Array=[]
func _init(data:Dictionary):
 ir=data
func f32(v:float)->float:
 return PackedFloat32Array([v])[0]
func triangle(point:Vector3, normal:Vector3, indices:Array)->bool:
 var n=normal.abs()
 var axes=[0,1]
 if n.x>n.y and n.x>n.z: axes=[1,2]
 elif n.y>=n.x and n.y>n.z: axes=[0,2]
 var xy=[]
 for index in indices:
  var v=ir.vertices[int(index)]
  xy.append(Vector2(f32(float(v[axes[0]])-point[axes[0]]),f32(float(v[axes[1]])-point[axes[1]])))
 var count=0
 for i in range(3):
  var p=xy[i]; var q=xy[(i+1)%3]
  if (p.y<0)==(q.y<0):continue
  if p.x>=0 and q.x>=0:count+=1;continue
  if p.x<0 and q.x<0:continue
  if ((q.x-p.x)*p.y)/(q.y-p.y)<p.x:count+=1
 return count%2==1
func leaf(node:int,field:int,point:Vector3,normal:Vector3)->bool:
 var spec=ir.nodes[node].leaves[field]
 for fi in range(int(spec[1]),int(spec[1])+int(spec[0])):
  var face=ir.collision_faces[fi]
  if int(face.flags)&32:continue
  if triangle(point,normal,face.indices):
   result=[node,fi,point];return true
 return false
func walk(node:int)->bool:
 while node>=0:
  var record=ir.nodes[node];var p=record.plane
  var normal=Vector3(p[0],p[1],p[2])
  var ds=f32(normal.y*start.y+normal.x*start.x+normal.z*start.z+float(p[3]))
  var de=f32(normal.y*finish.y+normal.x*finish.x+normal.z*finish.z+float(p[3]))
  var child=int(record.negative) if ds<0 else int(record.positive)
  if child>=0 and walk(child):return true
  if ds*de<0:
   var denom=f32((finish.y-start.y)*normal.y+(finish.x-start.x)*normal.x+(finish.z-start.z)*normal.z)
   var t=f32(-ds/denom) if denom!=0 else 1.0
   var point=Vector3(f32(start.x+(finish.x-start.x)*t),f32(start.y+(finish.y-start.y)*t),f32(start.z+(finish.z-start.z)*t))
   if leaf(node,0,point,normal) or leaf(node,1,point,normal):return true
   node=int(record.positive) if ds<0 else int(record.negative)
  else:return false
 return false
func query(a:Vector3,b:Vector3)->Array:
 start=a;finish=b;result=[];walk(0);return result
