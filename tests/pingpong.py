# -*- coding:utf-8 -*-
'''
  pingpong测试工具执行脚本
'''

import os, shutil, re
from test import BaseTest
from lpt.lib.error import *
from lpt.lib import lptxml
from lpt.lib import lptlog
from lpt.lib.share import utils
from lpt.lib import lptreport

    
class TestControl(BaseTest):
    '''
    继承BaseTest属性和方法
    '''
    def __init__(self, jobs_xml, job_node, tool, tarball='pingpong-0.1.tar.bz2'):
        super(TestControl, self).__init__(jobs_xml, job_node, tool, tarball)
        self.processBin = os.path.join(self.bin_dir, 'pingpong')
        self.processBin2 = os.path.join(self.bin_dir, 'pprun')
    
        
    def setup(self):
        '''编译源码，设置程序
        '''
        if not self.check_bin(self.processBin):
            self.tar_src_dir = self.extract_bar()
            os.chdir(self.tar_src_dir)
            self.compile(make_status=True,  make_install_status=True, make_install_para='-e LPTBIN=%s' % self.bin_dir)
            os.chdir(self.lpt_root)
                
    def run(self):
         
        tool_node = self.check_tool_result_node()
        lptlog.info("----------开始获取测试参数")
              
        self.games = self.get_config_array(tool_node, "games", [64,128,256])
        lptlog.info("测试games组： %s" % utils.list_to_str(self.games))
        self.times = self.get_config_value(tool_node, "times", 18, valueType=int)
        lptlog.info("测试次数: %s" % self.times)        
                                    
        cmd = self.processBin2
                 
           #执行测试程序
        lptlog.info("----------运行测试脚本")
        for game in self.games:
            lptlog.info("执行 %s games" % game)
            args = ['-b', self.bin_dir, '-c', "%d" % self.times, '-t', "%d" % game, '-d', self.tmp_dir]
            result_tmp_file = os.path.join(self.tmp_dir, "%d.pingpong" % game)
            utils.run_shell2(cmd, args_list=args, file=result_tmp_file)
            lptlog.info("%d games测试数据保存到: %s" % (game, result_tmp_file))
            

    
    def create_result(self):
        '''创建result_list
        '''
        for game in self.games:
           
            result_tmp_file = os.path.join(self.tmp_dir, "%s.pingpong" % game)
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

        results_lines = utils.read_all_lines(file)
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
        init_time_average = utils.average_list(utils.string_to_float(init_time_list), bits=0)
        #完成时间求平均值
        complete_time_average = utils.average_list(utils.string_to_float(complete_time_list), bits=0)
        sum_time = init_time_average + complete_time_average
        #定义result字典
        for l,v in zip(labels, (init_time_average,  complete_time_average, sum_time)):
            result_dict[l] = "%d" % v
       #定义result属性
        result_node_attrib = self.create_result_node_attrib("Average", self.times, game*2, [i*2 for i in self.games])
        
        result_list.append(result_dict)
        result_list.insert(0, result_node_attrib)
    
        return result_list
    
    
