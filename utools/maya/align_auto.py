##################################################################################################
# Copyright (c) 2014 Brett Dixon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
# Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##################################################################################################

"""The AlignAuto command will take the last selected component and use its normal to set all
selected component's normals to.  For example if you select several faces then a vertex, this will
use the vertex normal and set all selected faces to that normal.
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
        self._mesh = None

    def isUndoable(self):
        return True

    def doIt(self, args):
        border = []
        facelist = []
        
        selection = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(selection, True)

        dag = om.MDagPath()
        comp = om.MObject()
        if selection.length() == 0:
            return

        ## -- Get last component
        selection.getDagPath(selection.length() - 1, dag, comp)
        
        if comp.apiType() == om.MFn.kMeshPolygonComponent:
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

        ## -- Reset locked/unlocked normals
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

    def redoIt(self):
        for vtx, nml in self._verts:
            nml = nml or self._normal
            self._mesh.setVertexNormal(self._normal, vtx)

        for face, vtx, nml in self._faceverts:
            nml = nml or self._normal
            self._mesh.setFaceVertexNormal(nml, face, vtx)

    @staticmethod
    def creator():
        return omx.asMPxPtr(AlignAutoCommand())