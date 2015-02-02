# -*- coding:utf-8 -*-
'''
  定义log
更新log格式：update_logger
'''

import logging
import logging.handlers 
import os
import sys

from lpt.lib import readconfig


#__all__ = ['log' , 'update_logger']


#定义日志文件path
LOG_DIR = os.path.join(os.getenv('LPTROOT'),'logs')

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)
    
LOGFILE = os.path.join(LOG_DIR,'Test.log')

# 定义颜色
COLOR_RED='\033[1;31m'
COLOR_GREEN='\033[1;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[1;34m'
COLOR_PURPLE='\033[1;35m'
COLOR_CYAN='\033[1;36m'
COLOR_GRAY='\033[1;37m'
COLOR_WHITE='\033[1;38m'
COLOR_RESET='\033[1;0m'

#定义Log不同level对应的颜色
LOG_COLORS = {
        'DEBUG': '%s',
        'INFO': COLOR_GREEN + '%s' + COLOR_RESET,
        'WARNING': COLOR_YELLOW + '%s' + COLOR_RESET,
        'ERROR': COLOR_RED + '%s' + COLOR_RESET,
        'CRITICAL': COLOR_RED + '%s' + COLOR_RESET,
        'EXCEPTION': COLOR_RED + '%s' + COLOR_RESET,
}

#定义log输出格式
FORMATTER =  {
        'detail': '%(asctime)s %(name)s %(levelname)s %(filename)s %(module)s %(funcName)s  [%(pathname)s:%(lineno)d] %(message)s' ,
        'verbose':'%(asctime)s %(name)s %(levelname)s [%(pathname)s:%(lineno)d] %(message)s',
        'simple': '%(asctime)s %(name)s %(levelname)s  %(message)s',
}

FILE_HANDLER = {
                'filename': LOGFILE,
                'maxBytes': 1024*1024*20,  
                'backupCount': 5,
             }

# 
LOG_LEVEL = {0:'NOTSET', 10:'DEBUG', 20:'INFO', 30:'WARNING', 40:'ERROR', 50:'CRITICAL', 60:'EXCEPTION'}
   
#定义Log 彩色格式方法类
class ColoredFormatter(logging.Formatter):

        '''A colorful formatter.'''

        def __init__(self, fmt = None, datefmt = None):
            logging.Formatter.__init__(self, fmt, datefmt)

        def format(self, record):
            level_name = record.levelname
            msg = logging.Formatter.format(self, record)

            return LOG_COLORS.get(level_name, '%s') % msg


class LogRecord:

    '''
   定义Log属性、格式
   1.设置终端显示LEVEL,debug OR info OR error OR critical
    LogRecord.set_stdout_level(LEVEL) 
    
   2.设置终端输出日志输出格式fmt, simple OR verbose OR details
                    'detail' = '%(name)s %(levelname)s  %(asctime)s %(module)s %(process)d %(thread)d [%(pathname)s:%(lineno)d] %(message)s' ,
                    'verbose' = '%(name)s %(levelname)s %(asctime)s [%(pathname)s:%(lineno)d] %(message)s',
                    'simple' = '%(name)s %(levelname)s %(asctime)s %(message)s',
    LogRecord.set_stdout_formatter(fmt)
    
   3.设置终端日志输出格式的name
    LogRecord.set_logname(name)
    '''
     
    
    logname = 'lpts'
    fmt = 'simple'
    level = logging.INFO
    file_level = logging.DEBUG
    file_handler_dic = FILE_HANDLER
    quiet = False
      
    def __init__(self):
        self.logger = None
                
    @classmethod        
    def set_output_status(cls ,status):
        cls.quiet = status
        
    @classmethod
    def get_output_status(cls):
        return cls.quiet
        
     #设定level
    @classmethod
    def set_stdout_level(cls, loglevel):
        if isinstance(loglevel, str):
            cls.level = getattr(logging, loglevel.upper(), logging.DEBUG)
         
    @classmethod
    def get_stdout_level(cls):
        return logging.getLevelName(cls.level)
        
    #设定file_level
    @classmethod
    def set_file_level(cls, file_level):
        if isinstance(file_level, str):
            cls.file_level = getattr(logging, file_level.upper(), logging.DEBUG)
            
    @classmethod
    def get_file_level(cls):
        return logging.getLevelName(cls.file_level)
    
     #设定format
    @classmethod
    def set_stdout_formatter(cls,strfmt):
        if strfmt in ( 'detail', 'simple' , 'verbose'):
            cls.fmt = strfmt
        else:
            cls.fmt = 'verbose'
            
    @classmethod
    def get_stdout_formatter(cls):
            return cls.fmt
        
     #定义logname
    @classmethod
    def set_logname(cls,name):
        cls.logname = name
        
    @classmethod
    def get_logname(cls):
        return cls.logname
    
    @classmethod
    def set_filehandler(cls):
        pass
        

    def __add_handler(self, fuc, **kwargs):
        
        handler = fuc(**kwargs)
        formatter = logging.Formatter(FORMATTER['detail'],'%Y-%m-%d %H:%M:%S')
        handler.setLevel(self.file_level)
        handler.setFormatter(formatter)
        return handler


    def __add_streamhandler(self):
    
        ''' 定义 logger的console handler '''
        
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(self.level)
        formatter = ColoredFormatter(FORMATTER[self.fmt],'%Y-%m-%d %H:%M:%S')
        console.setFormatter(formatter)
        return console
    
   
    def __add_filehandler(self):
        
        ''' 定义 logger的File handler '''
    
        kwargs = self.file_handler_dic
    # 设置日志文件存储格式
        return self.__add_handler(logging.handlers.RotatingFileHandler, **kwargs)

    
    def record(self):  
        
        self.logger = logging.getLogger(self.logname)      
        if self.logger is not None:
            logging.shutdown()
            self.logger.handlers = []
            
        if self.quiet:
            output = logging.NOTSET
        else:
            output = logging.DEBUG
        self.logger.setLevel(output)
    
        #注册handler
        stdhandler = self.__add_streamhandler()
        filehandler = self.__add_filehandler()
        self.logger.addHandler(stdhandler)
        self.logger.addHandler(filehandler)
        
        return self.logger
        
    
              
def __import_log_funcs(fuc):
    #if sys.modules.has_key(__name__):
    #	return
    curr_mod = sys.modules[__name__]
    log_funcs = ['debug', 'info', 'warning', 'error', 'critical','exception']
    for func_name in log_funcs:
        func = getattr(fuc, func_name)
        setattr(curr_mod, func_name, func)
        
       
def set_logger():
    ''''
    实例化LogRecord方法
    logger = get_logger()
    '''
    log_record = LogRecord()   
    log = log_record.record()
    __import_log_funcs(log)
    
    
def update_logger(name=LogRecord.get_logname(), fmt=LogRecord.get_stdout_formatter(),
                  level=LogRecord.get_stdout_level(),  file_level=LogRecord.get_file_level(),
                  quiet=LogRecord.get_output_status(),  **kwargs):
    '''
    @param name:用于设定日志输出格式中的name
    @param level: 用于设定终端日志显示级别
    @param file_level:用于设定文件日志显示级别 
    @param fmt: 自定义的日志输出格式 simple,verbose,detail 
    '''
    
    if name is not None:
        LogRecord.set_logname(name)
        LogRecord.set_stdout_level(level)
        LogRecord.set_file_level(file_level)
        LogRecord.set_stdout_formatter(fmt)
        LogRecord.set_output_status(quiet)
    
    #重新实例化
    set_logger()
    
    
def init_logger():  
    logconfig = readconfig.lpt_conf()
    if logconfig.get_boolean_value('log', 'OPEN'):
        formatter = logconfig.get_str_value('log','FORMATTER')
        loglevel = logconfig.get_str_value('log', 'LEVEL')
        file_level = logconfig.get_str_value('log', 'FILE_LEVEL')
        quiet = logconfig.get_boolean_value('log', 'QUIET')
        update_logger(fmt=formatter, level=loglevel, file_level=file_level, quiet=quiet)
    else:
        set_logger()
        
        
init_logger()
    
