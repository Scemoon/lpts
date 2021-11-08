# -*- coding:utf-8 -*-

'''
 从配置文件conf中读取各个测试工具的配置参数
'''

import os, sys
import configparser
from lpt.lib import lptenv
import imp

LPTPATH = os.getenv('LPTROOT')
#LPTPATH = lptenv.get_lpt_root()
LPTCONF_DIR = os.path.join(LPTPATH, 'config')
PARAMETER_CONF = os.path.join(LPTPATH, 'parameters/default.conf')
LPT_CONF = os.path.join(LPTCONF_DIR, 'lpt.conf')

  
class BaseConfig(object):
    '''
    读取每个工具的参数配置，并返回一个字典
    '''
    def __init__(self, config_file):
        imp.reload(sys)  
        #sys.setdefaultencoding('utf-8') 
        self.config_file = config_file
        
        #检查parameter.conf是否存在，如果不存在将退出测试
        if not os.path.isfile(self.config_file):
            raise NameError("缺少 %s 配置文件"  % self.config_file)
        
        self.cf=configparser.ConfigParser()
        self.cf.read(self.config_file)
        
    
    def get_sections(self):
        '''
        获取所有sections,返回列表
        '''
        return self.cf.sections()
    
    def get_options(self, section):
        '''
        获取section包含的options,返回列表
        '''
        return self.cf.options(section)
    
    def get_str_value(self, section, option):
        '''
        获取options的value值，返回string
        '''
        return self.cf.get(section, option)
    
    def get_int_value(self, section, option):
        '''
        获取options的value值，返int
        '''
        return self.cf.getint(section, option)
    
    def get_float_value(self, section, option):
        '''
        获取options的value值，返float
        '''
        return self.cf.getfloat(section, option)
    
    def get_boolean_value(self, section, option):
        '''
        获取options的value值，返回boolean
        '''
        return self.cf.getboolean(section, option)
    


def get_config_sections(config=PARAMETER_CONF):
    
    return BaseConfig(config).get_sections()
        
def para_conf(config=PARAMETER_CONF):  
    '''
    获取测试工具几配置
    '''  
    return BaseConfig(config)

def lpt_conf(config=LPT_CONF):
    '''
    获取关于LPT的配置
    '''
    return BaseConfig(config)    

def get_conf_instance(config):
    
    return BaseConfig(config)
