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

logging.basicConfig()
LOGGER = logging.getLogger('Validation')
LOGGER.setLevel(logging.INFO)


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
        return '<Validator: {}>'.format(self.__class__.__name__)

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
        return self._enabled and self.visible

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
        LOGGER.info('Started validations')

        try:
            for validator in self._validators:
                self._validator = validator
                self._validator.reset()
                LOGGER.info('Validating %s', self._validator)

                try:
                    for i, r in enumerate(self._validator.run(selection, references)):
                        if self._canceled:
                            raise StopValidating

                        self._count += 1
                        yield self._validator, i
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
    
    

FORM, BASE = common.loadUiType(path.path(__file__).expand().parent / 'widgets' / 'validation_window.ui')
WINDOW = None
class ValidationWindow(FORM, BASE):
    itemSelected = QtCore.Signal(list)

    def __init__(self, runner, parent=None):
        super(ValidationWindow, self).__init__(parent)

        self.setupUi(self)

        self._runner = runner
        self._validatormodel = QtGui.QStandardItemModel()
        self._resultmodel = QtGui.QStandardItemModel()

        self.lvValidators.setModel(self._validatormodel)
        self.tvResults.setModel(self._resultmodel)

        self.bRun.clicked.connect(self.run)
        selectionmodel = self.tvResults.selectionModel()
        selectionmodel.selectionChanged.connect(self.selectionChangedHandler)

        runner.discover((r"C:\tmp\validation",))
        for validator in runner.validators:
            item = QtGui.QStandardItem(str(validator))
            item.setData(validator, QtCore.Qt.UserRole)
            self._validatormodel.appendRow(item)

    def run(self):
        for v, i in self._runner.start():
            print(v.count, i)

        self._resultmodel.clear()

        for validator in self._runner.validators:
            parent = QtGui.QStandardItem(str(validator))
            self._resultmodel.appendRow(parent)
            for err in validator.errors:
                if err.node:
                    item = QtGui.QStandardItem(err.node)
                else:
                    item = QtGui.QStandardItem(err.message)

                parent.appendRow(item)
        self.tvResults.expandAll()

        self.setStatus('err')

    def selectionChangedHandler(self, selection, deselection):
        selectionmodel = self.tvResults.selectionModel()
        self.itemSelected.emit([s.data() for s in selectionmodel.selectedIndexes() if s.parent().isValid()])

    def setStatus(self, status):
        if status == 'success':
            self.lStatusText.setText('Success')
            self.lStatusText.parent().setObjectName('Success')
        else:
            self.lStatusText.setText('Errors {}'.format(self._runner.errors))
            self.lStatusText.parent().setObjectName('Error')

        self.lStatusText.parent().style().unpolish(self.lStatusText.parent())
        self.lStatusText.parent().style().polish(self.lStatusText.parent())
        self.lStatusText.parent().update()


def main(callback=None):
    global WINDOW
    if WINDOW:
        WINDOW.close()

    runner = Runner()
    WINDOW = ValidationWindow(runner, common.getMayaWindow())
    if callback:
        WINDOW.itemSelected.connect(callback)
    WINDOW.show()

    
    
    
    
    