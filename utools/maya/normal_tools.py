from maya import cmds
from maya import OpenMaya as om


# =================================================================================================
def alignRounded():
    """
    Select faces
    For each edge get the local Z as vector
    For each vertex in edge, apply the vector to vertex
    """
    
    selection = om.MSelectionList()
    om.MGlobal.getActiveSelectionList(selection)
    seliter = om.MItSelectionList(selection, om.MFn.kMeshEdgeComponent)
    dag = om.MDagPath()
    comp = om.MObject()
    
    verts = {}
    border = []
    faceverts = {}
    facelist = []
    
    while not seliter.isDone():
        seliter.getDagPath(dag, comp)
        
        mesh = om.MFnMesh(dag)
        
        ## -- Get all of our border edges:
        eiter = om.MItMeshEdge(dag)
        while not eiter.isDone():
            if eiter.onBoundary():
                border.append(eiter.index())
            
            eiter.next()
        
        ## -- Find normals of soft edges in selection
        eiter = om.MItMeshEdge(dag, comp)
        while not eiter.isDone():
            faces = om.MIntArray()
            eiter.getConnectedFaces(faces)
            facelist += faces
            
            veca = om.MVector()
            mesh.getPolygonNormal(faces[0], veca)
            if eiter.isSmooth():
                vecb = om.MVector()
                mesh.getPolygonNormal(faces[1], vecb)
                vec = veca + vecb
            else:
                vec = veca
                
            verts[eiter.index(0)] = vec
            verts[eiter.index(1)] = vec
            
            eiter.next()
        
        ## -- Find all vertices that are not connected to a hard edge
        viter = om.MItMeshVertex(dag)
        keys = verts.keys()
        
        while not viter.isDone():
            edges = om.MIntArray(4)
            viter.getConnectedEdges(edges)
            index = viter.index()
            if index in keys:
                for n in edges:
                    if n in border:
                        continue
                    
                    if not mesh.isEdgeSmooth(n) or n in border:
                        ## -- Connected to hard edge so remove it
                        f = om.MIntArray()
                        viter.getConnectedFaces(f)
                        f = set(f) & set(facelist)
                        faceverts[index] = [verts[index], list(f)]
                        del verts[index]
                        
                        break
            
            viter.next()
    
        seliter.next()
    
    cmds.undoInfo(ock=True)

    ## -- Set the normals of each vert
    for idx, vec in verts.iteritems():
        mesh.setVertexNormal(vec, idx)
    
    for idx, data in faceverts.iteritems():
        normal = data[0]
        flist = data[1]
        for f in flist:
            mesh.setFaceVertexNormal(normal, f, idx)
    
    cmds.undoInfo(cck=True)

# =================================================================================================
def lock(lock=True):
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
def unlock():
    """ Unlock all normals on selected meshes """
    lock(False)

# =================================================================================================
def setVertexNormalMethod(mode):
    """
    Sets the vertexNormalMethod attribute on all selected:
    0 - unweighted          2 - angle weighted
    1 - area weighted       3 - angle and area weighted
    :param mode: the mode to switch to
    :type mode: int
    """
    selection = cmds.ls(sl=True, l=True, o=True)
    if len(selection) == 0:
        cmds.error("No mesh selected")

    meshnodes = cmds.ls( selection, l=True, exactType='mesh', o=True)
    meshDescendents = cmds.listRelatives(selection, fullPath=True, allDescendents=True, type='mesh')
    meshnodes = meshnodes + meshDescendents

    for mesh in meshnodes:
        print mesh + 'changed'
        ext.setAttr (mesh, 'vertexNormalMethod', mode)

# =================================================================================================
def toggleVertexNormalDisplay():
    """ Sets the Vertex Normal display to all and the length to 0.05 """
    
    state = cmds.polyOptions(q=True, dn=True)
    if state is None:
        state = True
    else:
        state = state[0]
    cmds.polyOptions(gl=True, dn=not state, point=True, sizeNormal=0.05)

# =================================================================================================
def softNormals():
    """Sets all selected edges to soft"""
    selection = ext.getSelection()
    if selection:
        objects = list(set(ext.ls(selection, o=True)))
        for obj in objects:
            edges = [e for e in selection if ext.ls(e, o=True)[0] == obj]
            cmds.polySoftEdge(edges, a=180)

# =================================================================================================
def hardNormals():
    """Sets all selected edges to hard"""
    selection = ext.getSelection()
    if selection:
        objects = list(set(ext.ls(selection, o=True)))
        for obj in objects:
            edges = [e for e in selection if ext.ls(e, o=True)[0] == obj]
            cmds.polySoftEdge(edges, a=0)
