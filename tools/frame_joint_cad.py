"""Selected hybrid: wedge post sleeve + axially screwed male rail cup."""
from frame_joint_wedge_cad import build as wedge_parts
from frame_joint_clamp_cad import build as clamp_parts
MODEL_VERSION='frame-cad-wedge-axial-v5'
def build(p):
 parts=wedge_parts(p)
 parts['male']=clamp_parts(p)['male']
 return parts
