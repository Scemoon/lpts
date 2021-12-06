# -*- coding:utf-8 -*-
'''
  x11perf，测试工具执行脚本
'''

import os, shutil, re
from .test import BaseTest
from lpt.lib.error import *
from lpt.lib import lptxml
from lpt.lib import lptlog
from lpt.lib.share import utils
from lpt.lib import lptreport
import glob


x11perf_keys = ['aa-polygon',
                'ellipses',
                'images-and-blits',
                'rectangles',
                'text',
                'windows']

    
class TestControl(BaseTest):
    '''
    @attention: 继承BaseTest属性和方法，将采用UnixBench中关于x11perf的测试方法，因此测试时需要先安装UnixBench
    '''
    def __init__(self, jobs_xml, job_node, tool, tarball='UnixBench5.1.3-1.tar.bz2'):
        super(TestControl, self).__init__(jobs_xml, job_node, tool, tarball)
      
    def __compile_x11perf(self, x11perf_tar="x11perf-1.5.3.tar.gz"):
        x11perf_tar_path = os.path.join(self.tools_dir, x11perf_tar)
        lptlog.info("解压x11perf压缩包")
        x11perf_srcdir = utils.extract_tarball_to_dir(x11perf_tar_path, self.src_dir)
        lptlog.info("x11per源目录: %s " % x11perf_srcdir)
        
        os.chdir(x11perf_srcdir)
        if os.path.isdir(x11perf_srcdir):
            lptlog.debug("编译x11perf测试程序")
            self.compile(configure_status=True, make_status=True, make_install_status=True) 
        #返回根lpt根目录
        os.chdir(self.lpt_root)
    
    
    def setup(self):
        '''编译源码，设置程序
        '''
               
        if not self.check_bin(self.processBin):
            self.tar_src_dir = self.extract_bar()
            os.chdir(self.tar_src_dir)
            self.compile(make_status=True)
            os.chdir(self.lpt_root)
                
        #检查x11perf安装程序
        if os.path.exists("/usr/bin/x11perf") or  os.path.exists("/usr/local/bin/x11perf"):
            lptlog.info("将使用系统x11perf程序")
        else:
            raise ValueError("请安装x11perf程序, xort-x11-apps")
            lptlog.info("系统中并没有安装x11perf程序，由lpt安装x11perf-1.5.3程序，如果系统缺少依赖，请安装提示安装依赖")
            utils.has_file("libX11-devel", "/usr/include/X11/Xlib.h")
            utils.has_file("libXmu-devel", "/usr/include/X11/Xmu/Xmu.h")
            utils.has_file("libXrender-devel", "/usr/include/X11/extensions/Xrender.h")
            self.__compile_x11perf(x11perf_tar="x11perf-1.5.3.tar.bz2")
        
    def run(self):
        '''
        '''
        tool_node = self.check_tool_result_node()
        lptlog.info("----------开始获取测试参数")
        self.parallels = [1]
        self.times = self.get_config_value(tool_node, "times", 10, valueType=int)
        lptlog.info("测试次数: %d" % self.times)
        cmd = "./Run"
        args_list = ["graphics", "-i", "%d" % self.times]
        #运行unixbench程序，进入unixbench 根目录, 清理环境
        os.chdir(self.tar_src_dir)
        os.system("rm -rf results/*")
        
        #执行测试程序
        lptlog.info("---------运行测试脚本")
        self.mainParameters["parameters"] = " ".join([cmd]+args_list)
        utils.run_shell2(cmd, args_list=args_list, file=os.devnull)
     
        #返回根目录
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
        result_dic = {}.fromkeys(x11perf_keys, 0)
        result_lines = utils.read_all_lines(file)
        for parallel in self.parallels:
            re_match = "[\d]+ CPUs in system; running %d parallel copy of tests" % parallel
            parallel_result_dic = result_dic.copy()
            for line in result_lines:
                if re.search(re_match, line, re.I):
                    parallel_index = result_lines.index(line)
                    paralell_result_list = [ self.__get_value(result_lines, parallel_index+index) for index in (10, 11, 12, 13, 14, 15) ]
                    for l,v in zip(tuple(x11perf_keys), tuple([utils.change_type(i) for i in paralell_result_list])):
                        parallel_result_dic[l] = "%.1f" % v
                    parallel_result_attrib = self.create_result_node_attrib("Average", self.times, parallel, self.parallels)
                    self.result_list.append([parallel_result_attrib, parallel_result_dic])
    
    def __get_value(self, lines, index):
      
        return lines[index].split()[-2]
