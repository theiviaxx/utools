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

"""Transform snap functions"""

from maya import cmds

from utools.maya import common


def enableSnap(enable, context):
    if context == 'Move':
        cmds.manipMoveContext(context, e=True, snap=enable)
    else:
        cmds.manipRotateContext(context, e=True, snap=enable)

def enableGrid(enable):
    cmds.grid(toggle=enable)
    cmds.optionVar(sv=('showGrid', enable))

def setSnapValue(val, context):
    if context == 'Move':
        cmds.manipMoveContext(context, e=True, snapValue=val)
    else:
        cmds.manipRotateContext(context, e=True, snapValue=val)

def setGridSpacing(div):
    kwargs = {
        'size': 20,
        'spacing': 1,
        'divisions': div,
        'displayAxes': True,
        'displayAxesBold': True,
        'displayGridLines': True,
        'displayDivisionLines': True
    }
    
    cmds.grid(**kwargs)
    
    uvpanel = cmds.getPanel(sty='polyTexturePlacementPanel')
    uvpanelexists = cmds.textureWindow(
        uvpanel[0],
        q=True,
        exists=True,
    )
    if uvpanelexists:
        spacing = cmds.textureWindow(uvpanel[0], q=True, spacing=True)
        
        if spacing <= 1:
            setUVGrid(kwargs['spacing'])
    
    cmds.optionVar(floatValue=('gridSpacing', kwargs['spacing']))
    cmds.optionVar(floatValue=('gridDivisions', kwargs['divisions']))
    cmds.optionVar(floatValue=('gridSize', kwargs['size']))
    cmds.optionVar(intValue=('displayGridAxes', kwargs['displayAxes']))
    cmds.optionVar(intValue=('displayGridLines', kwargs['displayGridLines']))
    cmds.optionVar(intValue=('displayGridAxesAccented', kwargs['displayAxesBold']))
    cmds.optionVar(intValue=('displayDivisionLines', kwargs['displayDivisionLines']))
    cmds.optionVar(floatValue=('textureWindowGridDivisions', kwargs['divisions']))
    
    common.focusViewport()

def setUVGrid(spacing):
    uvpanel = cmds.getPanel(sty='polyTexturePlacementPanel')[0]
    
    if not cmds.textureWindow(uvpanel, exists=True):
        return False
    
    kwargs = {
        'e': True,
        'divisions': cmds.grid(q=True, d=True),
        'spacing': spacing,
        'size': 2,
        'displayAxes': True,
        'displayGridLines': True,
        'displayDivisionLines': True,
    }
    
    cmds.textureWindow(uvpanel, **kwargs)
    
    for k, v in kwargs.items():
        if k == 'e':
            continue
        
        if k.startswith('display'):
            var = 'textureWindow%s' % k.capitalize()
        else:
            var = 'textureWindowGrid%s' % k.capitalize()
        cmds.optionVar(fv=(var, v))
    
    common.focusViewport()
