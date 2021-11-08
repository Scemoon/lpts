#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
    生成测试报告
'''
import os, sys, getopt
import datetime 
try:
    import lpt
except ImportError:
    current_dir = os.path.split(os.path.realpath(sys.modules[__name__].__file__))[0]
    lptroot = os.path.split(current_dir)[0]
    if not os.getenv('LPTROOT'):
        os.environ['LPTROOT'] = lptroot  
    from . import init_env
    init_env.setup(lptroot)
    
from lpt.lib.share import utils
from lpt.lib import lptxml
from lpt.lib import lptlog
from lpt.lib import lptreport
from lpt.lib.error import *

LPTROOT = os.getenv('LPTROOT')
DB_DIR = os.path.join(LPTROOT, 'db')
if not os.path.isdir(DB_DIR):
    os.mkdir(DB_DIR)


TOOLS = ('stream', 'lmbench', 'unixbench', 'dbench_fio', 'pingpong', "unixbench", "x11perf", "glxgears")
TEST = None
RESULT_FILE  = None
RESULT_DB = None


def usage():
    print('''
    Usage: report.py [options] args
    options: -h --help, 帮助信息
             -t --test, 指定测试工具
             -f --file, 指定result database (xml)
             -r --report, 指定需要保存的报告文件,
        ''')
    sys.exit()


  
def getopts(argv=sys.argv):
    
    global TEST 
    global RESULT_DB
    global RESULT_FILE 

    try:
        opts, args = getopt.getopt(argv[1:],"ht:f:r:",["help",'test', 'file', 'report'])
    except getopt.GetoptError:
        usage()

    if len(argv) <= 1:
        usage()

    for opt,value in opts:
        if opt in ('-h','--help'):
            usage()
        
        if opt in ('-t', '--test'):
            if value not in TOOLS:
                lptlog.error('请核对测试工具，不支持您所输入的测试工具 %s' % value)
                sys.exit()
            else:
                TEST = value
   
        if opt in ('-f', '--file'):
            if os.path.isfile(value):
                RESULT_DB = value
    
     
        if opt in ('-r', '--report'):
            RESULT_FILE = value
      

def report(result_xml, resultDir, tools_list=None, 
            reportname=None, format='xls', chart=False):
    '''report 方法'''
    lptlog.info('''
                        ~~~~~~~~~~~~~~~~~~~~
                          开始创建测试报告
                        ~~~~~~~~~~~~~~~~~~~~''')
    if  reportname is None:
        reportname = "LPTResult_%s.%s" %(datetime.datetime.now().strftime('%y-%m-%d_%H:%M:%S'), format)
    elif reportname.split(".")[-1] in ('txt', 'xls', 'doc', 'pdf'):
        reportname = reportname
    else:
        reportname = "%s.%s" %(reportname, format)
        
    report_file = os.path.join(resultDir, reportname)
    
    if not tools_list:
        tools_list = lptxml.get_result_tools(result_xml)
        if tools_list is None :
            lptlog.warning("%s 中无测试数据" % result_xml)
            raise ValueError("result.xml: %s" % result_xml)
        
    lptlog.info("测试报告工具集:  %s" % utils.list_to_str(tools_list))
    lptlog.info("测试报告格式: %s" % format)
    lptlog.info("测试报告名称:  %s" % reportname)
        
    #lptreport.report(result_xml, tools_list, report_file, format)
    if format == "xls":
        lptreport.xls_report(result_xml, tools_list, report_file, chart=chart)
    elif format == "txt":
        lptreport.txt_report(result_xml, tools_list, report_file)
    else:
        pass    
        
    if format=='txt':
        lptlog.info("Report File: %s*.txt" % report_file.split(".txt")[0])
    else:
         lptlog.info("Report File: %s" % report_file)
        
    lptlog.info('''
                        ~~~~~~~~~~~~~~~~~~~~
                          创建测试报告结束
                        ~~~~~~~~~~~~~~~~~~~~''')
    
def main():
    global TEST 
    global RESULT_DB
    global RESULT_FILE 
        
    getopts()
    if TEST is None:
        lptlog.critical("请指定测试工具")
        usage()
        
        
    if RESULT_DB is None:
        lptlog.critical("请指定result Databases")
        usage()
        
    if RESULT_FILE is None:
        lptlog.critical("请指定report Name")
        usage()

    lptlog.info('\n指定工具：%s\n报告文件：%s' % (TEST, RESULT_FILE))
    lptreport.save_result(TEST, RESULT_FILE, RESULT_DB)
    

if __name__ == "__main__":
    try:
        main()
    except Exception:
        #lptlog.exception('生成测试报告：FAIL')
        lptlog.error('生成测试报告：FAIL')
