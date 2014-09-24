# -*- coding:utf-8 -*-
import os
import re

from autotest.client import utils, test

# lpt env set
from autotest.client.shared.settings import settings
try:
    autodir = os.path.abspath(os.environ['AUTODIR'])
except KeyError:
    autodir = settings.get_value('COMMON', 'autotest_top_path')


autodir = os.path.abspath(os.environ['AUTODIR'])

lptdir = os.path.join(os.path.dirname(autodir), "lpt")
lptdir = os.path.join(autodir, "lpt")
os.environ['LPTROOT'] = lptdir
from autotest.client import setup_modules
setup_modules.setup(base_path=lptdir, root_module_name="lpt")

import lpt.api.test as lpt_test
from lpt.lib import lptlog
from lpt.lib.share import utils as lutils
from lpt.api import method


class dbench_fio(test.test, lpt_test.BaseTest):
    version = 4

    def __init__(self, job, bindir, outputdir):
        tool = str(self.__class__.__name__)
        lpt_test.BaseTest.__init__(self, tool)
        test.test.__init__(self, job, bindir, outputdir)


    # http://samba.org/ftp/tridge/dbench/dbench-3.04.tar.gz
    def setup(self, tarball='dbench-4.0.0.tar.bz2'):
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)

        #utils.system('patch -p1 < %s' %
                    # os.path.join(self.bindir, 'dbench_startup.patch'))
	utils.system("./autogen.sh")
        utils.configure()
        utils.make()

    def initialize(self):
        self.job.require_gcc()
        #self.results = []
	self.check_deps()
	utils.system("ulimit -n 100000", ignore_status=True)

    def run_once(self):

	tool_node = self.check_tool_result_node()

        lptlog.info("----------获取测试参数")

        cmd = os.path.join(self.srcdir, 'dbench')
        args = ['-B', 'fileio',  '-c', os.path.join(self.srcdir, 'loadfiles/client.txt'), '-R', '999999.99']

            #获取测试目录
        testdir = self.get_config_testdir(tool_node)
        args.append("-D")
        args.append(testdir)

            #获取设备,并尝试挂载到testdir
        devices_status = self.get_config_devices(tool_node, testdir)

        self.times = self.get_config_value(tool_node, "times", 5, valueType=int)
        lptlog.info("测试次数: %d " % self.times)


        self.parallel_type = self.get_config_value(tool_node, "parallel_type", "process", valueType=str)
        lptlog.info("测试并行方式: %s" % self.parallel_type)

        self.parallels = self.get_config_array(tool_node, "parallel", [4])
        lptlog.info("测试并行: %s" % lutils.list_to_str(self.parallels))
        if self.parallel_type  not in ("threads", "process"):
            self.parallel_type = "process"
        runtime = self.get_config_value(tool_node, 'runtime', 300, valueType=int)
        lptlog.info("测试时长: %s s" % runtime)
        args.append("-t")
        args.append("%d" % runtime)


        warnuptime = self.get_config_value(tool_node, 'warnuptime', 120, valueType=int)
        if warnuptime > runtime:
            lptlog.warning("warnuptime 大于 runtime, warnuptime = runtime/5")
            warnuptime = runtime/5
        lptlog.info("预热时长: %s s" % warnuptime)
        args.append("--warmup=%d" % warnuptime)


        lptlog.info("----------运行测试脚本")
        for parallel in self.parallels:
            lptlog.info("运行 %s 并行" % parallel)
            parallel_args = []

            if self.parallel_type == "threads":
                parallel_args.append("--clients-per-process=%d" % parallel)
                parallel_args.append("1")
            else:
 		parallel_args.append(str(parallel))

            for iter in range(self.times):
                lptlog.info("第 %s 次测试" % (iter+1))
                tmp_file = os.path.join(self.resultsdir, "%s_%s_%s.out" % (self.tool, parallel, iter+1))

                    #清除buffer
                method.clean_buffer()
                lutils.run_shell2(cmd, args_list=args+parallel_args, file=tmp_file)
                lptlog.info("%d 并行  %d 次测试，测试数据保存在: %s " % (parallel, iter+1, tmp_file))
        #create result list
        self.create_result()
        #save to result.xml
        self.save_results_to_xml()
        #create txt report
        self.txt_report()

    def create_result(self):
        '''创建result_list
           '''

        #labels = ("Throughtput", "clients", "max_latency")
        labels = ("Throughtput",  "max_latency")
        parallelstring = ",".join(map(str, self.parallels))

        r = re.compile(r"Throughput\s+(\d+.\d+)\s+MB/sec\s+(\d+)\s+clients\s+\d+\s+procs\s+max_latency=(\d+.\d+)\s", re.I)
        for parallel in self.parallels:
            sum_dic = {}
            for iter in range(self.times):
                tmp_result_file = os.path.join(self.resultsdir, "%s_%s_%s.out" % (self.tool, parallel, iter+1))
                if not os.path.isfile(tmp_result_file):
                    lptlog.warning("%s 不存在" % tmp_result_file)
                    continue
                result_lines = lutils.read_all_lines(tmp_result_file)
                for line in result_lines:
                    key_dic = {}
                    if r.match(line):
                        m = r.match(line)
                        #result_list = [m.group(1), m.group(2), m.group(3)]
                        result_list = [m.group(1), m.group(3)]
                        result_tuple = tuple([lutils.change_type(i)for i in result_list])
                        for l, v in zip(labels, result_tuple):
                            key_dic[l] = "%d" % v
                        if not sum_dic:
                            sum_dic = key_dic.copy()
                        else:
                            sum_dic = method.append_sum_dict(sum_dic, key_dic)
                        self.result_list.append([self.create_result_node_attrib(iter+1, self.times, parallel, self.parallels), key_dic])

            if  sum_dic:
                parallel_average_dic = method.append_average_dict(sum_dic, self.times)
                lptlog.debug("%d 并行求平均值:PASS" % parallel)
                self.result_list.append([self.create_result_node_attrib("Average", self.times, parallel, self.parallels), parallel_average_dic])



    #def postprocess_iteration(self):
     #   pattern = re.compile(r"Throughput (.*?) MB/sec (.*?) procs")
      #  (throughput, procs) = pattern.findall(self.results)[0]
       # self.write_perf_keyval({'throughput': throughput, 'procs': procs})

    def after_run_once(self):

        #os.system("ln -s %s %s/db" % (self.lptdbdir, self.resultsdir))
        #os.system("ln -s %s/%s %s/report"  % (self.lptresultsdir, self.tool, self.resultsdir))
        os.system("cp -r %s %s/db" % (self.lptdbdir, self.resultsdir))
        os.system("cp  -r %s/%s %s/report"  % (self.lptresultsdir, self.tool, self.resultsdir))

