
"""The AlignAuto command will take the last selected component and use its normal to set all
selected components to

vector variable will be 
"""
from maya import OpenMaya as om
from maya import OpenMayaMPx as omx


class AlignAutoCommand(omx.MPxCommand):
    def __init__(self):
        super(AlignAutoCommand, self).__init__()

        self._verts = []
        self._faceverts = [] # (face, vtx, normal)
        self._normal = om.MVector()
        self._currentverts = [] # (vtx, normal)
        self._currentfaceverts = [] # (face, vtx, normal)
        self._currentlocked = [] # (vtx, locked)
        self._currentfacelocked = [] # (face, vtx, locked)
        self._mesh = None

    def isUndoable(self):
        return True

    def doIt(self, args):
        self._verts = []
        self._faceverts = []
        border = []
        facelist = []
        
        selection = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(selection, True)

        ## -- Get last component
        dag = om.MDagPath()
        comp = om.MObject()
        if selection.length() == 0:
            return

        selection.getDagPath(selection.length() - 1, dag, comp)

        print comp.apiTypeStr()
        
        if comp.isNull():
            ## -- No selection?
            pass
        elif comp.apiType() == om.MFn.kMeshPolygonComponent:
            faceiter = om.MItMeshPolygon(dag, comp)
            while not faceiter.isDone():
                faceiter.getNormal(self._normal)
                faceiter.next()
        elif comp.apiType() == om.MFn.kMeshEdgeComponent:
            edgeiter = om.MItMeshEdge(dag, comp)
            while not edgeiter.isDone():
                mesh = om.MFnMesh(dag)
                veca = om.MPoint()
                vecb = om.MPoint()
                mesh.getPoint(edgeiter.index(0), veca)
                mesh.getPoint(edgeiter.index(1), vecb)
                self._normal = om.MVector(vecb) - om.MVector(veca)
                edgeiter.next()
        elif comp.apiType() == om.MFn.kMeshVertComponent:
            vertiter = om.MItMeshVertex(dag, comp)
            while not vertiter.isDone():
                vertiter.getNormal(self._normal)
                vertiter.next()

        # print vec.x, vec.y, vec.z

        # seliter = om.MItSelectionList(selection, om.MFn.kMeshPolygonComponent)
        # dag = om.MDagPath()
        # comp = om.MObject()
        # while not seliter.isDone():
        #     seliter.getDagPath(dag, comp)
            
        #     self._mesh = om.MFnMesh(dag)

        #     faceiter = om.MItMeshPolygon(dag, comp)
        #     while not faceiter.isDone():
        #         vertlist = om.MIntArray()
        #         self._mesh.getPolygonVertices(faceiter.index(), vertlist)
        #         self._verts[faceiter.index()] = list(vertlist)
        #         self._currentverts[faceiter.index()] = []
        #         for vtx in vertlist:
        #             vertnormal = om.MVector()
        #             self._mesh.getFaceVertexNormal(faceiter.index(), vtx, vertnormal)
        #             self._currentverts[faceiter.index()].append((vtx, vertnormal))

        #         faceiter.next()
            
        #     seliter.next()


        seliter = om.MItSelectionList(selection, om.MFn.kMeshPolygonComponent)
        dag = om.MDagPath()
        comp = om.MObject()
        while not seliter.isDone():
            seliter.getDagPath(dag, comp)
            
            self._mesh = om.MFnMesh(dag)
            nmlcount = om.MIntArray()
            nmlids = om.MIntArray()
            self._mesh.getNormalIds(nmlcount, nmlids)
            self._currentlocked = [(n, self._mesh.isNormalLocked(n)) for n in nmlids]

            ## -- Get our selected faces
            faceiter = om.MItMeshPolygon(dag, comp)
            while not faceiter.isDone():
                facelist.append(faceiter.index())

                nmlids = om.MIntArray()
                self._mesh.getFaceNormalIds(faceiter.index(), nmlids)
                self._currentfacelocked = [(faceiter.index(), n, self._mesh.isNormalLocked(n)) for n in nmlids]

                faceiter.next()

            faceset = set(facelist)
            
            ## -- Find normals of soft edges in selection
            eiter = om.MItMeshEdge(dag)
            while not eiter.isDone():
                faces = om.MIntArray(2)
                eiter.getConnectedFaces(faces)
                if set(faces) & faceset:
                    for faceidx in faces:
                        ## -- Get current normals
                        veca = om.MVector()
                        vecb = om.MVector()
                        self._mesh.getFaceVertexNormal(faceidx, eiter.index(0), veca)
                        self._mesh.getFaceVertexNormal(faceidx, eiter.index(1), vecb)

                        if faceidx in faceset:
                            ## -- Connected to our selection
                            if eiter.isSmooth():
                                self._verts.append((eiter.index(0), None))
                                self._verts.append((eiter.index(1), None))
                                self._currentverts.append((eiter.index(0), veca))
                                self._currentverts.append((eiter.index(1), vecb))
                            else:
                                ## -- Hard edge single face
                                self._faceverts.append((faceidx, eiter.index(0), None))
                                self._faceverts.append((faceidx, eiter.index(1), None))
                                self._currentfaceverts.append((faceidx, eiter.index(0), veca))
                                self._currentfaceverts.append((faceidx, eiter.index(1), vecb))
                        else:
                            if eiter.isSmooth():
                                self._verts.append((eiter.index(0), veca))
                                self._verts.append((eiter.index(1), vecb))
                                self._currentverts.append((eiter.index(0), veca))
                                self._currentverts.append((eiter.index(1), vecb))
                            else:
                                self._faceverts.append((faceidx, eiter.index(0), veca))
                                self._faceverts.append((faceidx, eiter.index(1), vecb))
                                self._currentfaceverts.append((faceidx, eiter.index(0), veca))
                                self._currentfaceverts.append((faceidx, eiter.index(1), vecb))
                
                eiter.next()
        
            seliter.next()

        self.redoIt()

    def undoIt(self):
        verts = []
        for vtx, nml in self._currentverts:
            if vtx in verts:
                continue
            self._mesh.setVertexNormal(nml, vtx)
            verts.append(vtx)

        for face, vtx, nml in self._currentfaceverts:
            self._mesh.setFaceVertexNormal(nml, face, vtx)


        locked = [i for i, n in self._currentlocked if n]
        util = om.MScriptUtil()
        arr = om.MIntArray()
        util.createIntArrayFromList(locked, arr)
        self._mesh.lockVertexNormals(arr)

        unlocked = [i for i, n in self._currentlocked if not n]
        util = om.MScriptUtil()
        arr = om.MIntArray()
        util.createIntArrayFromList(unlocked, arr)
        self._mesh.unlockVertexNormals(arr)

        # locked = [(f, i) for f, i, n in self._currentfacelocked if n]
        # if locked:
        #     faces, verts = zip(*locked)
        #     util = om.MScriptUtil()
        #     farr = om.MIntArray()
        #     util.createIntArrayFromList(faces, farr)

        #     util = om.MScriptUtil()
        #     varr = om.MIntArray()
        #     util.createIntArrayFromList(verts, varr)
        #     self._mesh.lockFaceVertexNormals(farr, varr)

        # unlocked = [(f, i) for f, i, n in self._currentfacelocked if not n]
        # if unlocked:
        #     faces, verts = zip(*unlocked)
        #     util = om.MScriptUtil()
        #     farr = om.MIntArray()
        #     util.createIntArrayFromList(faces, farr)

        #     util = om.MScriptUtil()
        #     varr = om.MIntArray()
        #     util.createIntArrayFromList(verts, varr)
        #     self._mesh.unlockFaceVertexNormals(farr, varr)


    def redoIt(self):
        # print self._verts
        for vtx, nml in self._verts:
            nml = nml or self._normal
            self._mesh.setVertexNormal(self._normal, vtx)

        #print self._faceverts
        for face, vtx, nml in self._faceverts:
            nml = nml or self._normal
            self._mesh.setFaceVertexNormal(nml, face, vtx)

    @staticmethod
    def creator():
        return omx.asMPxPtr(AlignAutoCommand())