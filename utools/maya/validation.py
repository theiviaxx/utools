"""Scene Validation for Maya

>>> from utools.maya import validation
>>> runner = validation.Runner()
>>> runner.discover('path/to/tests')
>>> runner.start()
"""

from __future__ import print_function

import time
import imp
import logging
from collections import namedtuple

import six
import path
from PySide import QtGui, QtCore

from utools.maya import common
from utools.maya.widgets import validator_res

logging.basicConfig()
LOGGER = logging.getLogger('Validation')
LOGGER.setLevel(logging.INFO)
PROGRESS_ROLE = QtCore.Qt.UserRole + 1
PROGRESS_COLOR = QtGui.QColor('#64b5f6')
BUTTON_SIZE = 56
WINDOW = None
STYLE = """
QWidget {
    color: #fff;
    font-family: Roboto;
    font-size: 14px;
}
QWidget:focus {
    border: none;
}
QAbstractItemView::indicator {
    width: 24px;
    height: 24px;
    background-image: url(':/ui/res/ic_check_box_white_24dp_1x.png');
}
QAbstractItemView::indicator:unchecked {
    background-image: url(':/ui/res/ic_check_box_outline_blank_white_24dp_1x.png');
}
QAbstractItemView::branch:open:has-children {
    image: url(':/ui/res/ic_expand_more_white_24dp_2x.png');
}
QAbstractItemView::branch:closed:has-children {
    image: url(':/ui/res/ic_closed_white_24dp_2x.png');
}
#ListValidators {background-color: #373737}
    QFrame {background-color: #303030 }
    QPushButton {
    border: none;
    background-color: transparent;
    background-image: url(':/ui/res/ic_play_arrow_color_24dp_2x.png');
}
#FrameResults QPushButton:hover {
    background-image: url(':/ui/res/ic_play_arrow_color_hover_24dp_2x.png');
}
#FrameResults QPushButton:checked {
    background-image: url(':/ui/res/ic_stop_color_24dp_2x.png');
}
#FrameResults QLabel {
    padding: 12px;
    font-size: 30px;
    background-color: #484848;
}
#FrameResults QLabel#Timing {
    font-size: 10px;
    padding: 0 0 0 20px;
    background-color: transparent;
}
"""


class ValidatorError(Exception):
    """Raised when a validator causes an unhandled exception"""


class StopValidating(Exception):
    """Raised to short circuit the Runner generator"""


class ValidationRegistry(type):
    plugins = {}
    def __init__(cls, name, bases, attrs):
        if name != 'Validator':
            ValidationRegistry.plugins[name] = cls()


class Validator(six.with_metaclass(ValidationRegistry, object)):
    Result = namedtuple('Result', ['node', 'message'])
    ENABLED = True

    def __init__(self):
        self._count = 1
        self._errors = []
        self._warnings = []
        self._enabled = self.ENABLED

    def __repr__(self):
        return self.__class__.__name__

    @property
    def count(self):
        return self._count
    
    @property
    def errors(self):
        return self._errors
    
    @property
    def warnings(self):
        return self._warnings

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled

    def run(self, selection=False, references=False):
        """Abstract method to be run by the runner and implemented by a subclass"""

    def action(self):
        """Abstract method to be run if no object is in an error result"""

    def reset(self):
        self._count = 1
        self._errors = []
        self._warnings = []


class Runner(object):
    """Discovers and runs Validator tests on the current scene"""
    def __init__(self):
        self._running = False
        self._canceled = False
        self._validators = []
        self._validator = None
        self._count = 0
        self._timestart = 0.0
        self._timeend = 0.0

    def start(self, selection=False, references=False):
        """Start running tests"""
        self._count = 0
        self._timeend = 0.0
        self._timestart = time.clock()
        self._running = True
        self._canceled = False
        LOGGER.info('Started validations')

        try:
            for validator in self._validators:
                validator.reset()
                if not validator.enabled:
                    continue
                self._validator = validator
                LOGGER.info('Validating %s', self._validator)

                try:
                    for i, r in enumerate(self._validator.run(selection, references)):
                        if self._canceled:
                            raise StopValidating

                        self._count += 1
                        yield self._validator, i
                except StopValidating:
                    raise
                except Exception as err:
                    raise ValidatorError(err)
        except StopValidating:
            # -- Just exit the loop
            pass

        self._timeend = time.clock()
        self._running = False
        LOGGER.info('Validations took {:.2f}s'.format(self.duration))
        raise StopIteration

    def stop(self):
        """Stop running tests"""
        self._canceled = True

    def discover(self, directories):
        """Find classes in `directories` that are subclasses of Validator"""
        self._validators = []

        for dir_ in directories:
            for pyfile in path.path(dir_).files('*.py'):
                modname = pyfile.namebase
                fp, pathname, description = imp.find_module(modname, [dir_])
                if fp:
                    LOGGER.debug('Found validation in %s', pathname)
                    imp.load_module(modname, fp, pathname, description)

        self._validators = list(ValidationRegistry.plugins.values())

    @property
    def running(self):
        return self._running

    @property
    def canceled(self):
        return self._canceled

    @property
    def validators(self):
        return self._validators

    @validators.setter
    def validators(self, validators):
        self._validators = validators

    @property
    def validator(self):
        return self._validator

    @property
    def errors(self):
        errors = 0
        for validator in self._validators:
            errors += len(validator.errors)

        return errors

    @property
    def warnings(self):
        warnings = 0
        for validator in self._validators:
            warnings += len(validator.warnings)

        return warnings

    @property
    def count(self):
        return self._count

    @property
    def duration(self):
        return self._timeend - self._timestart

##############################################################################
# Window
##############################################################################

class ResultFrame(QtGui.QFrame):
    def resizeEvent(self, event):
        for child in self.children():
            if isinstance(child, QtGui.QPushButton):
                child.move((self.width() / 2) - (child.width() / 2), 40)
                child.raise_()

        return super(ResultFrame, self).resizeEvent(event)


class ValidatorDelegate(QtGui.QStyledItemDelegate):
    def paint(self, painter, option, index):
        option = QtGui.QStyleOptionViewItemV4(option)
        painter.setRenderHints(QtGui.QPainter.TextAntialiasing)

        # -- Draw icon
        if index.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
            pixmap = QtGui.QPixmap(':/ui/res/ic_check_box_white_24dp_1x.png')
        else:
            pixmap = QtGui.QPixmap(':/ui/res/ic_check_box_outline_blank_white_24dp_1x')
        painter.drawPixmap(option.rect.left() + 16, option.rect.center().y() - 8, pixmap)

        # -- Draw text
        font = QtGui.QFont('Roboto', 12)
        painter.setFont(font)
        painter.drawText(
            option.rect.left() + 48,
            option.rect.center().y() + 8,
            index.data(QtCore.Qt.DisplayRole)
        )

        # -- Draw progress        
        progress = index.data(PROGRESS_ROLE)
        if progress:
            rect = option.rect
            rect.setY(rect.y() + rect.height())
            rect.setHeight(4)
            
            rect.setWidth(rect.width() * progress )
            painter.fillRect(rect, PROGRESS_COLOR)

    def sizeHint(self, option, index):
        return QtCore.QSize(100, 48)


class ResultModel(QtGui.QStandardItemModel):
    DAG_ROLE = QtCore.Qt.UserRole + 1
    MESSAGE_ROLE = DAG_ROLE + 1
    def __init__(self, *args):
        super(ResultModel, self).__init__(*args)

        self._role = self.DAG_ROLE

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole and index.parent().isValid():
            role = self._role

        return super(ResultModel, self).data(index, role)



class ValidationWindow(QtGui.QMainWindow):
    itemSelected = QtCore.Signal(list)

    def __init__(self, runner, parent=None):
        super(ValidationWindow, self).__init__(parent)

        self.setStyleSheet(STYLE)

        self._runner = runner
        self._validatormodel = QtGui.QStandardItemModel()
        self._resultmodel = ResultModel()

        self.build()

        self.lvValidators.setModel(self._validatormodel)
        self.tvResults.setModel(self._resultmodel)
        self.lvValidators.setItemDelegate(ValidatorDelegate())

        self.bRun.toggled.connect(self.toggleRun)
        selectionmodel = self.tvResults.selectionModel()
        selectionmodel.selectionChanged.connect(self.selectionChangedHandler)

        for validator in runner.validators:
            item = QtGui.QStandardItem(str(validator))
            item.setData(validator, QtCore.Qt.UserRole)
            item.setCheckable(True)
            state = QtCore.Qt.Checked if validator.enabled else QtCore.Qt.Unchecked
            item.setCheckState(state)
            item.setEditable(False)
            self._validatormodel.appendRow(item)

        self.resize(800, 600)

    def keyReleaseEvent(self, event):
        event.accept()
        self._resultmodel._role = ResultModel.DAG_ROLE
        self.tvResults.update()

    def keyPressEvent(self, event):
        if event.modifiers() == QtCore.Qt.ControlModifier:
            event.accept()
            self._resultmodel._role = ResultModel.MESSAGE_ROLE
            self.tvResults.update()

    def build(self):
        widget = QtGui.QWidget(self)
        layout = QtGui.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(widget)

        # -- Validators
        self.lvValidators = QtGui.QListView(widget)
        self.lvValidators.setObjectName('ListValidators')
        self.lvValidators.clicked.connect(self.checked)

        # -- Results
        self.fResults = ResultFrame(widget)
        self.fResults.setObjectName('FrameResults')
        resultlayout = QtGui.QVBoxLayout(self.fResults)
        resultlayout.setContentsMargins(0, 0, 0, 0)
        resultlayout.setSpacing(0)
        labelwidget = QtGui.QWidget(self.fResults)
        rowlayout = QtGui.QHBoxLayout(labelwidget)
        rowlayout.setContentsMargins(0, 0, 0, 0)
        rowlayout.setSpacing(0)
        self.lResult = QtGui.QLabel('Ready', labelwidget)
        # self.lWarnings = QtGui.QLabel(labelwidget)
        self.lResultIcon = QtGui.QLabel(labelwidget)
        self.lResultIcon.setMaximumWidth(48)
        rowlayout.addWidget(self.lResult)
        rowlayout.addWidget(self.lResultIcon)
        self.lTiming = QtGui.QLabel(self.fResults)
        self.lTiming.setObjectName('Timing')
        self.tvResults = QtGui.QTreeView(self.fResults)
        self.tvResults.setHeaderHidden(True)
        self.tvResults.setSelectionMode(QtGui.QTreeView.ExtendedSelection)
        self.tvResults.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tvResults.setIndentation(30)
        resultlayout.addWidget(labelwidget)
        resultlayout.addWidget(self.lTiming)
        resultlayout.addWidget(self.tvResults)

        # -- Run button
        self.bRun = QtGui.QPushButton(self.fResults)
        self.bRun.setCheckable(True)
        self.bRun.setObjectName('bRun')
        self.bRun.setMinimumSize(BUTTON_SIZE, BUTTON_SIZE)
        self.bRun.setMaximumSize(self.minimumSize())
        self.bRun.setAutoFillBackground(False)

        layout.addWidget(self.lvValidators)
        layout.addWidget(self.fResults)
        layout.setStretch(1, 1)

    def checked(self, index):
        item = self._validatormodel.itemFromIndex(index)
        state = QtCore.Qt.Checked if item.checkState() != QtCore.Qt.Checked else QtCore.Qt.Unchecked        
        item.setCheckState(state)
        self._runner.validators[item.row()].enabled = state

    def toggleRun(self):
        state = self.bRun.isChecked()
        if state:
            self.run()
        else:
            self._runner.stop()

    def run(self):
        self._resultmodel.clear()
        loop = QtCore.QEventLoop(self)
        for v, i in self._runner.start():
            item = self._validatormodel.findItems(str(self._runner.validator))[0]
            item.setData((i + 1) / float(v.count), PROGRESS_ROLE)
            loop.processEvents()

        for validator in self._runner.validators:
            if not validator.errors and not validator.warnings:
                continue

            parent = QtGui.QStandardItem(str(validator))
            font = parent.font()
            font.setPixelSize(18)
            parent.setFont(font)
            parent.setSizeHint(QtCore.QSize(100, 54))
            parent.setEditable(False)
            parent.setSelectable(False)
            self._resultmodel.appendRow(parent)
            for err in validator.errors:
                item = QtGui.QStandardItem()
                item.setData(err.message, ResultModel.MESSAGE_ROLE)
                item.setEditable(False)
                if err.node:
                    item.setData(err.node, ResultModel.DAG_ROLE)
                else:
                    item.setData(err.message, ResultModel.DAG_ROLE)
                

                parent.appendRow(item)
        self.tvResults.expandAll()
        self.lTiming.setText('Duration: {:.2f}s'.format(self._runner.duration))

        self.setStatus()
        self.bRun.setChecked(False)

    def selectionChangedHandler(self, selection, deselection):
        selectionmodel = self.tvResults.selectionModel()
        self.itemSelected.emit([s.data(ResultModel.DAG_ROLE) for s in selectionmodel.selectedIndexes() if s.parent().isValid()])

    def setStatus(self):
        if self._runner.errors:
            self.lResult.setText('Errors {}'.format(self._runner.errors))
            self.lResultIcon.setStyleSheet("background-image: url(':/ui/res/ic_error_white_24dp_2x.png');background-repeat: no-repeat;")
            self.lResult.parent().setStyleSheet('background-color: #f44336;')
        else:
            self.lResult.setText('Success')
            self.lResultIcon.setStyleSheet("background-image: url(':/ui/res/ic_done_white_24dp_2x.png');background-repeat: no-repeat;")
            self.lResult.parent().setStyleSheet('background-color: #64b5f6;')


def main(callback=None):
    global WINDOW
    if WINDOW:
        WINDOW.close()

    runner = Runner()
    runner.discover((r"C:\tmp\validation",))
    WINDOW = ValidationWindow(runner, common.getMayaWindow())
    if callback:
        WINDOW.itemSelected.connect(callback)
    WINDOW.show()

    
    
    
    
    