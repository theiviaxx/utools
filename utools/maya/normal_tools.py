from maya import cmds
from maya import OpenMaya as om

class NormalMode(object):
    Unweighted, AreaWeighted, AngleWeighted, AngleAreaWeighted = range(4)


# =================================================================================================
def lockNormals(lock=True):
    """ Lock all normals on selected meshes """
    selection = om.MSelectionList()
    om.MGlobal.getActiveSelectionList(selection)
    seliter = om.MItSelectionList(selection)
    dag = om.MDagPath()
    comp = om.MObject()
    mesh = None
    
    while not seliter.isDone():
        seliter.getDagPath(dag, comp)
        
        mesh = om.MFnMesh(dag)
        
        verts = om.MIntArray()
        viter = om.MItMeshVertex(dag)
        
        while not viter.isDone():
            verts.append(viter.index())
            
            viter.next()
    
        seliter.next()
    
    if not mesh:
        return False
    
    ## -- Set the normals of each vert
    if lock:
        mesh.lockVertexNormals(verts)
    else:
        mesh.unlockVertexNormals(verts)

# =================================================================================================
def unlockNormals():
    """ Unlock all normals on selected meshes """
    lockNormals(False)

# =================================================================================================
def setVertexNormalMethod(mode):
    """Sets the vertexNormalMethod attribute on all selected

    See `.NormalMode` for enums

    :param mode: the mode to switch to
    :type mode: int
    """
    selection = cmds.ls(sl=True, l=True, o=True)
    if len(selection) == 0:
        cmds.error("No mesh selected")

    meshnodes = cmds.ls(selection, l=True, exactType='mesh', o=True) or []
    meshnodes += cmds.listRelatives(selection, f=True, ad=True, type='mesh') or []

    for mesh in meshnodes:
        cmds.setAttr('{}.vertexNormalMethod'.format(mesh), mode)

# =================================================================================================
def toggleVertexNormalDisplay():
    """Sets the Vertex Normal display to all and the length to 0.05 """
    
    state = cmds.polyOptions(q=True, dn=True)
    if state is None:
        state = True
    else:
        state = state[0]
    cmds.polyOptions(gl=True, dn=not state, point=True, sizeNormal=0.05)

# =================================================================================================
def softNormals():
    """Sets all selected edges to soft"""
    selection = cmds.ls(sl=True, l=True)
    if selection:
        objects = list(set(cmds.ls(selection, o=True, l=True) or []))
        for obj in objects:
            edges = [e for e in selection if cmds.ls(e, o=True, l=True)[0] == obj]
            cmds.polySoftEdge(edges, a=180)

# =================================================================================================
def hardNormals():
    """Sets all selected edges to hard"""
    selection = cmds.ls(sl=True, l=True)
    if selection:
        objects = list(set(cmds.ls(selection, o=True, l=True) or []))
        for obj in objects:
            edges = [e for e in selection if cmds.ls(e, o=True, l=True)[0] == obj]
            cmds.polySoftEdge(edges, a=0)
