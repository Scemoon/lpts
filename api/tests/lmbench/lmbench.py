# -*- coding:utf-8 -*-
import os,sys
import re
import shutil
from autotest.client import test, utils
from autotest.client.shared import error


# lpt env set
from autotest.client.shared.settings import settings
try:
    autodir = os.path.abspath(os.environ['AUTODIR'])
except KeyError:
    autodir = settings.get_value('COMMON', 'autotest_top_path')


autodir = os.path.abspath(os.environ['AUTODIR'])

#lptdir = os.path.join(os.path.dirname(autodir), "lpt")
lptdir = os.path.join(autodir, "lpts")
os.environ['LPTROOT'] = lptdir
from autotest.client import setup_modules
setup_modules.setup(base_path=lptdir, root_module_name="lpt")

import lpt.api.test as lpt_test
from lpt.lib import lptlog
from lpt.lib.share import utils as lutils
from lpt.lib import lmbench as lm_method

class lmbench(test.test, lpt_test.BaseTest):
    """run lmbench"""
    version = 1

    def __init__(self, job, bindir, outputdir):
        tool = str(self.__class__.__name__)
        lpt_test.BaseTest.__init__(self, tool)
        test.test.__init__(self, job, bindir, outputdir)
        self.times = None
        self.parallels = None

    def initialize(self):
        self.job.require_gcc()
        self.err = []
        
    def setup(self, tarball='lmbench-3.0-a9-1.tar.bz2'):
        '''编译源码，设置程序
        '''
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        self.compile(make_status=True)
        os.chdir(self.lptdir)
            
    def run_once(self):
        
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
        os.chdir(self.srcdir)
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
        utils.system("./genResults.sh %s" % os.path.join(self.resultsdir, "lmbench.out"))
               #数据处理
        self.create_result()
        self.save_results_to_xml()
        #create txt report
        self.txt_report()
    
            
    def create_result(self):
        #os.chdir(self.tar_src_dir)
        #utils.system("./genResults.sh %s" % os.path.join(self.tmp_dir, "lmbench.out"))
        results_file = os.path.join(self.resultsdir, "lmbench.out")
        lm = lm_method.LmbenchData(results_file, self.times, self.parallels)
        lm_attrib= lm.get_basic()
        self.result_list = lm.get_data(attrib=lm_attrib)
        #print self.result_list
    
    def after_run_once(self):
        os.system("cp -r %s %s/db" % (self.lptdbdir, self.resultsdir))
        os.system("cp  -r %s/%s %s/report"  % (self.lptresultsdir, self.tool, self.resultsdir))
        