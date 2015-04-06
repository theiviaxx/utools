


from maya import OpenMaya as om
from maya import OpenMayaMPx as omx

import align_rounded
import align_auto
reload(align_auto)


def initializePlugin(obj):
    plugin = omx.MFnPlugin(obj, 'Brett Dixon', '0.1', 'Any')
    try:
        plugin.registerCommand('uAlignRounded', align_rounded.AlignRoundedCommand.creator)
        plugin.registerCommand('uAlignAuto', align_auto.AlignAutoCommand.creator)
    except:
        raise RuntimeError('Failed to register command')

def uninitializePlugin(obj):
    plugin = omx.MFnPlugin(obj)
    try:
        plugin.deregisterCommand('uAlignRounded')
        plugin.deregisterCommand('uAlignAuto')
    except:
        raise RuntimeError('Failed to unregister command')
