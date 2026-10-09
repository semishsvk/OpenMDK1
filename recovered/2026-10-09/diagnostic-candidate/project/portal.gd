extends RefCounted
static func in_range_or_cross(previous:float,current:float,lo:float,hi:float)->bool:
 return (lo<=current and current<=hi) or ((current<lo)!=(previous<lo)) or ((current<hi)!=(previous<hi))
static func query(previous:Vector3,current:Vector3)->int:
 if in_range_or_cross(previous.z,current.z,99,126) and in_range_or_cross(previous.x,current.x,-19,17) and current.y>654 and previous.y<=654:return 10
 return -1
