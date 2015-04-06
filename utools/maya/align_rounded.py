from maya import OpenMaya as om
from maya import OpenMayaMPx as omx


class AlignRoundedCommand(omx.MPxCommand):
    def __init__(self):
        super(AlignRoundedCommand, self).__init__()

        self._verts = {}
        self._faceverts = {}
        self._currentnormals = []
        self._currentfacenormals = []
        self._mesh = None

    def isUndoable(self):
        return True

    def doIt(self, args):
        self._verts = {}
        self._faceverts = {}
        border = []
        facelist = []
        
        selection = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(selection)
        seliter = om.MItSelectionList(selection, om.MFn.kMeshEdgeComponent)
        dag = om.MDagPath()
        comp = om.MObject()
        
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
                    # self._currentedges[mesh].append(eiter.index())
                    vecb = om.MVector()
                    mesh.getPolygonNormal(faces[1], vecb)
                    vec = veca + vecb
                else:
                    vec = veca
                    
                self._verts[eiter.index(0)] = vec
                self._verts[eiter.index(1)] = vec
                
                eiter.next()
            
            ## -- Find all vertices that are not connected to a hard edge
            viter = om.MItMeshVertex(dag)
            keys = self._verts.keys()
            
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
                            self._faceverts[index] = [self._verts[index], list(f)]
                            del self._verts[index]
                            
                            break
                
                viter.next()
        
            seliter.next()

        self._mesh = mesh
        for idx, vec in self._verts.iteritems():
            normal = om.MVector()
            self._mesh.getVertexNormal(idx, normal)
            self._currentnormals.append((idx, normal))
        
        for idx, data in self._faceverts.iteritems():
            flist = data[1]
            for f in flist:
                normal = om.MVector()
                self._mesh.getFaceVertexNormal(f, idx, normal)
                self._currentfacenormals.append(f, idx, normal)


        self.redoIt()

    def undoIt(self):
        for idx, normal in self._currentnormals:
            self._mesh.setVertexNormal(normal, idx)

        for f, idx, normal in self._currentfacenormals:
            self._mesh.getFaceVertexNormal(normal, f, idx)

    def redoIt(self):
        for idx, vec in self._verts.iteritems():
            self._mesh.setVertexNormal(vec, idx)
        
        for idx, data in self._faceverts.iteritems():
            normal = data[0]
            flist = data[1]
            for f in flist:
                self._mesh.setFaceVertexNormal(normal, f, idx)

    @staticmethod
    def creator():
        return omx.asMPxPtr(AlignRoundedCommand())