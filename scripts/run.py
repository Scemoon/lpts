#!/usr/bin/env python
# - *- coding:utf-8 -*-

import os, sys  
import importlib  
try:
    import lpt
except ImportError:
    current_dir = os.path.split(os.path.realpath(sys.modules[__name__].__file__))[0]
    lptroot = os.path.split(current_dir)[0]
    if not os.getenv('LPTROOT'):
        os.environ['LPTROOT'] = lptroot  
    import init_env
    init_env.setup(lptroot)
    
from lpt.lib import lptxml
from lpt.lib.error import *
from lpt.lib import lptlog
from lpt.tests import control


LPTROOT = os.getenv('LPTROOT')
DB_DIR = os.path.join(LPTROOT, 'db')
if not os.path.isdir(DB_DIR):
    os.mkdir(DB_DIR)
    
JOBS_XML = os.path.join(DB_DIR, 'jobs.xml')

__START_MSG = '''
   ################################################################
  #            --Linux Performance Testing Suite--                 #
  #                                                                #
  # @author:     Scemoon                                           #
  # @contact:    mengsan8325150@gmail.com                          #
  # @version:    LPT3.0                                             #                                                               
  #                                                                #
   ################################################################
    '''

__STOP_MSG = '''
   ################################################################
  #                                                                #           
  #              !!!     ALL  TESTS OVER     !!!                   #
  #                                                                #
   ################################################################
    '''
    
__BEGIN_MSG = '''
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                     %s Begin Testing                       
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~''' 

__END_MSG = '''
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                     %s Testing End                      
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~''' 


def run(job_id=None, tools_list=None, jobs_xml=JOBS_XML, format='txt', clean=False, REBOOT=False):
    jobs = lptxml.Jobs(jobs_xml)
    if job_id is None:
        try:
            job_node = jobs.get_new_job()
        except IndexError,e:
            lptlog.debug("job任务数为0， 期望非0")
            job_node = None
    else:
        
         #python 2.7
        #job_node = jobs.search_job_node("job[@id='%s']" % job_id)
        #python 2.6
        job_nodes = jobs.search_job_nodes("job")
        if job_nodes is None:
            lptlog.debug("job任务数为0， 期望非0")
            job_node = None
        else:
            job_filter_nodes = filter(lambda x: x.get("id")==str(job_id), job_nodes)
            if job_filter_nodes:
                job_node = job_filter_nodes[0]
            else:
                lptlog.debug("%s id不存在，请核对JOB ID" % job_id)
                job_node = None
               
    if job_node is None:
        #lptlog.error()
        raise MissXML, "没有找到对应的job任务， 请核对jobs.xml或者重新创建测试任务"
    
    #判断所有工具是否已经全部执行完毕
    no_exec_tools_nodes_list = jobs.get_noexec_tools_nodes(job_node)
    if not no_exec_tools_nodes_list:
        #lptlog.warning('任务中所有工具状态都已正确执行， 请重新创建测试任务')
        raise TestOK, "任务中所有工具状态都已正确执行， 请重新创建测试任务"
    else:
        no_exec_tools = map(jobs.get_tool_name, no_exec_tools_nodes_list)
        
    if not tools_list:
        lptlog.debug("未指定测试工具，将默认执行job中未执行成功的测试工具")  
        test_tools = map(jobs.get_tool_name, no_exec_tools_nodes_list)
    else: #python 2.7 #tools = filter(lambda x:job_node.find("tool[@id='%s']" % x).get('status') == "no", tools_list) #python 2.6 #no_exec_tools = map(lambda y:y.get('id'), jobs.get_noexec_tools_nodes(job_node)) #tools = filter(lambda x:no_exec_tools.count(x)>0, tools_list)
        test_tools = [ tool for tool in no_exec_tools if tool in tools_list]
        
        if not test_tools:
            #lptlog.warning('指定运行的测试工具已经全部执行完毕, 请重新创建任务')
            raise TestOK, '指定运行的测试工具已经全部执行完毕, 请重新创建任务'
        else:
            tools_string = " ".join(test_tools)
            lptlog.debug("尚未执行完毕的测试工具集:%s" % tools_string)
       
    for tool in test_tools:
        lptlog.info(__BEGIN_MSG % tool)
        try:
            control.run(tool, jobs_xml, job_node, clean=clean)
        except Exception, e:
            lptlog.debug(e)
            lptlog.error('''
                    ----------------------------------
                    +       %s 测试:FAIL    +
                    ----------------------------------
                    ''' % tool) 
            lptlog.info(__END_MSG % tool)
            #lptlog.exception("")
            if test_tools[-1] == tool:
                raise TestOK, "Test Over, but Some Case FAIL"
            else:
                continue
        else:
            #python 2.7
            #jobs.set_tool_status(job_node.find("tool[@id='%s']" % tool), 'ok')
            #python 2.6
            tool_node = filter(lambda x:x.get("id")==tool, jobs.get_tools_nodes(job_node))[0]
            jobs.set_tool_status(tool_node, 'ok')
            jobs.save_file()  
            lptlog.info('''
                    ----------------------------------
                    +       %s 测试:PASS    +
                    ----------------------------------
                    ''' % tool)     
            lptlog.info(__END_MSG % tool)
           
            if REBOOT:
                break
    
 


def main():
    #判断是否root用户
    #if os.getuid() <>0:
     #   lptlog.critical('请使用root用户')
      #  sys.exit()
        
    lptlog.info(__START_MSG)
    try:
        if not os.path.isfile(JOBS_XML):
            #lptlog.warning("jobs.xml文件不存在")
            raise NameError, "%s 不存在"  % JOBS_XML
        run()
    except Exception, e:
        lptlog.error('Debug Message: %s' % e)
    finally:
        lptlog.info(__STOP_MSG)
        
if __name__ == '__main__':
    main()




