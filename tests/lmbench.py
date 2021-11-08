# -*- coding:utf-8 -*-
'''
  lmbench测试工具执行脚本
'''

import os, shutil,re,time
from .test import BaseTest
from lpt.lib.error import *
from lpt.lib import lptxml
from lpt.lib import lptlog
from lpt.lib.share import utils
from lpt.lib import lptreport
from .share import method
from lpt.lib import lmbench as lm_method

class TestControl(BaseTest):
    '''
    继承BaseTest属性和方法
    '''
    def __init__(self, jobs_xml, job_node, tool, tarball='lmbench-3.0-a9-1.tar.bz2'):
        super(TestControl, self).__init__(jobs_xml, job_node, tool, tarball)
        self.times = None
        self.parallels = None
        
    def setup(self):
        '''编译源码，设置程序
        '''
        if not self.check_bin(self.processBin):
            self.tar_src_dir = self.extract_bar()
            os.chdir(self.tar_src_dir)
            self.compile(make_status=True)
            os.chdir(self.lpt_root)
            
    def run(self):
        
        tool_node = self.check_tool_result_node()
            
        lptlog.info("-----------开始获取测试参数")
        self.parallels =self.get_config_value(tool_node, "parallel", 1, valueType=int)
        if self.parallels >999:
            lptlog.info("限制并行数小于999, 将采用1")
            self.parallels = 1
        lptlog.info("测试并行数： %d" % self.parallels)
        
        self.times = self.get_config_value(tool_node, "times", 5, valueType=int)
        lptlog.info("测试次数: %d" % self.times)
        
        jobs_sched = self.get_config_value(tool_node, "lmbench_sched", "DEFAULT", valueType=str)
        if jobs_sched not in ("DEFAULT", "BALANCED", "BALANCED_SPREAD", "UNIQUE", "NIQUE_SPREAD"):
            jobs_sched="DEFAULT"
        lptlog.info("调度模式为：%s" % jobs_sched)
        
        testMem = self.get_config_value(tool_node, "testmemory", 1000, valueType=int)
        lptlog.info("指定测试内存为: %sM, 但如果测试内存大于系统可用内存，lmbench将自动计算可用内存" % testMem)
        
        output = self.get_config_value(tool_node, "output", "/dev/tty", valueType=str)
        lptlog.info("lmbench 将打印信息到: %s" % output)
        
        self.mainParameters["parameters"] = "Mem:%dM jobSched:%s" %(testMem, jobs_sched)
        
        lptlog.info("----------运行测试脚本")      
            #执行测试程序
        os.chdir(self.tar_src_dir)
        #Now, 配置测试参数
        utils.system("./config.sh -p %d -j %s -m %d -o %s" %(self.parallels, jobs_sched, testMem, output))
        
        #clean 之前的测试数据
        for rootdir, subdirs, files in os.walk("./results"):
            for dir in subdirs:
                subabsdir = os.path.join(rootdir, dir)
                if os.path.exists(subabsdir):
                    shutil.rmtree(os.path.join(rootdir, dir))
        #run
        for iter in range(self.times):
            utils.system("./run.sh")
            time.sleep(60)
        
        #gen results
        utils.system("./genResults.sh %s" % os.path.join(self.tmp_dir, "lmbench.out"))
  
        
    def create_result(self):
        #os.chdir(self.tar_src_dir)
        #utils.system("./genResults.sh %s" % os.path.join(self.tmp_dir, "lmbench.out"))
        results_file = os.path.join(self.tmp_dir, "lmbench.out")
        lm = lm_method.LmbenchData(results_file, self.times, self.parallels)
        lm_attrib= lm.get_basic()
        self.result_list = lm.get_data(attrib=lm_attrib)
        #print self.result_list
        

