# -*- coding:utf-8 -*-
'''
    定义测试方法:
    append_sum_dict(sum_dict, result_dict
'''

import os
from lpt.lib import lptlog
from lpt.lib.error import  *
from lpt.lib.share import utils

def append_sum_dict(sum_dict, result_dict):
    '''计算和
    @param result_dict: 测试数据，结构参照run_test函数,result_dict为一组数据
    '''
   
    for key in sum_dict.keys():
        sum_dict[key] = "%f" % (float(sum_dict[key]) + float(result_dict[key]))
                    
    return sum_dict

def append_average_dict(sum_dict, times, format="%.1f"):
    
    average_dict = {}
    for key in sum_dict.keys():
        average_dict[key] = format  % (float(sum_dict[key])/times)
    
    return average_dict
        

def average_dict(sum_dict, times):
    '''求平均值
    '''
    return dict.setdefault(k)
    


def clean_buffer():
    try:
        utils.system('echo "3" > /proc/sys/vm/drop_caches')
    except Exception:
        lptlog.warning("非root用户, 清除缓冲失败...")
        
def check_fileNone(*args):
    '''判断文件是否存在
    @return: NameError
    '''
    for file in args:
        if file is None or not os.path.isfile(file):
            raise NameError, "upexpect file"
        
def check_none(*args):
    for arg in args:
        if arg is None:
            raise NameError, "upexpect None"
        
        
def print_deps_log(func):
    def _print_deps_log(*args, **kwargs):
        lptlog.info("开始环境依赖检查")
        ret = func(*args, **kwargs)
        lptlog.info("结束环境依赖检查")
        return ret
    return _print_deps_log
        
def print_complier_log(func):
    def _print_complier_log(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except Exception:
            lptlog.error('编译:FAIL')
        #    os.chdir(root_dir)
            raise CompileException()
        else:
            lptlog.info('编译:OK')
        return ret
    return _print_complier_log
