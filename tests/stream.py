# -*- coding:utf-8 -*-
'''
  stream测试工具执行脚本
'''

import os, shutil,re
from test import BaseTest
from lpt.lib.error import *
from lpt.lib import lptxml
from lpt.lib import lptlog
from lpt.lib.share import utils
from lpt.lib import lptreport
from share import method

  
class TestControl(BaseTest):
    '''
    继承BaseTest属性和方法
    '''
    def __init__(self, jobs_xml, job_node, tool, tarball='stream-5.9-1.tar.bz2'):
        super(TestControl, self).__init__(jobs_xml, job_node, tool, tarball)
        self.processBin = os.path.join(self.bin_dir, 'stream')
        self.processBin2 = os.path.join(self.bin_dir, 'stream_mu')
        self.times = None
        self.parallels = None
        
        
    def setup(self):
        '''编译源码，设置程序
        '''
        if not self.check_bin(self.processBin, self.processBin2):
            self.tar_src_dir = self.extract_bar()
            os.chdir(self.tar_src_dir)
            self.compile(make_status=True)
            utils.copy(os.path.join(self.tar_src_dir, 'stream'), self.processBin)
            utils.copy(os.path.join(self.tar_src_dir, 'stream_mu'), self.processBin2)
            os.chdir(self.lpt_root)
                  
    def run(self):
        
        tool_node = self.check_tool_result_node()
            
        lptlog.info("-----------开始获取测试参数")
        testmode = self.get_config_value(tool_node, "testmode", "default", valueType=str)
        lptlog.info("测试模式： %s" % testmode)
        
        self.parallels = self.get_config_array(tool_node, "parallel", [1])
        lptlog.info("测试并行数组： %s" % ",".join(map(str, self.parallels)))
        
        self.times = self.get_config_value(tool_node, "times", 5, valueType=int)
        lptlog.info("测试次数: %d" % self.times )
        if testmode == 'custom':
            cmd = self.processBin2
                                
        else:
            cmd = self.processBin
            self.parallels = [1]
            
             
        lptlog.info("----------运行测试脚本")      
        #执行测试程序
        for parallel in self.parallels:
            if parallel == 1:
                pass
            else:
                os.environ['OMP_NUM_THREADS'] = str(parallel)
            for iter in range(self.times):
                lptlog.info('并行数 %d, 第 %d 测试：PASS' % (parallel, iter+1))
                tmp_result_file = os.path.join(self.tmp_dir, "stream_%d_%d.out" %(parallel, iter+1))
                utils.run_shell2(cmd, args_list=[], file=tmp_result_file)


    def create_result(self):
        #method.check_none(self.parallels, self.times)
        labels = ("Copy", 'Scale', 'Add', 'Triad')
                
        for parallel in self.parallels:
            sum_dic = {}
            for iter in range(self.times):
                iter_dic = {}
                tmp_result_file = os.path.join(self.tmp_dir, "stream_%d_%d.out" %(parallel, iter+1))
                if not os.path.isfile(tmp_result_file):
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
        lines = utils.read_all_lines(file)
        for line in lines:
            if r.match(line):
                copy = line.split()[1]
                index = lines.index(line)
                scale = lines[index+1].split()[1]
                add = lines[index+2].split()[1]
                triad = lines[index+3].split()[1]
                return tuple(map(utils.change_type, [copy, scale, add, triad]))
    
        return (0, 0, 0, 0)
    

       
