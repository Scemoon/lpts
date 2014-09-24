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
lptdir = os.path.join(autodir, "lpt")
os.environ['LPTROOT'] = lptdir
from autotest.client import setup_modules
setup_modules.setup(base_path=lptdir, root_module_name="lpt")

import lpt.api.test as lpt_test
from lpt.lib import lptlog
from lpt.lib.share import utils as lutils
from lpt.api import method


class pingpong(test.test, lpt_test.BaseTest):
    version = 1

    def __init__(self, job, bindir, outputdir):
        tool = str(self.__class__.__name__)
        lpt_test.BaseTest.__init__(self, tool)
        test.test.__init__(self, job, bindir, outputdir)


    def initialize(self):
        self.job.require_gcc()
        self.err = []

    def setup(self, tarball='pingpong-0.1.tar.bz2'):
        """
        Compiles pingpong.
        """
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        utils.make()

    def run_once(self):

        tool_node = self.check_tool_result_node()
        lptlog.info("----------开始获取测试参数")

        self.games = self.get_config_array(tool_node, "games", [64,128,256])
        lptlog.info("测试games组： %s" % lutils.list_to_str(self.games))
        self.times = self.get_config_value(tool_node, "times", 18, valueType=int)
        lptlog.info("测试次数: %s" % self.times)

        cmd = "./pingpong.sh"

           #执行测试程序
	os.chdir(self.srcdir)
        lptlog.info("----------运行测试脚本")
        for game in self.games:
            lptlog.info("执行 %s games" % game)
            args = ['-c', "%d" % self.times, '-t', "%d" % game, '-d', self.resultsdir]
            result_tmp_file = os.path.join(self.resultsdir, "%d.pingpong" % game)
	    command = cmd + " " + " ".join(args)
	    utils.system(command)
            #self.results_path = os.path.join(self.resultsdir, 'stream_%d_%d.out' % (parallel, iter+1))
            #utils.open_write_close(result_tmp_file, self.report_data)

            #lutils.run_shell2(cmd, args_list=args, file=result_tmp_file)
            lptlog.info("%d games测试数据保存到: %s" % (game, result_tmp_file))

        self.create_result()
	 #save to result.xml
        self.save_results_to_xml()
        #create txt report
        self.txt_report()

    def create_result(self):
        '''创建result_list
        '''
        for game in self.games:

            result_tmp_file = os.path.join(self.resultsdir, "%s.pingpong" % game)
                #获取 game 平均值
            game_result_list = self.__match_index(game, result_tmp_file)
            self.result_list.append(game_result_list)


    def __match_index(self, game, file):
        '''搜索index
        @return: 返回指定game的result_list,平均值, 
        '''
        labels = ('initialised', 'completed', 'total')
        result_list = []
        result_dict = {}
        if not os.path.isfile(file):
            lptlog.debug("%s 不存在")
            return result_list

        r_init_time = re.compile(r'(?P<thread>\d+) threads initialised in (?P<initialised>\d+) usec')
        r_complete_time = re.compile(r"(?P<games>\d+) games completed in (?P<completed>\d+) usec")

        results_lines = lutils.read_all_lines(file)
        init_time_list = []
        complete_time_list = []
        #获取初始化时间和完成时间，返回两个list
        for line in results_lines:
            if r_init_time.match(line):
                init_time = r_init_time.match(line).group("initialised")
                init_time_list.append(init_time)
            if r_complete_time.match(line):
                complete_time = r_complete_time.match(line).group("completed")
                complete_time_list.append(complete_time)
        #初始化时间求平均值
        init_time_average = lutils.average_list(lutils.string_to_float(init_time_list), bits=0)
        #完成时间求平均值
        complete_time_average = lutils.average_list(lutils.string_to_float(complete_time_list), bits=0)
        sum_time = init_time_average + complete_time_average
        #定义result字典
        for l,v in zip(labels, (init_time_average,  complete_time_average, sum_time)):
            result_dict[l] = "%d" % v
       #定义result属性
        result_node_attrib = self.create_result_node_attrib("Average", self.times, game*2, [i*2 for i in self.games])

        result_list.append(result_dict)
        result_list.insert(0, result_node_attrib)

        return result_list

    def after_run_once(self):

        #os.system("ln -s %s %s/db" % (self.lptdbdir, self.resultsdir))
        #os.system("ln -s %s/%s %s/report"  % (self.lptresultsdir, self.tool, self.resultsdir))
        os.system("cp -r %s %s/db" % (self.lptdbdir, self.resultsdir))
        os.system("cp  -r %s/%s %s/report"  % (self.lptresultsdir, self.tool, self.resultsdir))

