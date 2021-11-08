# -*- coding:utf-8 -*-
import os,sys
import re
import shutil
from autotest.client import test, utils
from autotest.client.shared import error
import os, shutil, re, stat, getpass

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
from lpt.lib import sysinfo


class bonnie(test.test, lpt_test.BaseTest):
    version = 1

    def __init__(self, job, bindir, outputdir):
        tool = str(self.__class__.__name__)
        lpt_test.BaseTest.__init__(self, tool)
        test.test.__init__(self, job, bindir, outputdir)
        self.times = None

    def initialize(self):
        self.job.require_gcc()
        self.err = []
	
    def setup(self, tarball='bonnie++-1.03e.tar.bz2'):
        """
        Compiles bonnie.
        """
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)
        utils.configure()
        utils.make()


    def run_once(self):
        tool_node = self.check_tool_result_node()
        lptlog.info("----------开始获取测试参数")

        cmd = os.path.join(self.srcdir, "bonnie++")
        args = ['-u', os.getuid(),  '-m', 'lpt', '-q']

            #获取测试目录
        testdir = self.get_config_value(tool_node, "testdir", os.path.join(self.lpttmpdir, "testdir"), valueType=str)
        if os.path.exists(testdir):
            if not os.path.isdir(testdir):
                lptlog.warning("%s 不是有效目录，将采用 /home/%u/testdir 目录" % testdir)
                testdir = "/home/%s/testdir" % getpass.getuser()
                os.makedirs(testdir, stat.S_IRWXU)
        else:
            os.makedirs(testdir, stat.S_IRWXU)
            testdir = os.path.abspath(testdir)
        args.append("-d")
        args.append(testdir)
        lptlog.info("测试目录: %s" % testdir)

            #获取设备

        devices = self.get_config_value(tool_node, "devices", "Nodevice", valueType=str)
        lptlog.info("测试分区: %s " % devices)
        if not os.path.exists(devices):
            lptlog.debug("%s 不存在" % devices)
        else:
            try:
                if not os.path.ismount(testdir):
                    util.system("mount %s %s" % (devices, testdir))
                else:
                    lptlog.debug("%s 已经挂载到 %s 目录" % (devices, testdir))
            except Exception:
                lptlog.warning("mount %s %s 失败，请确认分区是否已经格式化！！" % (devices, testdir))

            #获取测试内存大小
        memory = self.get_config_value(tool_node, "memory", sysinfo.get_memory_size(), valueType=str)
        if not lutils.check_size_format(memory, match="\d+[kKmMgGtT]?"):
            lptlog.warning("测试内存配置error, 将采用系统内存")
            memory = sysinfo.get_memory_size()
            lptlog.debug("系统内存大小：%s" % memory)
	   #获取测试文件大小
        filesize = self.get_config_value(tool_node, "filesize", "10g", valueType=str)
        if not lutils.check_size_format(filesize, match="\d+[kKmMgGtT]?"):
            lptlog.warning("%s 格式 error,将采用默认大小10g" % filesize)
            filesize = "10g"

        if float(lutils.custom_format(memory)) * 2 > float(lutils.custom_format(filesize)):
            lptlog.warning("测试需求:测试内存*2 小于 文件大小，但实际相反,  将降低测试内存大小为测试文件的1/2" )
            memory = float(lutils.custom_format(filesize))/2
            memory = lutils.custom_format(memory, auto=True)

        lptlog.info("测试内存大小：%s" % memory)
        lptlog.info("测试文件大小： %s" % filesize)
        args.append("-r")
        args.append(memory)

        #获取block大小
        blocksize = self.get_config_value(tool_node, "blocksize", "4k", valueType=str)
        if not lutils.check_size_format(blocksize, match="\d+k?"):
            lptlog.warning("blocksize=%s 格式 error,将采用默认大小8k" % blocksize)
            blocksize = "8k"

        args.append("-s")
        args.append("%s:%s" %(filesize, blocksize))
        lptlog.info("测试块大小： %s" % blocksize)

        small_files_num = self.get_config_value(tool_node, "small_files_num", 0, valueType=int)
        small_file_size = self.get_config_value(tool_node, "small_file_size", "1k", valueType=str)
        if not small_file_size in ("1k", "2k", "4k", "8k", "16k", "32k", "64k", "128k", "256k"):
            lptlog.warning("small_file_size=%s 格式error,请输入整型数字, 将采用默认值1k" % small_file_size)
        else:
            small_file_size = "1k"

        small_files_dirs = self.get_config_value(tool_node, "small_files_dirs", 0, valueType=int)

        if small_files_num == "0":
            args.append("-n")
            args.append("0")
        else:
            args.append("-n")
            args.append("%s:%s:%s:%d" %(small_files_num, small_file_size, small_file_size, small_files_dirs))

        lptlog.info("小文件数: %s k, 小文件大小: %s, 测试目录: %s" % (small_files_num, small_file_size,  small_files_dirs))

        self.times = self.get_config_value(tool_node, "times", 5, valueType=int)
        lptlog.info("测试次数: %d " % self.times)
        args.append("-x")
        args.append("%d" % self.times)

        no_buffer = self.get_config_value(tool_node, "no_buffer", "False", valueType=str)

        if no_buffer == "True":
            lptlog.info("no_buffer=True")
            args.append("-b")

        direct_io = self.get_config_value(tool_node, "direct_io", "False")
        if direct_io == "True":
            args.append("-D")
            lptlog.info("direct_io=True")


        #运行测试程序，要求保存结果到tmp目录，result_file命令为iozone_$parallel_type_$iter.out
        self.mainParameters["parameters"] = lutils.list_to_str(["bonnie++"]+args, ops=" ")
            #清除缓冲
        method.clean_buffer()
        lptlog.info("----------运行测试脚本")
        lutils.run_shell2(cmd, args_list=args, file=os.path.join(self.resultsdir, "bonnie.out"))
        lptlog.info("%s 测试数据保存在 %s 中"  %  (self.tool, os.path.join(self.resultsdir, "bonnie.out")))
	
	#create result list
        self.create_result()
        #save to result.xml
        self.save_results_to_xml()
        #create txt report
        self.txt_report()


    def create_result(self):
        '''创建result_list
           '''
        key_dic = {}
        sum_dic = {}

        file = os.path.join(self.resultsdir, "bonnie.out")
        lptlog.debug("读取 %s 文件" % file)
        if not os.path.isfile(file):
            raise IOError("open %s Error" % file)
        else:
            results_lines = lutils.read_all_lines(file)

        labels = ["name","file_size","putc","putc_cpu","put_block","put_block_cpu","rewrite","rewrite_cpu",
                "getc","getc_cpu","get_block","get_block_cpu","seeks","seeks_cpu","num_files","seq_create",
                "seq_create_cpu","seq_stat","seq_stat_cpu","seq_del","seq_del_cpu","ran_create","ran_create_cpu",
                "ran_stat","ran_stat_cpu","ran_del","ran_del_cpu" ]
        keys = labels
        keys.pop(0)
        keys.pop(0)
        keys.pop(12)
        keys = tuple(keys)

        iter=0
        for line in results_lines:
            fields = line.split(',')
            if len(fields) != 27:
                continue
            if fields[0] == "name":
                continue
            else:
                iter += 1

            lptlog.debug("line.split==27: %s" %  line)

            #attrib_dic = {'iter':str(iter), 'times':str(self.times), 'parallel':'1', 'parallels':'1' ,
                          #"name":fields[0], "filesize":fields[1], "num_files":fields[14]}
            attrib_dic = self.create_result_node_attrib(iter, self.times, 1, [1])

            #remove 多余项

            fields.pop(0)
            fields.pop(0)
            fields.pop(12)
            fields = tuple([lutils.change_type(i) for i in fields])

            for l, v in zip(keys, fields):
                key_dic[l] = "%d" % v

            if not sum_dic:
                sum_dic = key_dic.copy()
            else:
                sum_dic = method.append_sum_dict(sum_dic, key_dic)
            self.result_list.append([attrib_dic, key_dic])

        if  sum_dic:
            parallel_average_dic = method.append_average_dict(sum_dic, self.times)
            lptlog.debug("1 并行求平均值:PASS" )
            sum_attrib_dic = self.create_result_node_attrib("Average", self.times, 1, [1])
            self.result_list.append([sum_attrib_dic, parallel_average_dic])


    def after_run_once(self):

        #os.system("ln -s %s %s/db" % (self.lptdbdir, self.resultsdir))
        #os.system("ln -s %s/%s %s/report"  % (self.lptresultsdir, self.tool, self.resultsdir))
        os.system("cp -r %s %s/db" % (self.lptdbdir, self.resultsdir))
        os.system("cp  -r %s/%s %s/report"  % (self.lptresultsdir, self.tool, self.resultsdir))

