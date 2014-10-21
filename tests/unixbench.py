# -*- coding:utf-8 -*-
'''
  unixbench测试工具执行脚本
'''

import os, shutil, re
from test import BaseTest
from lpt.lib.error import *
from lpt.lib import lptxml
from lpt.lib import lptlog
from lpt.lib.share import utils
from lpt.lib import lptreport
import glob

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


class TestControl(BaseTest):
    '''
    继承BaseTest属性和方法
    '''
    def __init__(self, jobs_xml, job_node, tool, tarball='UnixBench5.1.3-1.tar.bz2'):
        super(TestControl, self).__init__(jobs_xml, job_node, tool, tarball)
        #self.unixbench_bin = os.path.join(self.bin_dir, 'unixbench')
        
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
            
        lptlog.info("----------开始获取测试参数")
        
        self.parallels =  self.get_config_array(tool_node, "parallel", [1])
        lptlog.info("测试并行组: %s" % utils.list_to_str(self.parallels))
        self.times = self.get_config_value(tool_node, "times", 10, valueType=int)
        if self.times < 3:
            self.times = 10
            lptlog.warning("测试次数必须大于3， 将采用默认值10")
        lptlog.info("测试次数: %d" % self.times)
               
        cmd = "./Run"
        
            #运行unixbench程序，进入unixbench 根目录, 清理环境
        os.chdir(self.tar_src_dir)
        utils.system("rm -rf results/*")
        
        #执行测试程序
        #执行测试脚本
        lptlog.info("---------运行测试脚本")
        #添加测试次数
        args_list=["-i", "%d" %self.times]
      
     #添加并行数
        for parallel in self.parallels:
            args_list.append("-c")
            args_list.append("%d" % parallel)
        
        self.mainParameters["parameters"] = " ".join([cmd]+args_list)
        utils.run_shell2(cmd, args_list=args_list, file=os.devnull)
        #utils.system_output(cmd, args=args_list)
         #返回根目录
        os.chdir(self.lpt_root)
        
    def create_result(self):           
        #数据处理
        #
        os.chdir(self.tar_src_dir)
        temp_result_list = glob.glob("./results/*[0-9]")
        if not temp_result_list:
            raise NameError, "% result data not found.." % self.tool
        else:
            temp_result_file = temp_result_list[0]
        
        self.__match_index(temp_result_file)
        #返回根目录
        os.chdir(self.lpt_root)
        
    def __match_index(self, file):
     
        '''获取unixbench屏幕输出
       '''
       
        result_dic = {}.fromkeys(unixbench_keys, 0)
        result_lines = utils.read_all_lines(file)
      #  flag_dic = {}
        for parallel in self.parallels:
            re_match = "\d+ CPUs in system; running %d parallel cop\S+ of tests" % parallel
            parallel_result_dic = result_dic.copy()
            for line in result_lines:
                if re.search(re_match, line, re.I):
                    parallel_index = result_lines.index(line)
                    paralell_result_list = [ self.__get_value(result_lines, parallel_index+index) for index in (16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 29) ]
                    for l,v in zip(tuple(unixbench_keys), tuple([utils.change_type(i) for i in paralell_result_list])):
                        parallel_result_dic[l] = "%.1f" % v
                    parallel_result_attrib = self.create_result_node_attrib("Average", self.times, parallel, self.parallels)
                    self.result_list.append([parallel_result_attrib, parallel_result_dic])
        
    
    def __get_value(self, lines, index):
      
        return lines[index].split()[-1]
