import time

from maya import cmds

from utools.maya.validation import Validator


class Loop(Validator):
    def run(self, *args):
        self._count = 11
        for i in xrange(self._count - 1):
            time.sleep(0.1)
            yield

        self._errors.append(Validator.Result(None, 'loop error'))

        yield
