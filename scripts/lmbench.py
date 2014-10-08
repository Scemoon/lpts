#!/usr/bin/env python
#/usr/bin/env python
# - *- coding:utf-8 -*-

import os, sys  
import importlib  
try:
    import lpt
except ImportError:
    import init_env
    current_dir = os.path.split(os.path.realpath('__file__'))[0]
    lptroot = os.path.split(current_dir)[0]
    init_env.setup(lptroot)
    if not os.getenv('LPTROOT'):
        os.environ['LPTROOT'] = lptroot
    
from lpt.lib import lptxml
from lpt.lib.error import *
from lpt.lib import lptlog
from lpt.tests import control

#LPT Directory
LPTROOT = os.getenv('LPTROOT')
RESULTS = os.path.join(LPTROOT, 'results')
TOOLSDIR = os.path.join(LPTROOT, 'tools')
TMPDIR = os.path.join(LPTROOT, 'tmp')
SRCDIR = os.path.join(LPTROOT, 'src')

class Lmbench:
    '''lmbench Run method'''
    def __init__(self):
        pass
    
    def setup(self):
        pass
    
    def run(self):
        pass
    
    def create_report(self):
        pass
    
    