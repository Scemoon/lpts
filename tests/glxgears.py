# -*- coding:utf-8 -*-
'''
  x11perf测试工具执行脚本
'''

import os, shutil, re
from .test import BaseTest
from lpt.lib.error import *
from lpt.lib import lptxml
from lpt.lib import lptlog
from lpt.lib.share import utils
from lpt.lib import lptreport
import glob


glxgears_keys = ["gears"]
    
class TestControl(BaseTest):
    '''
    继承BaseTest属性和方法
    '''
    def __init__(self, jobs_xml, job_node, tool, tarball='UnixBench5.1.3-1.tar.bz2'):
        super(TestControl, self).__init__(jobs_xml, job_node, tool, tarball)
        
        
    def check_deps(self):
        '''编译ubgears需要提供libx11-devel包和libGL-devel包
        '''
        utils.has_gcc()
        utils.has_file("libX11-devel", "/usr/include/X11/Xlib.h")
        utils.has_file("libGL-devel", "/usr/include/GL/gl.h")
        utils.has_file("libXext-devel","/usr/include/X11/extensions/Xext.h")
        
    def setup(self):
        '''编译源码，设置程序
        '''
        if not self.check_bin(self.processBin):
            self.tar_src_dir = self.extract_bar()
            os.chdir(self.tar_src_dir)
            utils.make(extra='clean', make='make')
             #修改Makefile文件
    
            lptlog.info("修改Makefile, 取消#GRAPHIC_TESTS = defined注释")
            cmd = '''sed -i "s/^#GRAPHIC_TESTS/GRAPHIC_TESTS/g" Makefile '''
            utils.system(cmd)
            self.compile(make_status=True)
            os.chdir(self.lpt_root)
                
    def run(self):
        
        tool_node = self.check_tool_result_node()
            
        lptlog.info("----------开始获取测试参数")
        
        self.times = self.get_config_value(tool_node, "times", 10, valueType=int)
        lptlog.info("测试次数: %d" % self.times)     
     
        self.parallels = [1]
            
        cmd = "./Run"
        args_list = ["ubgears", "-i", "%d" % self.times]
        self.mainParameters["parameters"] = " ".join([cmd]+args_list) 
        #运行unixbench程序，进入unixbench 根目录
        os.chdir(self.tar_src_dir)
        utils.system("rm -rf results/*")
        lptlog.info("---------运行测试脚本")
        utils.run_shell2(cmd, args_list=args_list, file=os.devnull)
    
        os.chdir(self.lpt_root)
        
    def create_result(self):           
        #数据处理
        #
        os.chdir(self.tar_src_dir)
        temp_result_list = glob.glob("./results/*[0-9]")
        if not temp_result_list:
            raise NameError("% result data not found.." % self.tool)
        else:
            temp_result_file = temp_result_list[0]
        
        self.__match_index(temp_result_file)
        #返回根目录
        os.chdir(self.lpt_root)
        
    def __match_index(self, file):
     
        '''获取unixbench屏幕输出
       '''
        self.parallels = [1]
        self.times = 3
        result_dic = {}.fromkeys(glxgears_keys, 0)
        result_lines = utils.read_all_lines(file)
        for parallel in self.parallels:
            re_match = "[\d]+ CPUs in system; running %d parallel copy of tests" % parallel
            parallel_result_dic = result_dic.copy()
            for line in result_lines:
                if re.search(re_match, line, re.I):
                    parallel_index = result_lines.index(line)
                    paralell_result_list = [ self.__get_value(result_lines, parallel_index+index) for index in (5,) ]
                    for l,v in zip(tuple(glxgears_keys), tuple([utils.change_type(i) for i in paralell_result_list])):
                        parallel_result_dic[l] = "%.1f" % v
                    parallel_result_attrib = self.create_result_node_attrib("Average", self.times, parallel, self.parallels)
                    self.result_list.append([parallel_result_attrib, parallel_result_dic])
    
    def __get_value(self, lines, index):
      
        return lines[index].split()[-2]
   
    
    
