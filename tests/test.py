# -*- coding:utf-8 -*-

'''
   定义测试工具测试方法
'''

import os, shutil, getpass, stat
from lpt.lib.share import  utils
from lpt.lib import lptxml
from lpt.lib import lptlog
from lpt.lib import lptreport
from lpt.lib.error import *
from share import method


#获取LPT ROOT PATH
LPTPATH = os.getenv('LPTROOT')

#解压路径
SRC_DIR = os.path.join(LPTPATH, 'src')

#可执行文件或者脚本
BIN_DIR = os.path.join(LPTPATH, 'bin')

#工具源码包
TOOLS_DIR = os.path.join(LPTPATH, 'tools')

#result目录
RESULTS_DIR = os.path.join(LPTPATH, 'results')

#tmp
TMP_DIR = os.path.join(LPTPATH, 'tmp')

#data目录
DB_DIR = os.path.join(LPTPATH, 'db')
JOBS_XML = os.path.join(DB_DIR, 'jobs.xml')


#判断文件或者目录是否存在
for dir in (SRC_DIR, BIN_DIR, TOOLS_DIR, RESULTS_DIR, DB_DIR):
    if not os.path.exists(dir):
        os.mkdir(dir)
    elif not os.path.isdir(dir):
        os.remove(dir) 
        os.mkdir(dir) 
    else:
        pass
    
    
class BaseTest(lptxml.XmlResults):
    '''
    定义测试工具测试方法
    @Function:check_debps,检查测试依赖， GCC必须
    @Function:extract_bar,解压缩tar, 如果True返回解压后的源码路径， False返回NameError
    @Function:compile, 编译源码，提供包括configure、make、make install参数
    @Function:setup,定义测试程序安装方法，和执行的一些前提条件（必须）
    @Fnction:run， 测试程序执行方法， 包括生成result处理方法
    @Function: save_results_to_xml, 处理测试工具原测试数据，经过处理保存到result.xml中
    @Function:txt_report, 读取result.xml，生成可读性更高的txt测试报告
    @Function:clean, 定义清除
    
    '''
    def __init__(self, jobs_xml, job_node, tool, tarball):
        self.lpt_root = LPTPATH
        self.tarball = tarball
        self.tarpath = os.path.join(TOOLS_DIR, tarball)
        self.src_dir = SRC_DIR
        self.tools_dir = TOOLS_DIR
        self.bin_dir = BIN_DIR
        self.results_dir = RESULTS_DIR
        self.tmp_dir = TMP_DIR
        self.result_xml = lptxml.get_job_result_file(jobs_xml=jobs_xml, job_node=job_node)
        self.jobs_xml = jobs_xml
        self.job_node = job_node
        self.tool = tool
        self.mainParameters={"parameters":"N/A"}
        
        if tarball[-2:] == "gz":
            self.tar_src_dir = os.path.join(SRC_DIR, tarball[:-7])
        elif tarball[-3:] == "bz2":
            self.tar_src_dir = os.path.join(SRC_DIR, tarball[:-8])
        else:
            self.tar_src_dir = os.path.join(SRC_DIR, tarball[:-4])
        super(BaseTest, self).__init__(self.result_xml)
        #定义可执行文件
        self.processBin = None
        self.processBin2 = None
        #定义result结构，list
        self.result_list = []
        
          
    @method.print_deps_log
    def check_deps(self):
        '''
        检查是否含缺少依赖
        @note: gcc 是必须的
        '''
        utils.has_gcc()
        
        
    def check_bin(self, Binfile, *args):
        '''检查是否存在Binfile
        @return: Boolean
        '''
        lptlog.info("检查测试程序...")
        if args:
            args = list(args)
            args.insert(0, Binfile)
        else:
            args = [Binfile]   
            
        for file in args:
            if file is None:
                return False
            if not os.path.exists(file):
                lptlog.info("未安装  %s " % file)
                return False
            else:
                lptlog.info("已安装 %s " % file )
                continue
        return True
    
    def extract_bar(self):
        '''
        解压tar包到指定路径
        @return: 返回tar源码包详细路径, 如果发生错误返回异常
        '''
        lptlog.info("开始解压测试程序")
        if not os.path.isdir(self.tar_src_dir):
            self.tar_src_dir = utils.extract_tarball_to_dir(self.tarpath, self.src_dir)
        return self.tar_src_dir
    
    @method.print_complier_log 
    def compile(self, configure_status=False, configure_para='', 
                make_status=False, make_para='', 
                make_install_status=False, make_install_para=''):
        '''
        安装源码包，执行configure、make、make install等操作
        @param configure_status:判断是否需要configrue
        @param configure_para:configrue的参数
        @param make_status:判断是否需要make
        @param make_para:make 操作需要的参数
        @param make_install_status: 判断是否需要make install
        '''
                
        if configure_status:
            lptlog.info("源码包进行configure")
            utils.configure(extra=configure_para, configure='./configure')
                
        if make_status:
            lptlog.info("源码包进行make")
            utils.make(extra=make_para, make='make')
                
        if make_install_status:
            lptlog.info("源码包进行make install")
            utils.make(extra='install '+make_install_para, make='make')
            
                             
    def setup(self):
        '''
            安装、调试测试程序
        '''
        pass
    
    
    def check_tool_result_node(self):
        '''检查jobs.xml文件中, 对应job_node中是否包含tool节点
        '''
        tool_node = lptxml.get_tool_node(self.tool, self.jobs_xml, self.job_node)
        if tool_node is None:
            lptlog.critical('测试任务中不包含 %s 测试工具，请核对测试文件' % self.tool)
            raise ValueError()
        else:
            lptlog.debug("检查到 %s 测试任务，开始运行 %s 测试程序" % (self.tool, self.tool))
        return tool_node
            
    def get_config_value(self, tool_node, key, defaultValue, valueType=str):
        '''从parameters.conf文件中读取Value, 如果读取失败，赋予key, defaultValue
        '''
        try:
            getValue = lptxml.get_tool_parameter(tool_node, key)
            lptlog.debug('获取 %s : %s' % (key, getValue))
            if getValue is None:
                getValue = defaultValue
        except Exception:
            lptlog.warning("获取 %s error,将采用默认值: %s" %(key, defaultValue))
            getValue = defaultValue
        finally:
            try:
                getValue = valueType(getValue)
            except Exception:
                raise FormatterError, getValue
            return getValue
            
    def get_config_array(self, tool_node, key, defaultValue):
        '''转换 1，2，4字符类型为list
        '''
        try:
            getList = lptxml.get_tool_parameter(tool_node,  key)
            lptlog.debug('获取 %s :%s' % (key, getList))
            if getList is None:
                getList = defaultValue
            getList = utils.check_int_list(getList)
        except Exception:
            lptlog.warning('获取 %s error,将采用默认值' % key)
            getList = defaultValue
        finally:
            if not isinstance(getList, list):
                raise TypeError, getList
            return getList
       
         
    def get_config_testdir(self, tool_node):
        '''获取IO测试目录
        '''
        testdir = self.get_config_value(tool_node, "testdir", os.path.join(self.tmp_dir, "testdir"), valueType=str)
        if os.path.exists(testdir):
            if not os.path.isdir(testdir):
                lptlog.warning("%s 不是有效目录，将采用 /home/%u/testdir 目录" % testdir)
                testdir = "/home/%s/testdir" % getpass.getuser()
                os.makedirs(testdir, stat.S_IRWXU)
        else:
            os.makedirs(testdir, stat.S_IRWXU)
            testdir = os.path.abspath(testdir)
        lptlog.info("测试目录: %s" % testdir)
        return testdir
        
    def get_config_devices(self, tool_node, testdir):
        '''获取测试设备， 并挂载到testdir
        '''
        devices = self.get_config_value(tool_node, "devices", "Nodevice", valueType=str)
        lptlog.info("测试分区: %s " % devices)
        if not os.path.exists(devices):
            lptlog.debug("%s 不存在" % devices)
            return False
        else:
            try:
                if not os.path.ismount(testdir):
                    utils.system("mount %s %s" % (devices, testdir))
                else:
                    lptlog.debug("%s 已经挂载到 %s 目录" % (devices, testdir))
                    
                return True
            except Exception:
                lptlog.warning("mount %s %s 失败，请确认分区是否已经格式化！！" % (devices, testdir))
                return False
                
    def run(self):
        '''
        @attention:执行测试程序的方法
        '''
        pass
    
    
    def create_result_node_attrib(self, iter, times, parallel, parallels):
        '''
        @param iter: 迭代次数
        @param times: 测试次数
        @param parallel: 测试并行数
        @param parallels: 测试并行数组
        @type parallels: list
        @type iter: str or int
        @type times:int
        @type parallel: int
        '''
        result_node_attrib = {}
        if isinstance(iter, int):
            iter = str(iter)
        parallelstring = ",".join(map(str, parallels))
        keys = ("iter", "times", "parallel", "parallels")
        values = ("%s" %iter, "%d" %times, "%d" %parallel, "%s" % parallelstring)
        for key, value in zip(keys, values):
            result_node_attrib[key] = value
        
        return result_node_attrib
    
      
    def create_result(self):
        '''
        @attention: update self.result_list,结果为
             [   [ {},{}] , [{},{}]  ]
        '''
        pass
    
    def save_results_to_xml(self):
        '''定义保存测试数据到result.xml中
        @param extra_attrbib: 定义result节点中包含的其他属性
        @attention: self.result_list定义了测试数据存储结构
                    [   [ {},{}] , [{},{}]  ]
        '''
        try:
            self.save_result_node(self.tool, self.mainParameters, self.result_list)
            lptlog.info("%s 保存到 %s :PASS" % (self.tool, self.result_xml))
        except Exception:
            #lptlog.exception("%s 保存到 %s :FAIL" % (self.tool, self.result_xml))
            #lptlog.error("%s 保存到 %s :FAIL" % (self.tool, self.result_xml))
            raise SaveXMLError, "%s 保存到 %s :FAIL" % (self.tool, self.result_xml)
           
    def txt_report(self, width=15, writeType='horizontal', tag_width=25, format='txt'):
        '''保存测试数据到xml成功后，生成简单的txt测试报告
        @param width: 定义数据段宽度
        @param writeType: 定义数据写入方向，
            horizontal，很如写入方法，宽度受width影响
            vertical, 纵向写入方法,指标字段宽度受tag_width影响，数据字段宽度受width影响
        ''' 
        JOBID =  lptxml.get_job_attrib_value('id', self.jobs_xml, self.job_node)
        result_txt_file = lptreport.set_result_file(self.results_dir, self.tool, JOBID, format)
        lptlog.info("%s txt测试报告保存于: %s" % (self.tool, result_txt_file))
        #lptreport.save_result(self.tool, result_txt_file, self.result_xml, width=15, writeType=writeType, tag_width=tag_width)
        lptreport.txt_report(self.result_xml, [self.tool], result_txt_file, width=15)
        
    def clean(self):
        '''清理测试环境
        '''
        try:
            if self.tar_src_dir:
                shutil.rmtree(self.tar_src_dir)
                lptlog.info("清理源目录 %s :PASS" % self.tar_src_dir)
            if self.processBin is not None and os.path.exists(self.processBin):
                os.remove(self.processBin)
                lptlog.info("清理Bin文件 %s :PASS" % self.processBin)
            if self.processBin2 is not None and os.path.exists(self.processBin2):
                os.remove(self.processBin2)
                lptlog.info("清理Bin文件 %s :PASS" % self.processBin2)
        except Exception, e:
            lptlog.warning('清理临时目录或文件：FAIL')
            lptlog.debug(e)
            #raise CleanError, e
        finally:
           os.chdir(self.lpt_root)
    
