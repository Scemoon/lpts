# -*- coding:utf-8 -*-
'''
  iozone测试工具执行脚本
'''

import os, shutil, re, getpass, stat
from test import BaseTest
from lpt.lib.error import *
from lpt.lib import lptxml
from lpt.lib import lptlog
from lpt.lib.share import utils
from lpt.lib import lptreport
from share import method
from lpt.lib import sysinfo

     
class TestControl(BaseTest):
    '''
    继承BaseTest属性和方法
    '''
    def __init__(self, jobs_xml, job_node, tool, tarball='iozone3_424.tar.bz2'):
        super(TestControl, self).__init__(jobs_xml, job_node, tool, tarball)
        self.processBin = os.path.join(self.bin_dir, 'iozone')
        self.times = None
        self.testmode = None
        self.parallel_type = None
        self.parallels = None
            
    def setup(self):
        '''编译源码，设置程序
        '''
        if not self.check_bin(self.processBin):
            self.tar_src_dir = self.extract_bar()
            os.chdir(os.path.join(self.tar_src_dir, "src/current"))
            arch = sysinfo.get_current_kernel_arch()
            lptlog.debug("硬件架构: %s " % arch)
            if (arch == 'ppc'):
                para = 'linux-powerpc'
            elif (arch == 'ppc64'):
                para = 'linux-powerpc64'
            elif (arch == 'x86_64'):
                para ='linux-AMD64'
            elif (arch == "mips64el"):
                para = "linux-AMD64"
            else:
                para = "linux"
                
            self.compile(make_status=True,  make_para=para)
            utils.copy(os.path.join(self.tar_src_dir, 'src/current/iozone'), self.processBin)
                              
    def run(self):
        
        tool_node = self.check_tool_result_node()
            
        lptlog.info("----------开始获取测试参数")
        
        speed_mount_status=False
        args = ["-i", "0", "-i" ,"1", "-i", "2"]
    
        self.testmode = self.get_config_value(tool_node, "testmode", os.path.join(self.tmp_dir, "speed"), valueType=str)
        if  self.testmode not in ("speed", "throughput"):
            self.testmode = "speed"
        lptlog.info("测试模式: %s" % self.testmode)
        
        testdir = self.get_config_testdir(tool_node)
            #获取设备,并尝试挂载到testdir,返回True或者False
        devices_status = self.get_config_devices(tool_node, testdir)
            
        filesize = self.get_config_value(tool_node, "filesize", "10g")
        if not utils.check_size_format(filesize):
            lptlog.warning("%s 格式 error,将采用默认大小10g" % filesize)
            filesize = "10g"
        lptlog.info("测试文件大小： %s" % filesize)     
        args.append("-s")
        args.append(filesize)
            
        blocksize = self.get_config_value(tool_node, "blocksize", "4k")
        if not utils.check_size_format(blocksize, match="[\d]+k?"):
            lptlog.warning("blocksize=%s 格式 error,将采用默认大小4k" % blocksize)
            
        lptlog.info("测试块大小: %s" % blocksize)
        args.append("-r")
        args.append(blocksize)
            
        self.times = self.get_config_value(tool_node, "times", 5, valueType=int)
	direct_status = self.get_config_value(tool_node, "directio", "False", valueType=str)
	if direct_status == "True":
	    args.append("-I")
	    lptlog.info("DirectIO: True")
        
        self.parallel_type = self.get_config_value(tool_node, "parallel_type", "process", valueType=str)
        if self.parallel_type  not in ("threads", "process"):
            self.parallel_type = "process"
        lptlog.info("测试并行方式: %s" % self.parallel_type)
        
        self.parallels = self.get_config_array(tool_node, "parallel", [4])
        lptlog.info("测试并行: %s" % utils.list_to_str(self.parallels))
        
        if self.testmode == "speed":
            self.parallels = [1]
        #运行测试程序，要求保存结果到tmp目录，result_file命令为iozone_$parallel_type_$iter.out
        lptlog.info("----------运行测试脚本")
        for parallel in self.parallels:
            parallel_args = []
            lptlog.info("%s 并行测试" % parallel)
            if self.testmode == 'throughput':
                parallel_args.append("-t")
                parallel_args.append(str(parallel))
                parallel_args.append("-F")
                for num in range(parallel):
                    parallel_args.append(os.path.join(testdir, "iozone_%s_%s_%s") % (self.testmode, parallel, num+1))
                
                if self.parallel_type == "threads":
                    parallel_args.append("-T")
         
            else:
               # if devices_status:
                  #  parallel_args.append("-U")
                 #   parallel_args.append(testdir)
                    
                parallel_args.append("-f")
                parallel_args.append("%s/iozone_test_file" % testdir) 
        
            for iter in range(self.times):
                lptlog.info("第 %d 次测试" % (iter+1))
                iozone_iter_result_file = os.path.join(self.tmp_dir, "iozone_%s_%d_%d.out" % (self.testmode, parallel, (iter+1)) )

                    #清除缓冲
                method.clean_buffer()
                utils.run_shell2(self.processBin, args_list=args+parallel_args, file=iozone_iter_result_file)
                lptlog.info("%s %s方式, %s并行, 第%d次测试数据保存在 %s 中"  % (self.tool, self.testmode, parallel, (iter+1), iozone_iter_result_file))
                
               
                #处理测试结果
            #self.result_list = deal_data(self.tmp_dir, self.testmode, self.times, self.parallels)
            
    def create_result(self):
        '''Create Results 
        '''
        
        for parallel in self.parallels: 
            sum_dic = {}
            for iter in range(self.times):
                iozone_parallel_list = []
                iozone_temp_file = os.path.join(self.tmp_dir, "iozone_%s_%d_%d.out" % (self.testmode, parallel, (iter+1)))
                iozone_dic = self.__match_index(iozone_temp_file)
                if not sum_dic:
                    sum_dic = iozone_dic.copy()
                else:
                    sum_dic = method.append_sum_dict(sum_dic, iozone_dic)
                iozone_attrib = self.create_result_node_attrib(iter+1, self.times, parallel, self.parallels)
                self.result_list.append([iozone_attrib, iozone_dic])
            if sum_dic:
                parallel_average_dic = method.append_average_dict(sum_dic, self.times)
                self.result_list.append([self.create_result_node_attrib("Average", self.times, parallel, self.parallels), parallel_average_dic])
       

       
    def __match_index(self, file):
        '''
        @return: 测试指标，dict
        @attention: 采用autotest中部分代码
            '''
   
        keylist = {}
        if not os.path.isfile(file):
            return []
        
        lptlog.debug("在%s中搜索测试指标" % file)
        results_lines = utils.read_all_lines(file)

        if self.testmode == "speed": 
        #labels = ('write', 'rewrite', 'read', 'reread', 'randread','randwrite', 
        #          'bkwdread', 'recordrewrite', 'strideread', 'fwrite', 
         #         'frewrite', 'fread', 'freread')
         
            labels = ('write', 'rewrite', 'read', 'reread', 'randread','randwrite')
            for line in results_lines:
                fields = line.split()
                if len(fields) != 8:
                    continue
                lptlog.debug("line.split==8: %s" %  line)
                try:
                    fields = tuple([int(i) for i in fields])
                except Exception:
                    continue
                           
                for l, v in zip(labels, fields[2:]):
                    key_name = "%s" % l
                    keylist[key_name] = "%d" % v               
        else:
            child_regexp  = re.compile(r'Children see throughput for[\s]+([\d]+)[\s]+([\S]+|[\S]+[\s][\S]+)[\s]+=[\s]+([\w]+)*')
            section = None
            w_count = 0
            for line in results_lines:
                line = line.strip()

            # Check for the beginning of a new result section
                match = child_regexp.search(line)
           
                if match:
             # Extract the section name and the worker count
                    w_count = int(match.group(1))
                    lptlog.debug("w_count:%s" % w_count)
                    section = self.__get_section_name(match.group(2))
                    lptlog.debug("section:%s" % section)

                # Output the appropriate keyval pair
		    #key_name = '%s-kids' % section
                    #keylist[key_name] = match.group(3)
                    keylist[section] = match.group(3)

        return keylist
                
    def __get_section_name(self, desc):
        #return desc.strip().replace(' ', '-')
        if desc == "initial writers":
            return "write"
        elif desc == "rewriters":
            return "rewrite"
        elif desc == "readers":
            return "read"
        elif desc == "re-readers":
            return "reread"
        elif desc == "random readers":
            return "randread"
        elif desc == "random writers":
            return "randwrite"
 
