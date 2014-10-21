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
lptdir = os.path.join(autodir, "lpts")
os.environ['LPTROOT'] = lptdir
from autotest.client import setup_modules
setup_modules.setup(base_path=lptdir, root_module_name="lpt")

import lpt.api.test as lpt_test
from lpt.lib import lptlog
from lpt.lib.share import utils as lutils
from lpt.api import method


class stream(test.test, lpt_test.BaseTest):
    version = 1

    def __init__(self, job, bindir, outputdir):
        tool = str(self.__class__.__name__)
        lpt_test.BaseTest.__init__(self, tool)
        test.test.__init__(self, job, bindir, outputdir)


    def initialize(self):
        self.job.require_gcc()
        self.err = []

    def setup(self, tarball='stream-5.9-1.tar.bz2'):
        """
        Compiles stream.
        """
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)

        utils.make()

    def run_once(self):
        tool_node = self.check_tool_result_node()
        self.mainParameters["parameters"] = "stream_mu"
        lptlog.info("-----------开始获取测试参数")
        testmode = self.get_config_value(tool_node, "testmode", "default", valueType=str)
        lptlog.info("测试模式： %s" % testmode)

        self.parallels = self.get_config_array(tool_node, "parallel", [1])
        lptlog.info("测试并行数组： %s" % ",".join(map(str, self.parallels)))

        self.times = self.get_config_value(tool_node, "times", 5, valueType=int)
        lptlog.info("测试次数: %d" % self.times )
        if testmode == 'custom':
            cmd = "./stream_mu"

        else:
            cmd = "./stream" 
            self.parallels = [1]

        lptlog.info("----------运行测试脚本")
        os.chdir(self.srcdir)
        #执行测试程序
        for parallel in self.parallels:
            if parallel == 1:
                pass
            else:
                os.environ['OMP_NUM_THREADS'] = str(parallel)
            for iter in range(self.times):
                #tmp_result_file = os.path.join(self.lpttmpdir, "stream_%d_%d.out" %(parallel, iter+1))
                #utils.run_shell2(cmd, args_list=[], file=tmp_result_file)
                #self.report_data = utils.system_output(cmd)
                self.results_path = os.path.join(self.resultsdir, "stream_%d_%d.out" %(parallel, iter+1))
                lutils.run_shell2(cmd, args_list=[], file=self.results_path)
                lptlog.info('并行数 %d, 第 %d 测试：PASS' % (parallel, iter+1))
                #utils.open_write_close(self.results_path, self.report_data)	

	#create result list
        self.create_result()
	#save to result.xml
        self.save_results_to_xml()
	#create txt report
        self.txt_report()

    def create_result(self):
        #method.check_none(self.parallels, self.times)
        labels = ("Copy", 'Scale', 'Add', 'Triad')

        for parallel in self.parallels:
            sum_dic = {}
            for iter in range(self.times):
                iter_dic = {}
                #tmp_result_file = os.path.join(self.tmp_dir, "stream_%d_%d.out" %(parallel, iter+1))
                tmp_result_file = os.path.join(self.resultsdir, "stream_%d_%d.out" %(parallel, iter+1))
                if not os.path.isfile(tmp_result_file):
                    lptlog.warning("测试数据 %s 不存在" % tmp_result_file)
                    continue

                result_tuple = self.__search_result(tmp_result_file)
                for key, value in zip(labels, result_tuple):
                    iter_dic[key] = "%.4f" %value
                if sum_dic:
                    sum_dic = method.append_sum_dict(sum_dic, iter_dic)
                else:
                    sum_dic = iter_dic.copy()
                self.result_list.append([self.create_result_node_attrib(iter+1, self.times, parallel, self.parallels), iter_dic])
            if  sum_dic:
                average_dic = method.append_average_dict(sum_dic, self.times)
                self.result_list.append([self.create_result_node_attrib("Average", self.times, parallel, self.parallels), average_dic])

    def __search_result(self, file):
        r= re.compile(r'Copy*',re.I)
        lines = lutils.read_all_lines(file)
        for line in lines:
            if r.match(line):
                copy = line.split()[1]
                index = lines.index(line)
                scale = lines[index+1].split()[1]
                add = lines[index+2].split()[1]
                triad = lines[index+3].split()[1]
                return tuple(map(lutils.change_type, [copy, scale, add, triad]))

        return (0, 0, 0, 0)

    def after_run_once(self):
        os.system("cp -r %s %s/db" % (self.lptdbdir, self.resultsdir))
        os.system("cp  -r %s/%s %s/report"  % (self.lptresultsdir, self.tool, self.resultsdir))

       
