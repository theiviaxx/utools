UBD Tools
===============================


* Free software: MIT license

Features
------------

* SnapWindow
  * To use:

```python
from utools.maya import common
from utools.maya.widgets import snapswindow

win = snapswindow.SnapsWindow(common.getMayaWindow())
win.show()
```

* Normals command
  * `cmds.uAlignRounded()`
  * `cmds.uAlignAuto()`