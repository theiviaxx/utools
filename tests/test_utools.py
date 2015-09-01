#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_utools
----------------------------------

Tests for `utools` module.
"""

import os
import unittest


from utools.maya import validation


class TestUtools(unittest.TestCase):

    def setUp(self):
        pass

    def test_something(self):
        pass

    def tearDown(self):
        pass


class TestValidation(unittest.TestCase):
    def test_runner(self):
        runner = validation.Runner()
        runner.discover([os.path.dirname(os.path.abspath(__file__))])
        self.assertEqual(len(runner.validators), 1)
        list(runner.start())

        self.assertEqual(len(runner.errors), 1)
        self.assertEqual(runner.errors[0].node, None)
        self.assertEqual(runner.errors[0].message, 'loop error')
        self.assertTrue(runner.duration > 0.9)



if __name__ == '__main__':
    unittest.main()