#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os, sys, getopt
import datetime
try:
    import lpt
except ImportError:
    current_dir = os.path.split(os.path.realpath(sys.modules[__name__].__file__))[0]
    lptroot = os.path.split(current_dir)[0]
    if not os.getenv('LPTROOT'):
        os.environ['LPTROOT'] = lptroot  
    import init_env
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

def usage():
    print '''
    Usage: compare.py [options] args
    options: -h --help, 帮助信息
             -t --test, 指定测试工具
             -f --file, 指定result database (xml)
             -n --name, 自定义输出名称
             -r --report, 指定需要保存的报告文件
        '''
    sys.exit()


  
def getopts(argv=sys.argv):
    
    tests_list = []
    xmls_list = []
    names_list = []
    report_file = None
    try:
        opts, args = getopt.getopt(argv[1:],"ht:f:r:n:",["help",'test', 'file', 'report', 'name'])
    except getopt.GetoptError:
        usage()

    if len(argv) <= 1:
        usage()

    for opt,value in opts:
        if opt in ('-h','--help'):
            usage()
        
        if opt in ('-t', '--test'):
            if value not in TOOLS:
                lptlog.warning('请核对测试工具，不支持您所输入的测试工具 %s' % value)
            else:
                tests_list.append(value)
   
        if opt in ('-f', '--file'):
            if os.path.isfile(value):
                xmls_list.append(value)
                
        if opt in ('-n', '--name'):
            names_list.append(value)
    
        if opt in ('-r', '--report'):
            report_file = value


    if len(xmls_list) < 2:
        lptlog.warning("期望result.xml > 2")
        sys.exit()
    else:
        compare(xmls_list, names=names_list, reportFile=report_file, tools=tests_list)
    
def compare(xmls_list, resultDir=os.getcwd() ,reportFile=None, names=[], tools=[], reportType="xls"):
    '''对比多个result xml文件， 如果指定tools，那么只对比tools,但tools必须包含在所有xmls文件中
    @param xmls: results xml ,type list
    @param names: 自定义对比名称，用于输出显示，type list, default []
    @param tools: 指定对比测试工具，type list, default [] '''
    
    lptlog.info('''
                        ~~~~~~~~~~~~~~~~~~~~
                          开始创建对比测试报告
                        ~~~~~~~~~~~~~~~~~~~~''')
    
    #检查resultDir
    if resultDir is None:
        resultDir = os.getcwd()
        
    if not  os.path.isdir(resultDir):
        os.makedirs(resultDir, mode=644)
        
    if  reportFile is None:
        reportFile = "LPTCmpResult_%s.%s" %(datetime.datetime.now().strftime('%y-%m-%d_%H:%M:%S'), reportType)
    elif reportFile.split(".")[-1] in ('txt', 'xls', 'doc', 'pdf'):
        reportFile = reportFile
    else:
        reportFile = "%s.%s" %(reportFile, reportType)
        
    report_abs_file = os.path.join(resultDir, reportFile)
    
    lptlog.info("@@@@@@@--指定对比工具: %s" % utils.list_to_str(tools))
    lptlog.info("@@@@@@@--对比对象分别为: %s " % utils.list_to_str(names))
    lptlog.info("@@@@@@@--对比测试报告类型: %s" % reportType)
    lptlog.info("@@@@@@@--对比测试报告: %s" % report_abs_file)
    if reportType == "xls":
        cmpobject = lptreport.XlsCompare(xmls_list, report_abs_file, input_tools=tools, input_name_list=names )
        cmpobject.cmp_tools()
        cmpobject.save()
    else:
        lptlog.warning(" %s 对比测试报告正在开发中..."  % reportType)
        
    lptlog.info('''
                        ~~~~~~~~~~~~~~~~~~~~
                          创建对比测试报告结束
                        ~~~~~~~~~~~~~~~~~~~~''')

if __name__ == "__main__":
    getopts()
    