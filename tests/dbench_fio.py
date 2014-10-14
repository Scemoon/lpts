# -*- coding:utf-8 -*-
'''
  bonnie++测试工具执行脚本
'''

import os, shutil, re, getpass
from test import BaseTest
from lpt.lib.error import *
from lpt.lib import lptxml
from lpt.lib import lptlog
from lpt.lib.share import utils
from lpt.lib import lptreport
from share import method
from lpt.lib import sysinfo

result_node_attrib = {'iter':'1', 'times':'1', 'parallel':'1', 'parallels':'1' }

class TestControl(BaseTest):
    '''
    继承test属性和方法
    '''
    def __init__(self, jobs_xml, job_node, tool, tarball='dbench-4.0.0.tar.bz2'):
        super(TestControl, self).__init__(jobs_xml, job_node, tool, tarball)
        self.processBin = os.path.join(self.bin_dir, 'dbench')
        self.times = None
        self.parallel_type = None
        self.parallels = None
	utils.system("ulimit -n 100000", ignore_status=True)
       
    @method.print_deps_log
    def check_deps(self):
        '''
        检查是否含缺少依赖
        @note: gcc 是必须的
        '''
        utils.has_gcc()
        utils.has_file("popt-devel", "/usr/include/popt.h")
        utils.has_file("zlib-devel", "/usr/include/zlib.h")
     
            
    def setup(self):
        '''编译源码，设置程序
        '''
        if not self.check_bin(self.processBin):
            self.tar_src_dir = self.extract_bar()
            os.chdir(self.tar_src_dir)
            os.system("./autogen.sh")
            self.compile(configure_status=True, make_status=True)
            utils.copy(os.path.join(self.tar_src_dir, 'dbench'), self.processBin)
            if not os.path.exists(os.path.join(self.tmp_dir, "loadfiles")):
		          utils.copy(os.path.join(self.tar_src_dir, 'loadfiles'), os.path.join(self.tmp_dir, "loadfiles"))
            os.chdir(self.lpt_root) 
                                 
    def run(self):
    
        tool_node = self.check_tool_result_node()
            
        lptlog.info("----------获取测试参数")
        
        cmd = self.processBin
        args = ['-B', 'fileio',  '-c', os.path.join(self.tmp_dir, 'loadfiles/client.txt'), '-R', '999999.99']
        
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
        lptlog.info("测试并行: %s" % utils.list_to_str(self.parallels))
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
        
        self.mainParameters["parameters"] = " ".join(["dbench"]+args)
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
                tmp_file = os.path.join(self.tmp_dir, "%s_%s_%s.out" % (self.tool, parallel, iter+1))
                   
                    #清除buffer
                method.clean_buffer()
                utils.run_shell2(self.processBin, args_list=args+parallel_args, file=tmp_file)
                lptlog.info("%d 并行  第 %d 次测试，测试数据保存在: %s " % (parallel, iter+1, tmp_file))
        
               
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
                tmp_result_file = os.path.join(self.tmp_dir, "%s_%s_%s.out" % (self.tool, parallel, iter+1))
                if not os.path.isfile(tmp_result_file):
                    lptlog.warning("%s 不存在" % tmp_result_file)
                    continue
                result_lines = utils.read_all_lines(tmp_result_file)
                for line in result_lines:
                    key_dic = {}
                    if r.match(line):
                        m = r.match(line)
                        #result_list = [m.group(1), m.group(2), m.group(3)]
                        result_list = [m.group(1), m.group(3)]
                        result_tuple = tuple([utils.change_type(i)for i in result_list])
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
        
            
    
                                    
                
  
