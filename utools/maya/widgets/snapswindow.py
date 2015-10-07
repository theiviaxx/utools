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

"""Snaps Window"""

from functools import partial
from fractions import Fraction

from maya import cmds

from PySide import QtGui, QtCore

from utools.maya import snaps
from utools.maya import common

class SnapsWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(SnapsWindow, self).__init__(parent)
        
        self.setWindowTitle('Snaps')
        
        widget = QtGui.QWidget(self)
        self.setCentralWidget(widget)
        self._layout = QtGui.QVBoxLayout(widget)
        self.setStyleSheet('QPushButton:checked {background-color: rgb(60, 160, 255); }')
        
        self.buildMove()
        self.buildRotate()
        self.buildGrid()
        
        self.setMaximumSize(QtCore.QSize(226, 184))
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        
    def buildMove(self):
        group = QtGui.QGroupBox(self)
        group.setTitle('Move')
        group.setCheckable(True)
        group.setChecked(cmds.manipMoveContext('Move', q=True, snap=True))
        group.toggled.connect(lambda x: snaps.enableSnap(x, 'Move'))
        group.setFlat(True)
        layout = QtGui.QGridLayout(group)
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(group)
        
        btngroup = QtGui.QButtonGroup(self)

        current = cmds.manipMoveContext('Move', q=True, snapValue=True)
        
        s = 4.0
        for i in xrange(10):
            col = i % 5
            row = 0 if i < 5 else 1
            btn = QtGui.QPushButton(group)
            btn.setCheckable(True)
            btn.setChecked(current == s)
            btn.setMinimumWidth(40)
            btn.setText(str(Fraction(str(s))))
            btn.clicked.connect(partial(snaps.setSnapValue, s, 'Move'))
            layout.addWidget(btn, row, col)
            btngroup.addButton(btn)
            
            s /= 2.0

    def buildRotate(self):
        group = QtGui.QGroupBox(self)
        group.setTitle('Rotate')
        group.setCheckable(True)
        group.setChecked(cmds.manipRotateContext('Rotate', q=True, snap=True))
        group.toggled.connect(lambda x: snaps.enableSnap(x, 'Rotate'))
        group.setFlat(True)
        layout = QtGui.QHBoxLayout(group)
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(group)
        
        btngroup = QtGui.QButtonGroup(self)

        current = cmds.manipRotateContext('Rotate', q=True, snapValue=True)
        
        values = [15, 30, 45, 90, 180]
        
        for value in values:
            btn = QtGui.QPushButton(group)
            btn.setCheckable(True)
            btn.setChecked(int(current) == value)
            btn.setMinimumWidth(40)
            btn.setText(str(value))
            btn.clicked.connect(partial(snaps.setSnapValue, value, 'Rotate'))
            layout.addWidget(btn)
            btngroup.addButton(btn)

    def buildGrid(self):
        state = cmds.grid(q=True, toggle=True)
        group = QtGui.QGroupBox(self)
        group.setTitle('Grid')
        group.setCheckable(True)
        group.setChecked(state)
        group.toggled.connect(snaps.enableGrid)
        group.setFlat(True)
        layout = QtGui.QGridLayout(group)
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(group)
        
        btngroup = QtGui.QButtonGroup(self)
        
        values = [1, 2, 4, 8, 16, 32, 64, 128]
        current = cmds.grid(q=True, spacing=True)
        row = 0
        
        for i, value in enumerate(values):
            if i > 3:
                row = 1
            btn = QtGui.QPushButton(group)
            btn.setCheckable(True)
            btn.setChecked(current == value)
            btn.setMinimumWidth(40)
            btn.setText(str(Fraction(str(value))))
            btn.clicked.connect(partial(snaps.setGridSpacing, value))
            layout.addWidget(btn, row, i % 4)
            btngroup.addButton(btn)


def main():
    win = SnapsWindow(common.getMayaWindow())
    win.show()

    return win
