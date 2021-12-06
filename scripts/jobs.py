#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
创建job
'''
import os, sys, getopt
try:
    import lpt
except ImportError:
    current_dir = os.path.split(os.path.realpath(sys.modules[__name__].__file__))[0]
    lptroot = os.path.split(current_dir)[0]
    if not os.getenv('LPTROOT'):
        os.environ['LPTROOT'] = lptroot  
    from . import init_env
    init_env.setup(lptroot)
     
from lpt.lib import lptxml
from lpt.lib import lptlog
from lpt.lib.error import *
from lpt.lib.share import utils

LPTROOT = os.getenv('LPTROOT')
DB_DIR = os.path.join(LPTROOT, 'db')
if not os.path.isdir(DB_DIR):
    os.mkdir(DB_DIR)
    
JOBS_XML = os.path.join(DB_DIR, 'jobs.xml')
default_parameter = os.path.join(LPTROOT, "parameters/default.conf")
TOOLS = ('stream', 'unixbench', 'dbench_fio', 'pingpong', 'iozone', 'x11perf', 'glxgears')

#首先创建job
def add_job(tools_list, jobs_xml=JOBS_XML, parameter=default_parameter, job_attrib={}, resultXmlName="results"):
    '''
    创建新任务
    @param tools_list:工具列表
    @type tools_list: list 
    '''
    try:
        lptlog.info('''
                        ~~~~~~~~~~~~~~~~~~~~
                          开始创建测试任务
                        ~~~~~~~~~~~~~~~~~~~~''')
        lptlog.debug("指定测试工具集: %s" % utils.list_to_str(tools_list))
        lptxml.add_job(jobs_xml, tools_list, parameter, job_attrib=job_attrib, resultXmlName=resultXmlName)
        lptlog.info('''
                        ++++++++++++++++++
                         创建测试任务:PASS
                        ++++++++++++++++++''')
    except CreateJobException as e:
        lptlog.debug(e)
        lptlog.error('''
                        ++++++++++++++++++
                         创建测试任务:FAIL
                        ++++++++++++++++++''')
        #lptlog.exception('')
        
    finally:
         lptlog.info('''
                        ~~~~~~~~~~~~~~~~~~~~
                          创建测试任务结束
                        ~~~~~~~~~~~~~~~~~~~~''')
    
def usage():
    print('''
	Usage: jobs.py [options] args
	options: -h --help, 帮助信息
             	 -t --test, 指定测试测试工具
		 -g --group 指定测试工具组,用空格隔开,如"stream lmbench"
        ''')
    sys.exit()
        
def getopts(argv=sys.argv):
    '''
    自定义参数
    '''
    tools_list = []
    
    try:
        opts, args = getopt.getopt(argv[1:],"ht:g:",["help",'test', 'group'])
    except getopt.GetoptError:
        usage()

    if len(argv) <= 1:
        usage()

    for opt,value in opts:
        if opt in ('-h','--help'):
            usage()
        if opt == '-t':
            if value not in TOOLS:
                lptlog.error('请核对测试工具，不支持您所输入的测试工具 %s' % value)
                sys.exit()
            else:
                tools_list.append(value)
                
        if opt in ('-g', '--group'):
             value_list = value.split()
             for tools in  value_list:
                    if tools in TOOLS:
                        tools_list.append(tools)
        else:
                        lptlog.warning('%s不是有效的测试工具，请核对工具名称' % tools)
    
    return tools_list

def main():
    tools_list = getopts()
    
    if not tools_list :
        lptlog.error('没有输入有效的测试工具')
        sys.exit()
    else:
        	lptlog.info('测试工具集:%s' % ', '.join(tools_list))
    
    add_job(tools_list)
    

if __name__ ==  '__main__':
    main()
    
