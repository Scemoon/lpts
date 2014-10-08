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
unixbench_keys = ['Dhrystone2-using-register-variables',
                    'Double-Precision-Whetstone',
                    'Execl-Throughput',
                    'FileCopy1024-bufsize2000-maxblocks',
                    'FileCopy256-bufsize500-maxblocks',
                    'FileCopy4096-bufsize8000-maxblocks',
                    'Pipe-Throughput',
                    'Pipe-based-ContextSwitching',
                    'Process-Creation',
                    'ShellScripts-1concurrent',
                    'ShellScripts-8concurrent',
                    'System-Call-Overhead',
                    'System-Benchmarks-Index-Score']
# end lpt env set


class unixbench(test.test, lpt_test.BaseTest):

    """
    This test measure system wide performance by running the following tests:
      - Dhrystone - focuses on string handling.
      - Whetstone - measure floating point operations.
      - Execl Throughput - measure the number of execl calls per second.
      - File Copy
      - Pipe throughput
      - Pipe-based context switching
      - Process creation - number of times a process can fork and reap
      - Shell Scripts - number of times a process can start and reap a script
      - System Call Overhead - estimates the cost of entering and leaving the
        kernel.

    @see: http://code.google.com/p/byte-unixbench/
    @author: Dale Curtis <dalecurtis@google.com>
    """
    version = 1

    def __init__(self, job, bindir, outputdir):
	tool = str(self.__class__.__name__)
	lpt_test.BaseTest.__init__(self, tool)
	test.test.__init__(self, job, bindir, outputdir)
        

    def initialize(self):
        self.job.require_gcc()
        self.err = []

    def setup(self, tarball='UnixBench5.1.3-1.tar.bz2'):
        """
        Compiles unixbench.

        @tarball: Path or URL to a unixbench tarball
        @see: http://byte-unixbench.googlecode.com/files/unixbench-5.1.3.tgz
        """
        tarball = utils.unmap_url(self.bindir, tarball, self.tmpdir)
        utils.extract_tarball_to_dir(tarball, self.srcdir)
        os.chdir(self.srcdir)

        #utils.system('patch -p0 < %s/Makefile.patch' % self.bindir)
        utils.make()

    def run_once(self):

	tool_node = self.check_tool_result_node()

        lptlog.info("----------开始获取测试参数")

        self.parallels =  self.get_config_array(tool_node, "parallel", [1])
        lptlog.info("测试并行组: %s" % lutils.list_to_str(self.parallels))
        self.times = self.get_config_value(tool_node, "times", 10, valueType=int)
        if self.times < 3:
            self.times = 10
            lptlog.warning("测试次数必须大于3， 将采用默认值10")
        lptlog.info("测试次数: %d" % self.times)

        cmd = "./Run"

        #执行测试脚本
        lptlog.info("---------运行测试脚本")

	#shutil.rmtree(self.resultsdir)
        os.chdir(self.srcdir)

        #添加测试次数
        args_list=["-i", "%d" %self.times]

        #添加并行数
        for parallel in self.parallels:
            args_list.append("-c")
            args_list.append("%d" % parallel)

        #utils.run_shell2(cmd, args_list=args_list, file=os.devnull)
        #utils.system_output(cmd, args=args_list)
         #返回根目录

        vars = 'UB_TMPDIR="%s" UB_RESULTDIR="%s"' % (self.tmpdir,
                                                     self.resultsdir)
        self.report_data = utils.system_output(vars + ' %s ' % cmd  + ' '.join(args_list))
        self.results_path = os.path.join(self.resultsdir,
                                         'raw_output_%s' % self.iteration)
        utils.open_write_close(self.results_path, self.report_data)

        #数据处理
	self.create_result()
        self.save_results_to_xml()
        #create txt report
        self.txt_report()


    def create_result(self):
        #数据处理
        #
        #os.chdir(self.tar_src_dir)
        #temp_result_list = glob.glob("%s/resul" % self.resultsdir)a
        #if not temp_result_list:
        #    raise NameError, "% result data not found.." % self.tool
        #else:
        #    temp_result_file = temp_result_list[0]

        self.__match_index(self.results_path)
        #返回根目录
       # os.chdir(self.lpt_root)


    def __match_index(self, file):

        '''获取unixbench屏幕输出
       '''

        result_dic = {}.fromkeys(unixbench_keys, 0)
        result_lines = lutils.read_all_lines(file)
      #  flag_dic = {}
        for parallel in self.parallels:
            re_match = "\d+ CPUs in system; running %d parallel cop\S+ of tests" % parallel
            parallel_result_dic = result_dic.copy()
            for line in result_lines:
                if re.search(re_match, line, re.I):
                    parallel_index = result_lines.index(line)
                    paralell_result_list = [ self.__get_value(result_lines, parallel_index+index) for index in (16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 29) ]
                    for l,v in zip(tuple(unixbench_keys), tuple([ lutils.change_type(i) for i in paralell_result_list])):
                        parallel_result_dic[l] = "%.1f" % v
                    parallel_result_attrib = self.create_result_node_attrib("Average", self.times, parallel, self.parallels)
                    self.result_list.append([parallel_result_attrib, parallel_result_dic])


    def __get_value(self, lines, index):

        return lines[index].split()[-1]


    def cleanup(self):
        """
        Check error index list and throw TestError if necessary.
        """
        if self.err:
            e_msg = ("No measured results for output lines: %s\nOutput:%s" %
                     (" ".join(self.err), self.report_data))
            raise error.TestError(e_msg)

    def process_section(self, section, suffix):
        keyval = {}
        subsections = section.split('\n\n')

        if len(subsections) < 3:
            raise error.TestError('Invalid output format. Unable to parse')

        # Process the subsection containing performance results first.
        for index, line in enumerate(subsections[1].strip().split('\n')):
            # Look for problems first.
            if re.search('no measured results', line, flags=re.IGNORECASE):
                self.err.append(str(index + 1))

            # Every performance result line ends with 6 values, with the sixth
            # being the actual result. Make sure there are at least that words
            # in the line before processing.
            words = line.lower().split()
            if len(words) >= 6:
                key = re.sub('\W', '', '_'.join(words[:-6]))
                keyval[key + suffix] = words[-6]

        # The final score should be the last item in the third subsection.
        keyval['score' + suffix] = subsections[2].strip().split()[-1]

        self.write_perf_keyval(keyval)

    def postprocess_iteration(self):
        # Break up sections around dividing lines.
        sections = self.report_data.split('-' * 72)

        # First section is junk to us, second has results for single CPU run.
        if len(sections) > 1:
            self.process_section(section=sections[1], suffix='')

            # Only machines with > 1 CPU will have a 3rd section.
            if len(sections) > 2:
                self.process_section(section=sections[2], suffix='_multi')
        else:
            raise error.TestError('Invalid output format. Unable to parse')

    def after_run_once(self):

        #os.system("ln -s %s %s/db" % (self.lptdbdir, self.resultsdir))
        #os.system("ln -s %s/%s %s/report"  % (self.lptresultsdir, self.tool, self.resultsdir))
        os.system("cp -r %s %s/db" % (self.lptdbdir, self.resultsdir))
        os.system("cp  -r %s/%s %s/report"  % (self.lptresultsdir, self.tool, self.resultsdir))


""" Here is a sample output:

   #    #  #    #  #  #    #          #####   ######  #    #   ####   #    #
   #    #  ##   #  #   #  #           #    #  #       ##   #  #    #  #    #
   #    #  # #  #  #    ##            #####   #####   # #  #  #       ######
   #    #  #  # #  #    ##            #    #  #       #  # #  #       #    #
   #    #  #   ##  #   #  #           #    #  #       #   ##  #    #  #    #
    ####   #    #  #  #    #          #####   ######  #    #   ####   #    #

   Version 5.1.2                      Based on the Byte Magazine Unix Benchmark

   Multi-CPU version                  Version 5 revisions by Ian Smith,
                                      Sunnyvale, CA, USA
   December 22, 2007                  johantheghost at yahoo period com


1 x Dhrystone 2 using register variables  1 2 3 4 5 6 7 8 9 10

1 x Double-Precision Whetstone  1 2 3 4 5 6 7 8 9 10

1 x Execl Throughput  1 2 3

1 x File Copy 1024 bufsize 2000 maxblocks  1 2 3

1 x File Copy 256 bufsize 500 maxblocks  1 2 3

1 x File Copy 4096 bufsize 8000 maxblocks  1 2 3

1 x Pipe Throughput  1 2 3 4 5 6 7 8 9 10

1 x Pipe-based Context Switching  1 2 3 4 5 6 7 8 9 10

1 x Process Creation  1 2 3

1 x System Call Overhead  1 2 3 4 5 6 7 8 9 10

1 x Shell Scripts (1 concurrent)  1 2 3

1 x Shell Scripts (8 concurrent)  1 2 3

2 x Dhrystone 2 using register variables  1 2 3 4 5 6 7 8 9 10

2 x Double-Precision Whetstone  1 2 3 4 5 6 7 8 9 10

2 x Execl Throughput  1 2 3

2 x File Copy 1024 bufsize 2000 maxblocks  1 2 3

2 x File Copy 256 bufsize 500 maxblocks  1 2 3

2 x File Copy 4096 bufsize 8000 maxblocks  1 2 3

2 x Pipe Throughput  1 2 3 4 5 6 7 8 9 10

2 x Pipe-based Context Switching  1 2 3 4 5 6 7 8 9 10

2 x Process Creation  1 2 3

2 x System Call Overhead  1 2 3 4 5 6 7 8 9 10

2 x Shell Scripts (1 concurrent)  1 2 3

2 x Shell Scripts (8 concurrent)  1 2 3

========================================================================
   BYTE UNIX Benchmarks (Version 5.1.2)

   System: localhost: GNU/Linux
   OS: GNU/Linux -- 2.6.32.26+drm33.12 -- #1 SMP Wed Jan 12 16:16:05 PST 2011
   Machine: i686 (GenuineIntel)
   Language: en_US.utf8 (charmap=, collate=)
   CPU 0: Intel(R) Atom(TM) CPU N455 @ 1.66GHz (3325.2 bogomips)
          Hyper-Threading, x86-64, MMX, Physical Address Ext, SYSENTER/SYSEXIT
   CPU 1: Intel(R) Atom(TM) CPU N455 @ 1.66GHz (3325.0 bogomips)
          Hyper-Threading, x86-64, MMX, Physical Address Ext, SYSENTER/SYSEXIT
   14:11:59 up 1 day,  1:10,  0 users,  load average: 0.47, 0.48, 0.51; runlevel

------------------------------------------------------------------------
Benchmark Run: Fri Jan 14 2011 14:11:59 - 14:41:26
2 CPUs in system; running 1 parallel copy of tests

Dhrystone 2 using register variables        2264000.6 lps   (10.0 s, 7 samples)
Double-Precision Whetstone                      507.0 MWIPS (10.1 s, 7 samples)
Execl Throughput                                796.7 lps   (30.0 s, 2 samples)
File Copy 1024 bufsize 2000 maxblocks        110924.1 KBps  (30.1 s, 2 samples)
File Copy 256 bufsize 500 maxblocks           32600.5 KBps  (30.1 s, 2 samples)
File Copy 4096 bufsize 8000 maxblocks        284236.5 KBps  (30.0 s, 2 samples)
Pipe Throughput                              301672.5 lps   (10.0 s, 7 samples)
Pipe-based Context Switching                  29475.3 lps   (10.0 s, 7 samples)
Process Creation                               3124.6 lps   (30.0 s, 2 samples)
Shell Scripts (1 concurrent)                   1753.0 lpm   (60.0 s, 2 samples)
Shell Scripts (8 concurrent)                    305.9 lpm   (60.1 s, 2 samples)
System Call Overhead                         592781.7 lps   (10.0 s, 7 samples)

System Benchmarks Index Values               BASELINE       RESULT    INDEX
Dhrystone 2 using register variables         116700.0    2264000.6    194.0
Double-Precision Whetstone                       55.0        507.0     92.2
Execl Throughput                                 43.0        796.7    185.3
File Copy 1024 bufsize 2000 maxblocks          3960.0     110924.1    280.1
File Copy 256 bufsize 500 maxblocks            1655.0      32600.5    197.0
File Copy 4096 bufsize 8000 maxblocks          5800.0     284236.5    490.1
Pipe Throughput                               12440.0     301672.5    242.5
Pipe-based Context Switching                   4000.0      29475.3     73.7
Process Creation                                126.0       3124.6    248.0
Shell Scripts (1 concurrent)                     42.4       1753.0    413.4
Shell Scripts (8 concurrent)                      6.0        305.9    509.8
System Call Overhead                          15000.0     592781.7    395.2
                                                                   ========
System Benchmarks Index Score                                         238.0

------------------------------------------------------------------------
Benchmark Run: Fri Jan 14 2011 14:41:26 - 15:09:23
2 CPUs in system; running 2 parallel copies of tests

Dhrystone 2 using register variables        3411919.6 lps   (10.0 s, 7 samples)
Double-Precision Whetstone                      964.3 MWIPS (10.1 s, 7 samples)
Execl Throughput                               2053.5 lps   (30.0 s, 2 samples)
File Copy 1024 bufsize 2000 maxblocks        158308.0 KBps  (30.0 s, 2 samples)
File Copy 256 bufsize 500 maxblocks           46249.5 KBps  (30.0 s, 2 samples)
File Copy 4096 bufsize 8000 maxblocks        389881.9 KBps  (30.0 s, 2 samples)
Pipe Throughput                              410193.1 lps   (10.0 s, 7 samples)
Pipe-based Context Switching                 113780.0 lps   (10.0 s, 7 samples)
Process Creation                               7609.0 lps   (30.0 s, 2 samples)
Shell Scripts (1 concurrent)                   2355.0 lpm   (60.0 s, 2 samples)
Shell Scripts (8 concurrent)                    308.1 lpm   (60.2 s, 2 samples)
System Call Overhead                        1057063.2 lps   (10.0 s, 7 samples)

System Benchmarks Index Values               BASELINE       RESULT    INDEX
Dhrystone 2 using register variables         116700.0    3411919.6    292.4
Double-Precision Whetstone                       55.0        964.3    175.3
Execl Throughput                                 43.0       2053.5    477.6
File Copy 1024 bufsize 2000 maxblocks          3960.0     158308.0    399.8
File Copy 256 bufsize 500 maxblocks            1655.0      46249.5    279.5
File Copy 4096 bufsize 8000 maxblocks          5800.0     389881.9    672.2
Pipe Throughput                               12440.0     410193.1    329.7
Pipe-based Context Switching                   4000.0     113780.0    284.5
Process Creation                                126.0       7609.0    603.9
Shell Scripts (1 concurrent)                     42.4       2355.0    555.4
Shell Scripts (8 concurrent)                      6.0        308.1    513.5
System Call Overhead                          15000.0    1057063.2    704.7
                                                                   ========
System Benchmarks Index Score                                         407.4

"""
