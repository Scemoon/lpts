# -*- coding:utf-8 -*-

import sys


class DespendException(Exception):
    '''
    缺少依赖
    '''
    def __init__(self, strs):
        self.strs = strs
        
    def __str__(self):
        return "deps check FAIL: %s" % self.strs

class TestException(Exception):
    '''
    测试异常
    '''
   
class CompileException(NameError): 
    '''
    '''
    
class ConfigToXmlException(Exception):
    '''
    '''

class CreateJobException(Exception):
    '''
    '''
  
class JobException(Exception):
    '''
    '''

class FormatterError(Exception):
    '''
    '''
    
class CalledProcessError(Exception):
    '''
    '''
    
class RunShellError(Exception):
    '''
    '''
    
class SaveTxtResultError(Exception):
    '''
    '''
    
class UnRootError(Exception):
    '''
    '''

class PermitsError(Exception):
    '''
    '''
    
class CleanError(Exception):
    '''定义清除日志Error
    '''
    def __init__(self, strs):
        self.strs = strs
    def __str__(self):
        return "Clean Env Error,详细信息: %s" % self.strs
    
class CreatNodeError(Exception):
    def __init__(self, strs):
        self.strs = strs
    def __str__(self):
        return "创建job节点Error,详细信息: %s" % self.strs
    
class TestOK(ValueError):
    ''''''
    
class MissXML(ValueError):
    ''''''

class SaveXMLError(Exception):
    ''''''