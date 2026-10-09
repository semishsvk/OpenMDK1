extends RefCounted
var state="IDLE"
var target=-1
var drains={"resource":false,"stage":false,"bind":false}
func begin(index:int):
 target=index
 state="RESOURCE_PENDING"
 drains.resource=true
func step():
 if state=="RESOURCE_PENDING":
  drains.resource=false
  drains.stage=true
  state="STAGE_PENDING"
 elif state=="STAGE_PENDING":
  drains.stage=false
  drains.bind=true
  state="BIND_PENDING"
 elif state=="BIND_PENDING":
  drains.bind=false
  state="SOURCE_COMMANDS"
 elif state=="SOURCE_COMMANDS":
  state="ACTIVE"
 return state
func active()->bool:return state=="ACTIVE"
func snapshot()->Dictionary:return {"state":state,"target":target,"drains":drains.duplicate()}
