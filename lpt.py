#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
    lpt环境设置、任务创建、任务执行、创建report
'''

import os
import sys
#from lib import lptenv

#设定系统环境
lptdir =  os.path.dirname(os.path.realpath(sys.modules[__name__].__file__))

if not os.getenv('LPTROOT'):
    os.environ['LPTROOT'] = lptdir
try:
    from lpt.lib import lptenv
    lptenv.setup(lptdir)
except ImportError:
    cwd = os.getcwd()
    os.chdir(lptdir)
    from lib import lptenv
    lptenv.setup(lptdir)
    os.chdir(cwd)
    
from lpt.lib.error import *
from optparse import OptionParser
from optparse import OptionGroup
import optparse

from lpt.lib import lptlog
from lpt.lib.error import *
from lpt.lib.share import utils
from lpt.scripts import jobs
from lpt.scripts import run as Jobrun
from lpt.scripts import report as Testreport
from lpt.lib import lptxml
from lpt.scripts import compare
from lpt.lib import readconfig

LPTROOT = os.getenv('LPTROOT')
DB_DIR = os.path.join(LPTROOT, 'db')
RESULTS_DIR = os.path.join(LPTROOT, 'results')
BIN_DIR = os.path.join(LPTROOT, 'bin')
TMP_DIR = os.path.join(LPTROOT, 'tmp')

for dir in (DB_DIR, RESULTS_DIR, BIN_DIR, TMP_DIR):
    if not os.path.isdir(dir):
        os.makedirs(dir, mode=644)
     
JOBS_XML = os.path.join(DB_DIR, 'jobs.xml')
VERSION_FILE = os.path.join(LPTROOT, 'Version')
defaultParameter = os.path.join(LPTROOT, "parameters/default.conf")


START_MSG = '''
   ################################################################
  #               --Linux Performance Testing--                    #
  #                                                                #
  # @author:     Scemoon                                           #
  # @contact:    mengsan8325150@gmail.com                          #
  # @version:    %s                                          #
  #                                                                #
   ################################################################
    ''' % utils.get_version(VERSION_FILE)

STOP_MSG = '''
   ################################################################
  #                                                                #           
  #              !!!     ALL  TESTS OVER     !!!                   #
  #                                                                #
   ################################################################
    '''



def get_list_from_string(option, opt, value, parser):
    '''返回list
    '''
    #print parser.values
    return parser.values.g.split(",")

class Lpt:
    '''
  Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Print log message.
  -q, --quite           No print log message
  -L LEVEL, --LEVEL=LEVEL
                        Log Level:debug,info,warning,error,critical
  -t TOOL, --tool=TOOL  Test Tool
  -g TOOLS, --group=TOOLS
                        Test Tools, example：unixbench,stream

  Job:
    --create            create job use tools of you give by -t or by -g
                        option,default use all tools in parameter.conf.
    -n JobName, --name=JobName
                        set job name
    -f JobsDB, --file=JobsDB
                        jobs databases file of xml
    -i JobID, --id=JobID
                        job id for run or report
    -l, --list          list all jobs

  Run:
    --run               Run job by use job id, default last .You can use tool
                        of you give by -t option, default run all tools that
                        not execute in job tasks
    --clean             clean all temporary file after testing

  Report:
    -F FORMAT           set report format:txt、execl、doc or pdf
    -r NAME             set report name
    -d DIR              set report dir
    --report            create report，with result databases file of xml
    -R XML              get result databases of xml
    --compare           performance compare
    -X resultsXml, --XML=resultsXml
                        Result databases of xmls, separate tags with commas
    -N names, --Names=names
                        point Test Objects, separate tags with commas
    '''
    def __init__(self):
        self.tools_list = []
        self.jobs_xml = None
        self.jobName = "lpt_%s" % utils.gen_random_strs()
        
    
    def set_jobName(self, name):
        pass
   
    def parser(self, argv=sys.argv):
        usage = "usage: %prog [options]" 
        parser = OptionParser(usage=usage, version="%prog 3.0.0")
       
       
        parser.add_option('-v', '--verbose',  
                         action='store_false', 
                         dest='verbose',  
                         default=False,
                         help='Print log message.')
        parser.add_option('-q', '--quite',  
                         action='store_true', 
                         dest='verbose',  
                         help='No print log message')
        parser.add_option('-L', '--LEVEL',  action='store', 
                         metavar="LEVEL",
                         dest='loglevel',  
                         choices=("info", "debug", 'warning', "error", "critical"),
                         help='Log Level:debug,info,warning,error,critical')
        parser.add_option('-t', '--tool', 
                         action='append',
                         dest="tools_list",
                         metavar="TOOL",
                         help="Test Tool")
        parser.add_option('-g', '--group', 
                         action='store', 
                         dest="tools_group", 
                         metavar="TOOLS",
                         help="Test Tools, example：unixbench,stream")
   
        job_group = OptionGroup(parser, "Job")
        job_group.add_option('--create', 
                            action='store_const',
                            const=0, 
                            dest='mode',
                            help="create job use tools of you give by -t or by -g option,default use all tools in parameter.conf.")
        job_group.add_option('-n', '--name', 
                            action='store',
                            dest='JobName', 
                            metavar="JobName",
                            help="set job name")
        job_group.add_option('-p', '--parameter',
			    action='store',
			    dest='parameter',
			    metavar="conf",
			    help="parameter config file")
        job_group.add_option('-f', '--file', 
                            action='store', 
                            dest='jobs_xml',
                            metavar="JobsDB", 
                            default=JOBS_XML,
                            help='jobs databases file of xml')
        job_group.add_option('-i', '--id', 
                            action="store",
                            dest='job_id', 
                            metavar="JobID",
                            help="job id for run or report")
        job_group.add_option('-l', '--list', 
                            action='store_true',
                            dest='jobs_list', 
                            help='list all jobs')
        parser.add_option_group(job_group)
       
        run_group = OptionGroup(parser, "Run")
        run_group.add_option('--run', 
                            action="store_const",
                            const=1, 
                            dest='mode',
                            help="Run job by use job id, default last .You can use tool of you give by -t option, default run all tools that not execute in job tasks")
        run_group.add_option('--clean',  
                         action='store_true', 
                         dest='clean',  
                         default=False,
                         help='clean all temporary file after testing')
        parser.add_option_group(run_group)
       
        report_group = OptionGroup(parser, "Report")
        report_group.add_option('-F',
                               action="store", 
                               dest="format", 
                               choices=('txt', 'xls', 'doc', 'pdf'), 
                               metavar="FORMAT",
                               default='xls', 
                               help="set report format:txt、execl、doc or pdf")
       
        report_group.add_option('-r', 
                               action="store", 
                               dest="reportname", 
                               metavar="NAME" , 
                               help="set report name")
        report_group.add_option('-d',
                               action="store", 
                               dest="reportdir", 
                               metavar="DIR" , 
                               default= RESULTS_DIR,
                               help="set report dir")
        report_group.add_option('--report', 
                               action='store_const', 
                               const=2, 
                               dest="mode",
                               help="create report，with result databases file of xml")
        report_group.add_option('-R',  
                               action='store', 
                               dest="resultdb", 
                               metavar="XML",
                               help="get result databases of xml")
        
        report_group.add_option('--compare', 
                            action="store_const",
                            const=3, 
                            dest="mode",
                            help="performance compare")
        report_group.add_option('-X','--XML', 
                            action="store", 
                            dest="compareFiles", 
                            metavar="resultsXml",
                            help="Result databases of xmls, separate tags with commas")
        report_group.add_option('-N', '--Names', 
                            action="store", 
                            dest="compareNames", 
                            metavar="names",
                            help="point Test Objects, separate tags with commas")
        parser.add_option_group(report_group)
       
        opts, args = parser.parse_args(argv)
       
        return opts
       
    
    def check_root(self):
        if os.getuid() <>0:
            lptlog.warning("请使用root用户执行测试用例")
            sys.exit()
            #raise UnRootError("请使用root用户执行测试用例")
                
    def list_jobs(self, jobs_xml):
        print "%12s%18s%30s%30s" %("JOBID", "JOBNAME", "resultsDB", "TOOLS")
        jobs_nodes = lptxml.search_job_nodes('job', xml_file=jobs_xml)
        if jobs_nodes:
            for job_node in jobs_nodes:
                resultsdb = lptxml.get_job_text("resultsDB", xml_file=jobs_xml, job_node=job_node)
                tool_list = map(lambda x:x.get('id'), lptxml.get_tools_nodes(job_node))
                if len(tool_list) < 3:
                    tool_name = ','.join(tool_list)
                    print "%12s%18s%30s%30s" %(job_node.get('id'), job_node.get('name'), resultsdb, tool_name) 
                else:
                    print "%12s%18s%30s%30s" %(job_node.get('id'), job_node.get('name'), resultsdb,  ','.join(tool_list[0:3])) 
                    n = 3
                    while True:
                        if len(tool_list[n:]) > 3:
                            print "%90s" % ','.join(tool_list[n:n+3])
                            n = n + 3
                            continue
                        else:
                            print "%90s" % ','.join(tool_list[n:])
                            break
            
    def parser_opts(self):
        opts = self.parser()
       #检查是否root用户
#        self.check_root()
       #设定log格式
        if opts.verbose:
           lptlog.update_logger(quiet=opts.verbose)
        #
        if opts.loglevel:
            lptlog.update_logger(level=opts.loglevel)
        
	if opts.parameter:
	    if os.path.isfile(opts.parameter):
	        parameterConfig = opts.parameter
	else:
	    parameterConfig = defaultParameter

        TOOLS_LIST = readconfig.para_conf(config=parameterConfig).get_sections()
       #获取工具列表    
        if opts.tools_list:
            #self.tools_list.extend(filter(lambda x: TOOLS_LIST.count(x)>0, opts.tools_list))
            self.tools_list.extend([ tool.strip() for tool in opts.tools_list if tool in TOOLS_LIST])
        
        if opts.tools_group:
            #self.tools_list.extend(filter(lambda x: TOOLS_LIST.count(x)>0, opts.tools_group.split(',')))
            self.tools_list.extend([ tool.strip() for tool in opts.tools_group.split(',') if tool in TOOLS_LIST])
           
        if self.tools_list:
            
            self.tools_list = {}.fromkeys(self.tools_list).keys()
            #lptlog.info("工具集合: %s" % ",".join(self.tools_list ))
             
        #jobs_xml
        self.jobs_xml = os.path.realpath(opts.jobs_xml)

        try:
            #创建job，可以指定jobs_xml,指定测试工具，指定job名称
            if opts.mode == 0:
                if opts.JobName:
                    self.jobName = opts.JobName
                jobs.add_job(self.tools_list, jobs_xml=self.jobs_xml, parameter=parameterConfig, jobs_attrib={'name':'%s' % self.jobName})
               
            #定义执行任务的方法
            elif opts.mode == 1:
                #开始测试
                lptlog.info(START_MSG)
                if not os.path.abspath(self.jobs_xml):
                    #lptlog.warning("缺失jobs文件，请核对jobs文件或者重新创建job")
                    raise optparse.OptionValueError, "缺失jobs文件，请核对jobs文件或者重新创建job"
                    
                else:
                    Jobrun.run(job_id=opts.job_id, tools_list=self.tools_list, 
                               jobs_xml=self.jobs_xml, format='txt', clean=opts.clean)
                   
                    lptlog.info(STOP_MSG)
                
            elif opts.mode == 2:

                if not  opts.resultdb  or not os.path.abspath(opts.resultdb):
                    #lptlog.warning("请指定result databases(xml)")
                    raise optparse.OptionValueError, "请指定result databases(xml)"
                        
                if not os.path.isdir(opts.reportdir):
                    lptlog.warning("%s 不是有效的目录" % opts.reportdir)
                    os.makedirs(opts.reportdir, mode=777)
                
                Testreport.report(os.path.realpath(opts.resultdb), opts.reportdir, tools_list=self.tools_list,
                                   reportname=opts.reportname, format=opts.format)
                
            elif opts.mode == 3:
                if opts.compareFiles:
                    xmls_list = [ os.path.realpath(str(xml)) for xml in opts.compareFiles.split(',') if os.path.abspath(xml)]
                else:
                    xmls_list = []
                    
                if opts.compareNames:
                    names_list = [ str(name).strip() for name in opts.compareNames.split(',')]
                else:
                    names_list = []
               
                compare.compare(xmls_list, resultDir=opts.reportdir ,reportFile=opts.reportname, names=names_list, tools=self.tools_list, reportType=opts.format)
            else:
                if opts.jobs_list:
                    #检查是否存在jobs xml文件
                    if not os.path.isfile(self.jobs_xml):
                        print self.jobs_xml
                        #lptlog.warning("缺失jobs文件，请核对jobs文件或者重新创建job")
                        #raise NameError("")
                        raise ValueError, "缺失jobs文件，请核对jobs文件或者重新创建job"
                    else:
                        self.list_jobs(self.jobs_xml)
                #else:
                 #   lptlog.warning("-h or --help show help message...")
        except KeyboardInterrupt:
            lptlog.warning("按下CTRL+C,将停止测试程序")
            sys.exit()
        except optparse.OptionValueError, e:
            lptlog.error("Bad option or value")
            lptlog.debug(e)
        except Exception, e:
            lptlog.exception("测试中遇到异常情况，如果需要，请联系作者！！！！\n")
            lptlog.error(e)
def main():
   lpt= Lpt()
   lpt.parser_opts()

if __name__ == '__main__':
    main()
