# -*- coding:utf-8 -*-

import os
import time
from . import lptxml
from . share import utils
from . import lptlog
from . import lptxls
from . error import  *
import xlwt
import string
from lpt.lib import readconfig
from lpt.lib import chart
from pychart import tick_mark
from multiprocessing import Process
from signal import SIGTERM 
from lpt.lib import sysinfo
from lpt.lib import lmbench


from .share import base_xls
import xlwt
from lpt.lib.share import utils

try:
    from PIL import Image
except  Exception:
    lptlog.warning("缺少PIL模块，可能导致生成图片Error!")


lptdir = os.getenv("LPTROOT")
VERSION_FILE = os.path.join(lptdir, "release")
DOCS_FILE = os.path.join(lptdir, "config/docs.conf")
lpttmpdir = os.path.join(lptdir, "tmp")
tmpdir = os.path.join("/tmp/lpts")
if not os.path.exists(tmpdir):
    os.makedirs(tmpdir)
    
TITLE = '''
   ###############################################################
                 --%s Performance Testing--                                                                                 
   --author:     Scemoon                                           
   --contact:    mengsan8325150@gmail.com                          
   --version:    %s                                      
   ###############################################################
    ''' 
    
INDEX_KEYS = {'unixbench':['Dhrystone2-using-register-variables',
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
                    'System-Benchmarks-Index-Score'],
        'x11perf':['aa-polygon',
                        'ellipses',
                        'images-and-blits',
                        'rectangles',
                        'text',
                        'windows'
                        #'Graphics-Benchmarks-Index-Score'
                            ],
        'glxgears':['gears'],
        'stream':['Copy', 'Add', 'Triad', 'Scale'],
        'pingpong':["initialised", "completed", "total"],
        'iozone':['write', 'rewrite', 'read', 'reread', 'randread', 'randwrite'],
        'bonnie':["putc","putc_cpu","put_block","put_block_cpu","rewrite","rewrite_cpu",
                "getc","getc_cpu","get_block","get_block_cpu","seeks","seeks_cpu","seq_create",
                "seq_create_cpu","seq_stat","seq_stat_cpu","seq_del","seq_del_cpu","ran_create","ran_create_cpu",
                "ran_stat","ran_stat_cpu","ran_del","ran_del_cpu" ],
        'dbench_fio':['Throughtput', 'max_latency'],
        'lmbench':lmbench.get_index_list()
        
        }

#parameters_keys = ["parameters", "parallels", "times"]
parameters_keys = ["parameters"]

class CFork:
    ''' create fork'''
    
    @classmethod
    def __create_process(cls):
        try:
            forkPID = os.fork()
            if forkPID >0:
                return 1
            else:
                return 0
        except OSError:
            lptlog.warning("create process Error")
            return 2
        
    @classmethod
    def _create_chprocess(cls):
        '''return chidl process pid'''
        
        forkStatus = cls.__create_process()       
        if forkStatus == 1:
             #os.setsid() 
             #os.umask(0)
             cforkStatus = cls.__create_process()
             if cforkStatus == 0:
                 return os.getpid()
             else:
                 return None
        elif forkStatus==0:
            return os.getpid()
        else:
            return None
             
    
    @classmethod
    def _kill_chiprocess(cls, pid):
        if pid:
            pass
        else:
            lptlog.warning("Pid Type Error")
            return 1
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
                lptlog.info("Now, Kill Pid %s: PASS" % pid)
        except OSError as err:
            lptlog.error("Kill pid %s :Error" % pid)
            
    @classmethod
    def run(cls, func, *args, **kwargs):
        pid = cls._create_chprocess()
        func(*args, **kwargs)
        cls._kill_chiprocess(pid)
        
    
tick_mark_list = [tick_mark.star, tick_mark.plus, tick_mark.dia, tick_mark.tri, tick_mark.dtri, 
             tick_mark.circle1, tick_mark.blacksquare, tick_mark.blackdia, tick_mark.blackdtri,
              tick_mark.gray70square, tick_mark.gray70dia, tick_mark.gray70dtri]

def get_config_value(key, tool, config=DOCS_FILE):
        return readconfig.get_conf_instance(config).get_str_value(tool, key)
    
class InfoReport(lptxml.XmlResults):
    '''report OS informance '''
    def __init__(self, xml):
         super(InfoReport, self).__init__(xml)
    
    def get_OSinfo_dict(self):
        return self.get_node_attrib_dict(self.root)
    
        
class Report(lptxml.XmlResults):
    '''get results.xml info ''' 
    def __init__(self, xml, tool):
        super(Report, self).__init__(xml)
        self.tool = tool
        self.tool_indexs = INDEX_KEYS[self.tool]
        
    def get_nodes(self):
        return self.search_tool_result_nodes(self.tool)
    
    def get_parallel_nodes(self, parallel):
        return self.search_tool_result_parallel_nodes(self.tool, parallel)
    
    def get_parallels(self):
        '''get parallels 
        @return: list'''
        
        parallelstring = self.get_tool_result_parallels(self.tool, key='parallels')
        return utils.check_int_list(parallelstring)
    
    def get_parameters(self):
        parameterstring = self.get_tool_result_parallels(self.tool, key='parameters')
        parallelstring = self.get_tool_result_parallels(self.tool, key='parallels')
        times = self.get_tool_result_parallels(self.tool, key='times')
        return {"parameters":parameterstring, "parallels":parallelstring, "times":times}
    
    def check_tool_nodes(self):
        if not self.search_tool_result_nodes(self.tool):
            return False
        else:
            return True
        
    def get_parallel_nodes(self, parallel):
        '''获取某并行时，测试数据'''
        return self.search_tool_result_parallel_nodes(self.tool, parallel)
    
    def get_hor_data_title(self):
        return self.tool_indexs
    
    def get_times(self, node):
        return  self.get_result_attrib(node, "iter")
        
    def get_parallel_hor_data(self, node):
        ''' @return: dict'''
        parallel_dict = {}
        for index in self.tool_indexs:
            parallel_dict[index] = self.get_result_text(node, index)
            
        return parallel_dict
    
    def get_ver_data_title(self, nodes):
        return [ self.get_times(node) for node in nodes ] 
    
    def get_ver_data(self, index, parallel, nodes):
        iter_dict = {}
        for iter in self.get_ver_data_title(nodes):
            iter_dict[iter] = self.search_element_by_tagAndtimes(self.tool, index, parallel, iter)[0]
            
        return iter_dict
           
    #def get_config_value(self, key):
     #   return readconfig.get_conf_instance(DOCS_FILE).get_str_value(self.tool, key)
    
    def get_parallel_data(self, parallel):
        average_nodes = self.search_nodes_by_parallelAndtimes(self.tool, parallel, "Average")
        if average_nodes:
            parallel_result_list = []
            for key in self.tool_indexs:
                parallel_result_list.append(self.get_result_text(average_nodes[0]), key)
        else:
            raise ValueError("平均值为空")
        return parallel_result_list
    
    
    def get_index_data(self, index):
        '''@param:
            @return: list: '''
    
        index_result_list = []
        for parallel in self.get_parallels():
            values = self.search_element_by_tagAndtimes(self.tool, index, parallel, "Average")
            if not values:
                lptlog.warning("获取times='Average', index=%s, parallel=%s 的值为空，赋值0")
                value = 0
            else:
                value = float(values[0])
                lptlog.debug('匹配times="Average", index=%s , parallel=%s 的results value:%s' % (index, parallel, value))
            index_result_list.append(value)
        return index_result_list

    def get_lmbench_attrib(self, node, key):
        return self.get_result_attrib(node, key)

class TxtReport(Report):
    '''  create txt report'''      
    def __init__(self, xml_file, tool, txt_file, width, tag_width, writeType):  
        super(TxtReport, self).__init__(xml_file, tool)
        self.fp = open(txt_file, 'w')
        self.width = width
        self.tag_width = tag_width
        self.writeType = writeType
                
    def file_close(self):
        self.fp.flush()
        self.fp.close()

    def write(self, text, width=10, position='left', fillchar=' '):
        if isinstance(text,bytes):
            text_bak = str(text,'utf-8')
        if isinstance(text,str):
            text_bak = text
        fill = bytes(' ','utf-8')
        newtext = utils.strwidth(text_bak, width, position, fillchar)
        self.fp.write(newtext)
        
    def set_title(self):
        self.fp.write('\n')   
        #self.write(self.TXT_TITLE % tool, width=100, position='center')
        self.fp.writelines(TITLE % (self.tool, utils.get_version(VERSION_FILE)))
        self.fp.write("\n")
        
    
    def _set_section_title(self, seq, title, width=30):
        self.fp.write('\n') 
        self.fp.write('\n') 
        self.fp.write("  %s. %s" % (seq, title))
        self.fp.write("\n  ========\n")
        
    def _write_text(self, text, width):
        u_text = utils.to_unicode(text)
        n = 0
        while True:
            if len(u_text[n:]) > width:
                if n == 0:
                    end = n + width - 1
                else:
                    end = n + width
                self.write(utils.from_unicode(u_text[n:(n+width-1)]), width=width, position="left")
                self.fp.write("\n")
                n = + end
                continue
            else:
                self.write(utils.from_unicode(u_text[n:]), width=width, position="left")
                self.fp.write("\n")
                break

    
    def set_tool_description(self, width=50):
        '''这里的width指unicode宽度'''
        text = get_config_value("descriptions", self.tool)
        self._set_section_title("一", "概述" )
        self.fp.write("  ")
        self._write_text(text, width)
    
    def set_tool_index(self, width=50):
        self._set_section_title("二", "指标" )
        for index in self.tool_indexs:
            text = "  %s: %s" %(index, get_config_value(index, self.tool))
            self._write_text(text, width)
            #self.fp.write("\n")
            
    def set_result_title(self, section="三"):
        
        self._set_section_title(section, "测试数据")
        
    def write_element_text(self, node, width):
        '''定义写element内容的方法,写入所有node节点中所有element的text
        '''
        self.fp.write("\n")
        self.fp.write("  ")
        #iter = node.get('iter')
        iter = self.get_times(node)
        self.write(iter, width=width)
        parallel_result_dict = self.get_parallel_hor_data(node)
        for index in self.tool_indexs:
            self.write(parallel_result_dict[index], width)
        
    def write_element_tag(self, width):
        '''定义写element标签的方法, 写入node节点中所有element的标签
        '''
        self.fp.write("\n")
        self.fp.write("  ")
        self.write('Times', width=width)
        #for element in node:
            #self.write(element.tag, width=width)
        for index in self.get_hor_data_title():
            self.write(index, width=width)
        self.fp.write("\n")
        self.fp.write("  ")
        self.write("-", width=width*(len(self.tool_indexs)+1), fillchar='-' )
        
            
    def write_nodes(self, nodes, width):
        '''
        '''
        self.write_element_tag(width)
        for node in nodes:
            self.write_element_text(node, width)
        self.fp.write("\n")
        self.fp.write("  ")
        self.write("-", width=width*(len(self.tool_indexs)+1), fillchar='-' )
        
    def write_horizontal_results(self):
      
        parallels = self.get_parallels()
        lptlog.debug("并行列表:%s" % utils.list_to_str(parallels))
        for parallel in parallels:
            #result_parallel_nodes 并行数为parallel的节点列表
            #result_parallel_nodes = self.search_tool_result_parallel_nodes(tool, parallel)
            result_parallel_nodes = self.get_parallel_nodes(parallel)
            if result_parallel_nodes is None:
                lptlog.warning("%s 测试工具的 %s 并行测试数据为Null" %(tool, parallel))
                continue
            self.fp.write("\n")
            self.fp.write("\n")
            self.fp.write("** %s 并行测试数据：" % parallel)
            self.fp.write("\n   ==============\n")
            lptlog.info("将写入并行数为 %s 的数据" % parallel)
                
            self.write_nodes(result_parallel_nodes, self.width) 
        self.fp.write("\n")  
      
    def _write_lmbench(self, keys, nodes):
        for node in nodes:
            self.fp.write("%8s" % self.get_times(node))
            node_results_dic = self.get_parallel_hor_data(node)
            for key in keys:
                self.write(node_results_dic.get(key), width=8, position="right")
            self.fp.write("\n")
            
    def write_lmbench(self):
        self.set_result_title(section="二")
        parallels = self.get_parallels()
        parallel = parallels[0]
        lptlog.debug("lmbench 并行数为: %s " % parallel)
        
        result_parallel_nodes = self.get_parallel_nodes(parallel)
        if result_parallel_nodes is None:
            lptlog.warning("%s 测试工具的 %s 并行测试数据为Null" %(tool, parallel))
            raise TestException("%s 测试工具的 %s 并行测试数据为Null" %(tool, parallel))
        
        self.fp.write("\n")
        self.fp.write("\n")
        self.fp.write('''Basic system parameters
----------------------------------------
     Mhz     tlb   cache     mem    scal
           pages    line     par    load
                   bytes  
----------------------------------------''')
        self.fp.write("\n")
        self.write(self.get_lmbench_attrib(result_parallel_nodes[0], "Mhz"), width=8, position="right")
        self.write(self.get_lmbench_attrib(result_parallel_nodes[0], "tlb"), width=8, position="right")
        self.write(self.get_lmbench_attrib(result_parallel_nodes[0], "line_size"), width=8, position="right")
        self.write(self.get_lmbench_attrib(result_parallel_nodes[0], "mem_load_par"), width=8, position="right")
        self.write(self.get_lmbench_attrib(result_parallel_nodes[0], "scal_load"), width=8, position="right")
        
        self.fp.write("\n\n")
        self.fp.write('''Processor, Processes - times in microseconds - smaller is better
----------------------------------------------------------------------------------------
   Times    null    null    open            slct     sig     sig    fork    exec      sh
            call     I/O    clos    stat     TCP    inst    hndl    proc    proc    proc
--------- ------------- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- --------------''') 
        self.fp.write("\n")
        self._write_lmbench(lmbench.lm_process, result_parallel_nodes)
        
        self.fp.write("\n\n")
        self.fp.write('''Basic integer operations - times in nanoseconds - smaller is better
-------------------------------------------------------------------
   Times   intgr   intgr   intgr   intgr   intgr
             bit    add      mul     div     mod
--------- ------------- ------ ------ ------ ----''')
        
        self.fp.write("\n")
        self._write_lmbench(lmbench.lm_int, result_parallel_nodes)
        
        self.fp.write("\n\n")
        self.fp.write('''Basic uint64 operations - times in nanoseconds - smaller is better
------------------------------------------------------------------
   Times   int64   int64   int64   int64   int64
             bit     add     mul     div     mod
--------- ------------- ------ ------ ------ ---''')
        self.fp.write("\n")
        self._write_lmbench(lmbench.lm_int64, result_parallel_nodes)
        
        self.fp.write("\n\n")
        self.fp.write('''Basic float operations - times in nanoseconds - smaller is better
-----------------------------------------------------------------
   Times   float   float   float   float
             add     mul     div    bogo
--------- ------------- ------ ------ ---''')
        self.fp.write("\n")
        self._write_lmbench(lmbench.lm_float, result_parallel_nodes)
        
        self.fp.write("\n\n")
        self.fp.write('''Basic double operations - times in nanoseconds - smaller is better
------------------------------------------------------------------
   Times  double  double  double  double
             add     mul     div    bogo
--------- ------------- ------  -------- ''')
        self.fp.write("\n")
        self._write_lmbench(lmbench.lm_double, result_parallel_nodes)
        
        self.fp.write("\n\n")
        self.fp.write('''Context switching - times in microseconds - smaller is better
------------------------------------------------------------------
   Times   2p/0K  2p/16K  2p/64K  8p/16K  8p/64K 16p/16K 16p/64K
           ctxsw   ctxsw   ctxsw   ctxsw   ctxsw   ctxsw   ctxsw
--------- ------------- ------ ------ ------ ------ ------ -------''')
        self.fp.write("\n")
        self._write_lmbench(lmbench.lm_ctx, result_parallel_nodes)
        
        self.fp.write("\n\n")
        self.fp.write('''*Local* Communication latencies in microseconds - smaller is better
-------------------------------------------------------------------------
   Times   2p/0K    Pipe      AF     UDP    RPC/     TCP    RPC/     TCP
           ctxsw            UNIX             UDP             TCP    conn
--------- ------------- ----- ----- ---- ----- ----- ----- ----- --------''')
        self.fp.write("\n")
        self._write_lmbench(lmbench.lm_ipc_local, result_parallel_nodes)
        
        self.fp.write("\n\n")
        self.fp.write('''File & VM system latencies in microseconds - smaller is better
------------------------------------------------------------------------
   Times      0K File        10K File       Mmap    Prot    Page   100fd
          Create  Delete  Create  Delete Latency   Fault   Fault   selct
--------- ------------- ------ ------ ------ ------ ------- ----- ------''')
        self.fp.write("\n")
        self._write_lmbench(lmbench.lm_file_vm, result_parallel_nodes)
        
        self.fp.write("\n\n")
        self.fp.write('''*Local* Communication bandwidths in MB/s - bigger is better
-------------------------------------------------------------------------------
   Times    Pipe      AF     TCP    File    Mmap   Bcopy   Bcopy     Mem     Mem
                    UNIX          reread  reread  (libc)  (hand)    read   write
--------- ------------- ---- ---- ---- ------ ------ ------ ------ ---- -------''')
        self.fp.write("\n")
        self._write_lmbench(lmbench.lm_bw_ipc_local, result_parallel_nodes)
        
        self.fp.write("\n\n")
        self.fp.write('''Memory latencies in nanoseconds - smaller is better
    (WARNING - may not be correct, check graphs)
---------------------------------------------------
    Times   L1 \$   L2 \$    Main    Rand 
                              mem     mem
--   ----   ----    --------    ---------''')
        self.fp.write("\n")
        self._write_lmbench(lmbench.lm_mem, result_parallel_nodes)
        
        self.fp.write("\n\n")
        
    def write_vertical_results(self):
        #判断tool result是否存在
        parallels = self.get_parallels()
        lptlog.debug("并行列表:%s" % utils.list_to_str(parallels))
        for parallel in parallels:
            #result_parallel_nodes 并行数为parallel的节点列表
            #result_parallel_nodes = self.search_tool_result_parallel_nodes(tool, parallel)
            result_parallel_nodes = self.get_parallel_nodes(parallel)
            if result_parallel_nodes is None:
                lptlog.warning("%s 测试工具的 %s 并行测试数据为Null" %(tool, parallel))
                continue
            self.fp.write("\n")
            self.fp.write("\n")
            self.fp.write("** %s并行测试数据：" % parallel)
            self.fp.write("\n   ==============\n")
            lptlog.info("将写入并行数为 %s 的数据" % parallel)
            
            #获取迭代值，返回list
            #times_list = []
            #for node in result_parallel_nodes:
               # times_list.append(self.get_result_attrib(node, "iter"))
            times_list = [ self.get_times(node) for node in result_parallel_nodes ]
                
            #获取指标名称
            #elements_tag_list = self.get_tool_element_tag(result_parallel_nodes[0])
            elements_tag_list = self.tool_indexs
            
            #首先写入row标题
            self.fp.write("\n")
            self.fp.write("  ")
            self.write("TESTS", self.tag_width)
            for iter in times_list:
                self.write(iter, self.width)
                
            #写入row标题和data的分隔符
            self.fp.write("\n") 
            self.fp.write("  ")
            self.write("-", width=self.width*(len(times_list))+self.tag_width, fillchar='-' )
            
            #开始写入数据
            for element_tag in elements_tag_list:
                self.fp.write("\n")
                self.fp.write("  ")
                self.write(element_tag, self.tag_width)
                for iter in times_list:
                    element_text = self.search_element_by_tagAndtimes(self.tool, element_tag, parallel, iter)[0]
                    self.write(element_text, self.width)
                    
            self.fp.write("\n")
            self.fp.write("  ")
            self.write("-", width=self.width*(len(times_list))+self.tag_width, fillchar='-' )
            self.fp.write("\n")
            self.fp.write("\n")
            
        
    def report(self):
        lptlog.debug("检查是否包含 %s result" % self.tool)
        if not self.check_tool_nodes():
            raise ValueError(" %s 测试数据为空..." % self.tool)
        #nodes = self.get_nodes()
        self.set_title()
        self.set_tool_description()
        if self.tool == "lmbench":
            self.write_lmbench()
            return 0
      
        self.set_tool_index()
        self.set_result_title()
        lptlog.debug("数据写入方式： %s" % self.writeType)
        if self.writeType == "horizontal":
            self.write_horizontal_results()
        elif self.writeType == "vertical":
            self.write_vertical_results()
            
                
                
def txt_report(xml, tools_list, reportfile, width=15):
    ''' create txt report'''
    for tool in tools_list:
        #创建txt测试报告
        lptlog.info("开始创建 %s 的 txt测试报告"  % tool)
        if len(tools_list) > 1:
            txt_report_file = reportfile.split(".txt")[0]+"_%s.txt" % tool
        else:
            txt_report_file = reportfile
            
        try:
            #txtops = XmlToTxt(result_xml, txt_report_file)
            
            if tool in ("unixbench", "x11perf", "bonnie"):
                writeType = "vertical"
                tag_width =40
            else:
                writeType = "horizontal"
                tag_width = 15
                
            txtops = TxtReport(xml, tool, txt_report_file, width, tag_width, writeType)  
            txtops.report()
            lptlog.info("""
                 --------------------------------------------------------------
                    创建 %s 的  txt测试报告：PASS
                 --------------------------------------------------------------
            """ % tool)
        except Exception as e:
            lptlog.exception("创建 %s 的  txt测试报告：FAIL" % tool)
            lptlog.error("""
                 --------------------------------------------------------------
                    创建 %s 的  txt测试报告：FAIL
                 --------------------------------------------------------------
            """ % tool)
            lptlog.debug(e)
            continue
                
class InfoXlsReport(InfoReport):
    '''report OS infor, format xls'''
    def __init__(self, xls_object):
        #super(InfoXlsReport, self).__init__(xml)
        self.xls_write = xls_object
        self.sheet = self.xls_write.sheet("OSInfo")               
    
    def write_keys(self, row=3, col=2):
        for key in sysinfo.OSInfo.type_keys:
            self.xls_write.write_cell(self.sheet, key, row, 1)
            #row += 1
            for subkey in sysinfo.OSInfo.info_keys[key]:
                 #self.xls_write.data_title(self.sheet, [subkey], row, col_start_index=col)
                 self.xls_write.data_seq(self.sheet, subkey, row, col)
                 row += 1 
            #row += 1
            
    def _set_text_format(self, value, row, col):
        u_text = utils.to_unicode(value)

        colswidth = self.sheet.col(col).width 
        rowdefaultheight = self.sheet.row_default_height
        rowheight = self.sheet.row(row).height
        if len("    "+u_text) * 297< colswidth:
            pass
        else:
            rate = len("    "+u_text) * 300 / colswidth + 1
            if rowheight < rowdefaultheight * rate:
                self.sheet.row(row).height = rowdefaultheight * rate
    
    def write_values(self, xml, name, col, row=2):
        class XmlInfo(InfoReport):
            def __init__(self, xml):
                super(XmlInfo, self).__init__(xml)
                         
        osinfo_dict = XmlInfo(xml).get_OSinfo_dict()
          
        self.xls_write.data_title(self.sheet, [name], row, col_start_index=col)
        row += 1
        for key in sysinfo.OSInfo.type_keys:
            #row += 1
            for subkey in sysinfo.OSInfo.info_keys[key]:
                self.xls_write.info(self.sheet, osinfo_dict.get(subkey, "N/A"), row, col)
                self._set_text_format(osinfo_dict.get(subkey, "N/A"), row, col)
                self.sheet.row(row).height_mismatch=True
                row += 1
            #row += 1
        
class XlsReport(Report):
    '''create xls report'''
    def __init__(self, xml, tool, xls_object, writeType="horizontal", chart=False):
        '''@parameter xls_object: xls write object, lptxls.Wxls()'''
        super(XlsReport, self).__init__(xml, tool)
        self.xls_write = xls_object
        self.sheet = xls_object.sheet(tool)
        self.writeType = writeType
        self.chart = chart
        
    def write_title(self, row_width=3, col_width=4):
        title = "---%s Performance Results---"  % self.tool
        self.xls_write.title(self.sheet, title, rowmin=1, rowmax=1+row_width, colmin=1, colmax=col_width)
        return row_width + 1 + 1
    
    def _set_text_format(self, key, row, colmin, colmax):
        text = get_config_value(key, self.tool)
        u_text = utils.to_unicode(text)
        #sum of  from col 1 to col 5
        colswidth = sum([ self.sheet.col(col).width for col in range(colmin, colmax)])
        rowheight = self.sheet.row_default_height 
        if len("    "+u_text) * 430 < colswidth:
            pass
        else:
            rate = len("    "+u_text) * 430 / colswidth + 1
            self.sheet.row(row).height = rowheight * rate
            
    def write_tool_descriptions(self, row, colmin=1, colmax=5):
        self.xls_write.section_title(self.sheet, "一.  概述", row)
        self.xls_write.description(self.sheet, "    %s" % get_config_value("descriptions", self.tool), row+1, colmin=colmin, colmax=colmax)
        #self._set_text_format("descriptions", row+1, colmin, colmax)
        return row+2
    
     
    def write_tool_index(self, row, colmin=1, colmax=5, section="二"):
        self.xls_write.section_title(self.sheet, "%s.  指标" % section, row)
        row = row + 1
        for index in self.tool_indexs:
            self.xls_write.description(self.sheet, "    %s: %s" % (index, get_config_value(index, self.tool)), row, colmin=colmin, colmax=colmax)
            #self._set_text_format(index, row, colmin, colmax)
            row = row + 1
        return row
    
    def write_parameters(self, row, colmin, colwidth, section="三"):
        self.xls_write.section_title(self.sheet, "%s.  参数" % section, row)
        row = row + 1
        self.xls_write.write_cell(self.sheet, "Main Parameters", row, col=colmin)
        row += 1
        for key in parameters_keys:
            self.xls_write.data_seq(self.sheet, key, row, col=colmin)
            self.xls_write.parameters(self.sheet, self.get_parameters()[key], row, colmin+1, colmin+colwidth)
            row = row + 1
        return row
        
    def write_result_title(self, row, section="四"):
        self.xls_write.section_title(self.sheet, "%s.  结果"  % section, row)
        return row + 1

        
    def write_hor_data_title(self, row):
        self.xls_write.data_title(self.sheet, ["TIMES"], row)
        data_title_list = self.get_hor_data_title()
        self.xls_write.data_title(self.sheet, data_title_list, row, col_start_index=2)
        #for  data_title in data_title_list:
            # if len(utils.to_unicode(data_title)) * 367 < self.sheet.col(2+data_title_list.index(data_title)).width:
             #    pass
             #else:
              #   self.sheet.col(2+data_title_list.index(data_title)).width = len(utils.to_unicode(data_title)) * 265
        return row + 1
        
    def write_parallel_data_des(self, parallel, row):
        self.xls_write.write_cell(self.sheet, "%s Parallel Data" % parallel, row, 1)
        return row + 1

    def write_parallel_hor_data(self, nodes, row):
        style = xlwt.XFStyle()
        style.font = base_xls.font(bold=True, colour=0x08)
        style.alignment = base_xls.alignment()
        style.borders = base_xls.borders(line=0x01)
        style.pattern = base_xls.pattern(solid_pattern=0x01, fore_colour=0x2A)
        for node in nodes:
            self.xls_write.data_seq_bak(self.sheet, self.get_times(node), row, style)
            node_dict = self.get_parallel_hor_data(node)
            self.xls_write.data(self.sheet, list(map(float, [node_dict.get(index) for index in self.tool_indexs])), row, col_start_index=2)
            row = row + 1
            
        return row
    
    def write_ver_data_title(self, row, nodes):
         self.xls_write.data_title(self.sheet, ["TESTS"], row)
         data_title_list =  self.get_ver_data_title(nodes)
         self.xls_write.data_title(self.sheet, data_title_list, row, col_start_index=2 )
         return row + 1
    
    def write_ver_data(self, row, parallel, nodes):
        for index in self.tool_indexs:
            self.xls_write.data_seq(self.sheet, index, row)
            #if len(utils.to_unicode(index)) * 367 < self.sheet.col(1).width:
            #    pass
            #else:
             #   self.sheet.col(1).width = len(utils.to_unicode(index)) * 367
            iter_dict = self.get_ver_data(index, parallel, nodes)
            self.xls_write.data(self.sheet, list(map(float, [ iter_dict.get(iter) for iter in self.get_ver_data_title(nodes)])), row, col_start_index=2)
            row = row + 1
        return row
    
    def _colswidth(self, writeType):
        if self.writeType == "horizontal":
            colwidth = len(self.get_hor_data_title())
        elif self.writeType == "vertical":
            colwidth = len(self.get_ver_data_title(self.get_nodes())) / len(self.get_parallels())
            
        return colwidth
    
    def _tran_png_to_bmp(self, pngfile):
        bmpfile = pngfile.split('.')[0]+".bmp"
        Image.open(pngfile).convert("RGB").save(bmpfile)
        return bmpfile

    def _gen_index_graphic(self, index, graphic_name, title):
        Y_max = max(self.get_index_data(index))
        parallel_results_list = [self.get_parallels(), self.get_index_data(index)]
        graphic = chart.Draw(list(map(list, list(zip(*parallel_results_list)))), graphic_name, title)
        xais = graphic.set_X("parallels")
        yais = graphic.set_Y("Results", tic_interval=Y_max/5)
        ar = graphic.creat_area((300, 100), xais, yais)
        plot = graphic.creat_bar_plot(index)
        graphic.area_add_plot(ar, [plot])
        graphic.draws(ar)
        
    def gen_index_graphic(self, graphic_name="lpt"):
        for index in self.tool_indexs:
            index_name = graphic_name
            index_name = os.path.join(tmpdir,"%s_%s_%s" % (index_name, self.tool, index))
            try:
                self._gen_index_graphic(index, index_name, index)
            except Exception as e:
                lptlog.error("gen graphic error: %s" % e)
                lptlog.exception("")

    
    def _write_index_img(self, index, row, col, graphic_name="lpt"):
        graphic_name = os.path.join(tmpdir,"%s_%s_%s" % (graphic_name, self.tool, index))
        pngfile = graphic_name+".ps"
        if os.path.exists(pngfile):
            bmpfile = self._tran_png_to_bmp(pngfile)
            self.xls_write.insert_img(self.sheet, bmpfile, row, col)
            row = row + 9
        else:
            lptlog.error("No Found %s" % pngfile)
        return row + 1

    def write_indexs_img(self, row, col):
        self.xls_write.section_title(self.sheet, "五.  图例",  row)
        row = row + 1
        for index in self.tool_indexs:
            self.xls_write.write_cell(self.sheet,  index, row, col)
            row = row + 1
            row  = self._write_index_img(index, row, col)
                        
        return row + 1
    
    def hor_report(self, row):
        '''横向写入方法'''
        parallels = self.get_parallels()
        lptlog.debug("获取 %s 测试并行数: %s" % (self.tool, utils.list_to_str(parallels)))
        for parallel in parallels:
            parallel_nodes = parallel_nodes = self.get_parallel_nodes(parallel)
            row = self.write_parallel_data_des(parallel, row)
            row = self.write_hor_data_title(row)
            lptlog.debug("写入 指标名称 PASS")
            #空一行
            #row = row + 1
            row = self.write_parallel_hor_data(parallel_nodes, row)
            lptlog.debug("写入 %d 并行 测试数据:PASS" % parallel)
            #空二行
            row = row + 1
            
        return row
    
    def ver_report(self, row):
        parallels = self.get_parallels()
        lptlog.debug("获取 %s 测试并行数: %s" % (self.tool, utils.list_to_str(parallels)))
        for parallel in parallels:
            parallel_nodes = self.get_parallel_nodes(parallel)
            row = self.write_parallel_data_des(parallel, row)
            row = self.write_ver_data_title(row, parallel_nodes)
            row = self.write_ver_data(row, parallel, parallel_nodes)
            row = row + 1
            
        return row
    
    def _get_lmbench_result_nodes(self):
        parallels = self.get_parallels()
        parallel = parallels[0]
        lptlog.debug("lmbench 并行数为: %s " % parallel)
        nodes = self.get_parallel_nodes(parallel)
        return nodes
                
    def lmbench_report(self):
        colwidth=5
        row = self.write_title(col_width=colwidth+1)
        row_des = row + 1
        row = self.write_tool_descriptions(row_des, colmin=1, colmax=colwidth+1)
        row = row +1
        row = self.write_parameters(row, 1, colwidth, section="二")
        row = row + 1
        row = self.write_result_title(row, section="三")
        #row = row + 1
        for lm_des in lmbench.des[1:]:
            #get group data ,type list
                #获取tiltle_keys切片，并获取该切片位置的 group tilte,然后转换成list
            data_title_list = list(lmbench.title_keys[lmbench.des.index(lm_des)])
            title_len = len(data_title_list)
            self.xls_write.lmbench_des(self.sheet, lm_des, row, 1, 1+title_len)
            row +=1
            self.xls_write.data_title(self.sheet, ["TIMES"], row)
            self.xls_write.data_title(self.sheet, data_title_list, row, col_start_index=2)
            row += 1
            nodes = self._get_lmbench_result_nodes()
            for node in nodes:
                self.xls_write.data_seq(self.sheet, self.get_times(node), row)
                node_dict = self.get_parallel_hor_data(node)
                keys = list(lmbench.lm_keys[lmbench.des.index(lm_des)])
                self.xls_write.data(self.sheet, list(map(float,[node_dict.get(key) for key in keys] )), row, col_start_index=2)
                row = row + 1
            row += 1
            #调整格式
        self.sheet.col(1).width = 4000
        for col in range(2, 12):
            self.sheet.col(col).width = 3600
        self._set_text_format("descriptions", row_des+1, colmin=1, colmax=1+colwidth+1)
            
    def report(self):
        lptlog.debug("检查是否包含 %s result" % self.tool)
        if not self.check_tool_nodes():
            raise ValueError(" %s 测试数据为空...")
        #nodes = self.get_nodes()
        if self.tool == "lmbench":
            self.lmbench_report()
            return
        lptlog.info("数据写入方式： %s" % self.writeType)
        lptlog.debug("写入标题")
        colwidth = int(self._colswidth(self.writeType))
        row = self.write_title(col_width=colwidth+1)
        row_des = row + 1
        row = self.write_tool_descriptions(row_des, colmin=1, colmax=1+colwidth)
        row_index_start = row + 1
        row = self.write_tool_index(row_index_start, colmin=1, colmax=1+colwidth)
        row = row + 1
        row = self.write_parameters(row, 1, colwidth)
        row += 1
        row = self.write_result_title(row)
       
        if self.writeType == "horizontal":
            row = self.hor_report(row)
                          
        elif self.writeType == "vertical":
            row = self.ver_report(row)
            
        if colwidth <=4:
            for col in range(2, colwidth+1+1):
                self.sheet.col(col).width = 16000/colwidth
            
        if self.chart and len(self.get_parallels())>1:
            lptlog.info("生成图片报告")
            self.gen_index_graphic()
            self.write_indexs_img(row, 1)
      
        #调整格式
        self._set_text_format("descriptions", row_des+1, colmin=1, colmax=1+colwidth+1)
        for index in self.tool_indexs:
            self._set_text_format(index, row_index_start+self.tool_indexs.index(index)+1, colmin=1, colmax=1+colwidth+1)
         
    
def xls_report(xml, tools, reportfile, writeType="horizontal", chart=False):
    '''定义xls report 流程'''
    #初始化xls实例
    Wxls_object = lptxls.Wxls()
   
        #写入system info
    lptlog.info("写入system environment") 
    infoxls = InfoXlsReport(Wxls_object)
    infoxls.write_keys()
    infoxls.write_values(xml, "Opreating System Environment", 3) 
                    
    for tool in tools:
        lptlog.info("开始创建 %s xls测试报告"  % tool)
        if tool in ("unixbench", "x11perf", "glxgears", "bonnie"):
            writeType="vertical"
        else:
            writeType = "horizontal"                
             #创建xls测试报告
        
        try:
            lptlog.info("开始写入 %s 测试数据到 xls测试报告 " % tool)
            xlsreport = XlsReport(xml, tool, Wxls_object, writeType, chart=chart)
            xlsreport.report()
            lptlog.info("""
                 --------------------------------------------------------------
                    创建 %s 的  xls测试报告：PASS
                 --------------------------------------------------------------
            """ % tool)
        except Exception as e:
            lptlog.error("""
                 --------------------------------------------------------------
                    创建 %s 的  xls测试报告：FAIL
                 --------------------------------------------------------------
            """ % tool)
            lptlog.debug(e)
            lptlog.exception("%s 测试数据写入 %s Error" %(tool, reportfile))
            continue
        
        lptlog.debug("保存测试报告")
        Wxls_object.save(reportfile)
           

    
def set_result_file(results_dir, tool, id, type):
    '''
    在results_dir中保存report
    '''
    tool_dir = os.path.join(results_dir, tool)
    if not  os.path.isdir(tool_dir):
        os.makedirs(tool_dir)
        
    result_file = "%s-%s.%s" % (tool, id, type)
    result_abs_file = os.path.join(tool_dir, result_file)
    return result_abs_file


           
def save_result(tool, result_file, xml_file, width=15, writeType='horizontal', tag_width=25, format='txt'): 
    '''默认保存的report 格式：txt
    @attention: 暂时只支持该格式，其他格式如xls等，需要手动生成
    '''
   
    if tool in ("unixbench", "x11perf"):
        writeType="vertical"
        tag_width=40
        
    try:
        #txtops = XmlToTxt(xml_file, result_file)
        #txtops.simple_report(tool, width, writeType, tag_width)
        txtops = TxtReport()
        lptlog.info("创建 %s 的 %s 测试报告：PASS" %(tool, format))
        lptlog.info("%s txt测试报告保存于: %s" % (tool, result_file))
    except Exception as e:
        #lptlog.exception("创建 %s 的 %s 测试报告：FAIL" %(tool, format))
        lptlog.error("创建 %s 的 %s 测试报告：FAIL" %(tool, format))
        lptlog.debug(e)

class ToolCompareError(Exception):
    ''' '''
    
class ToolCompare(object):
    ''''''
    def __init__(self, tool, xmls_dict):
        self.tool = tool
        self.xmls_dict = xmls_dict
        self.xmls_keys = list(xmls_dict.keys())
        self.results_xml_list = list(xmls_dict.values())
        self.tool_indexs = INDEX_KEYS[self.tool]
              
    def get_parallels(self):
        parallelstring = lptxml.get_result_parallels(self.results_xml_list[0], self.tool)
        return utils.check_int_list(parallelstring)
    
    def check_parallels(self):
        '''检查parallels是否相同，相同则进行比较，不同则结束比较
        @param:limit result.xml limit to 10
        @return:boolean   '''
        parallels=lptxml.get_result_parallels(self.results_xml_list[0], self.tool)
        if parallels is None:
            return False
        
        for result_xml in self.results_xml_list:
            if parallels == lptxml.get_result_parallels(result_xml, self.tool):
                continue
            else:
                return False
        return True
            
    
    def get_parallel_result(self, result_xml, parallel):
        '''@param parallel: 并行数
        @param result_xml:result xml 
        @param indexs:测试指标
        @return: dict'''
        parallel_result_dict = {}
        
        xmlresults = lptxml.XmlResults(result_xml)
        lptlog.debug('匹配times="Average", parallel=%s 的results node' % parallel)
        nodes = xmlresults.search_nodes_by_parallelAndtimes(self.tool, parallel, "Average")
        if nodes:
            for key in self.tool_indexs:
                parallel_result_dict[key] = xmlresults.get_result_text(nodes[0], key)
            return parallel_result_dict
        else:
            raise ToolCompareError("nodes 期望不为空")
        

    def get_index_result(self, index, result_xml):
        '''@param index: 指标
        @param result_xml: result xml
        @param parallels:并行数
        @return: dict'''
        index_result_dict = {}
        xmlresults = lptxml.XmlResults(result_xml)
        for parallel in self.get_parallels():
            values = xmlresults.search_element_by_tagAndtimes(self.tool, index, parallel, "Average")
            if not values:
                lptlog.warning("获取times='Average', index=%s, parallel=%s 的值为空，赋值0")
                value = 0
            else:
                value = float(values[0])
            lptlog.debug('匹配times="Average", index=%s , parallel=%s 的results value:%s' % (index, parallel, value))
            index_result_dict[parallel] = value
        
        return index_result_dict
    
    def get_parameters(self, result_xml):
        xmlresults = lptxml.XmlResults(result_xml)
        parameterstring = xmlresults.get_tool_result_parallels(self.tool, key='parameters')
        parallelstring = xmlresults.get_tool_result_parallels(self.tool, key='parallels')
        times = xmlresults.get_tool_result_parallels(self.tool, key='times')
        return {"parameters":parameterstring, "parallels":parallelstring, "times":times}
    
    def get_tool_keys(self):
        return INDEX_KEYS[self.tool]
    
    #def get_config_value(self, key):
     #   return readconfig.get_conf_instance(DOCS_FILE).get_str_value(self.tool, key)
    
class ParallelsError(Exception):
    ''''''
       
class CompareToolXls(ToolCompare):
    ''''''
    def __init__(self, tool, tool_sheet, xls_object, xmls_dict):
        super(CompareToolXls, self).__init__(tool, xmls_dict)
        self.xls_write = xls_object
        self.sheet = tool_sheet
        self.parallels = self.get_parallels()
        if self.check_parallels():
            lptlog.debug("results中parallels相同")
        else:
            raise ParallelsError("%s 对比， parallels不同"  % self.tool)
        
        
    def _set_row_height(self, row, height):
        self.seet.row(row).height = height
    
    def _set_col_width(self, col, width):
        self.sheet.col(col).width = width

        
    def write_title(self, row_width=3, col_width=4):
        #col_width = len(self.tool_indexs)
        cmp_title = "---%s Compare Results---" % self.tool
        self.xls_write.title(self.sheet, cmp_title, rowmin=1, rowmax=1+row_width, colmin=1, colmax=1+col_width )
        return 1+row_width+1
    
    def _set_text_format(self, key, row, colmin, colmax):
        text = get_config_value(key, self.tool)
        u_text = utils.to_unicode(text)
        colswidth = sum([ self.sheet.col(col).width for col in range(colmin, colmax)])
        #rowheight = self.sheet.row(row).height
        rowheight = self.sheet.get_row_default_height()
        if len(u_text+"    ") * 430 < colswidth:
            pass
        else:
            rate = len(u_text+"    ") * 430 / colswidth + 1
            self.sheet.row(row).height = rowheight * rate
            
    def write_tool_descriptions(self, row, colmin, colmax):
        self.xls_write.section_title(self.sheet, "一.  概述", row)
        #colmax=colmin+len(self.tool_indexs)
        self.xls_write.description(self.sheet, "    %s" % get_config_value("descriptions", self.tool), row+1, colmin=colmin, colmax=colmax)
        return row+2
    
     
    def write_tool_index(self, row, colmin, colmax, section="二"):
        #colmax = colmin + len(self.tool_indexs)
        self.xls_write.section_title(self.sheet, "%s.  指标" % section, row)
        row = row + 1
        for index in self.tool_indexs:
            self.xls_write.description(self.sheet, "    %s: %s" % (index, get_config_value(index, self.tool)), row, colmin=colmin, colmax=colmax)
            row = row + 1
        return row
    
    def write_parameters(self, row, colmin, colmax, section="三"):
        self.xls_write.section_title(self.sheet, "%s.  参数" % section, row)
        row += 1
        for key in parameters_keys:
            self.xls_write.write_cell(self.sheet, key, row, col=colmin)
            row += 1
            for xml_name in self.xmls_keys:
                self.xls_write.data_seq(self.sheet, xml_name, row, col=1)
                self.xls_write.parameters(self.sheet, self.get_parameters(self.xmls_dict[xml_name])[key], row, colmin+1, colmax)
                row += 1
            row +=1
        return row 
    
    def write_result_title(self, row, section="四"):
        self.xls_write.section_title(self.sheet, "%s.  结果" % section, row)
        return row + 1
    
    def write_parallel_data_des(self, parallel, row):
        self.xls_write.write_cell(self.sheet, "%s Parallel Data" % parallel, row, 1)
        #if len(utils.to_unicode("%s Parallel Data" % parallel)) * 367  > self.sheet.col(1).width:
           # self.sheet.col(1).width = len(utils.to_unicode("%s Parallel Data" % parallel)) * 367
    
    def write_parallel_data_title(self, row, col=1):
        self.xls_write.data_title(self.sheet, ['TEST'], row, col_start_index=col)
        self.xls_write.data_title(self.sheet, self.tool_indexs, row, col_start_index=col+1)
       
        #for x in range(len(self.tool_indexs)):
            #if len(utils.to_unicode(self.tool_indexs[x])) * 367 > self.sheet.col(col+1+x).width:
               # self.sheet.col(col+1+x).width = len(utils.to_unicode(self.tool_indexs[x])) * 367
    
    def write_parallel_data(self, parallel, row, col=1):
        for xml_name in self.xmls_keys:
            self.xls_write.data_seq(self.sheet, xml_name, row)
            result_dict = self.get_parallel_result(self.xmls_dict[xml_name], parallel)
            self.xls_write.data(self.sheet, list(map(float, [result_dict.get(index) for index in self.tool_indexs])), row, col_start_index=col+1)
            row = row+1
            
        return row
    
    def write_index_data_des(self, index, row):
        self.xls_write.write_cell(self.sheet, "%s" % index, row, 1)
        #if len(utils.to_unicode(index)) * 367  > self.sheet.col(1).width:
         #   self.sheet.col(1).width = len(utils.to_unicode(index)) * 367
        
    def write_index_data_title(self, row, col=1):
        self.xls_write.data_title(self.sheet, ['TEST'], row, col_start_index=col)
        self.xls_write.data_title(self.sheet, ["Par %d" % parallel for parallel in self.parallels ], row, col_start_index=col+1)
            
    def write_index_data(self, index, row, col=1):
        for xml_name in self.xmls_keys:
            self.xls_write.data_seq(self.sheet, xml_name, row)
            self.xls_write.data(self.sheet, list(map(float, list(self.get_index_result(index, self.xmls_dict[xml_name]).values()))), row, col_start_index=col+1)
            row = row+1
            
        return row+1
    
   
    def _get_all_index_data(self, index):
        '''获取index所有xml数据中，tag为index的所有测试数据
        @return: list, ie:[ (), ()], 其中一个list为parallel元组'''
        index_data_list = []
        for xml_name in self.xmls_keys:
            index_data = list(map(float, list(self.get_index_result(index, self.xmls_dict[xml_name]).values())))
            index_data_list.append(index_data)
        index_data_list.insert(0, self.parallels)
    
        return index_data_list
         
    def _get_max_value(self, index):
        Y_max = 0
        index_data_list =  self._get_all_index_data(index)
        for index_list in index_data_list:
            if Y_max < max(index_list):
                Y_max = max(index_list)
        return Y_max
              
    def __gen_index_graphic(self, index,  graphic_name, title):
        graphic = chart.Draw(list(map(list, list(zip(*self._get_all_index_data(index))))), graphic_name, title)
        Y_max = self._get_max_value(index)
        xais = graphic.set_X("parallels")
        yais = graphic.set_Y("Results", tic_interval=Y_max/6)
        ar = graphic.creat_area((300, 100), xais, yais)
        plot_list = []
        for xml_name in self.xmls_keys:
            plot = graphic.creat_line_plot(xml_name, self.xmls_keys.index(xml_name)+1, tick_mark_list[self.xmls_keys.index(xml_name)])
            plot_list.append(plot)
        graphic.area_add_plot(ar, plot_list)
        graphic.draws(ar)
        
    def gen_index_graphic(self, graphic_name):
        '''gen all index graphic'''
        for index in self.tool_indexs:
            graphic_name = os.path.join(tmpdir,"%s_%s_%s" % (graphic_name, self.tool, index))
            graphic = chart.Draw(list(map(list, list(zip(*self._get_all_index_data(index))))), graphic_name, index)
            xais = graphic.set_X("parallels")
            yais = graphic.set_Y("Results")
            ar = graphic.creat_area((300, 100), xais, yais)
            plot_list = []
            for xml_name in self.xmls_keys:
                plot = graphic.creat_line_plot(xml_name, self.xmls_keys.index(xml_name)+1, tick_mark_list[self.xmls_keys.index(xml_name)])
                plot_list.append(plot)
            graphic.area_add_plot(ar, plot_list)
            graphic.draws(ar)
        
    def _get_all_par_data(self, parallel):
        par_data_list = []
        for xml_name in self.xmls_keys:
           result_dict = self.get_parallel_result(self.xmls_dict[xml_name], parallel)
           par_data = list(map(float, [result_dict.get(index) for index in self.tool_indexs]))
           par_data_list.append(par_data)
        par_data_list.insert(0, self.tool_indexs)
        return par_data_list
    
    def __gen_par_graphic(self, parallel, graphic_name, title):
        graphic = chart.Draw(list(map(list, list(zip(*self._get_all_par_data(parallel))))), graphic_name, title)
        xais = graphic.set_X("Index")
        yais = graphic.set_Y("Results")
        ar = graphic.creat_area((300, 100), xais, yais)
    
        plot_list = []
        for xml_name in self.xmls_keys:
            #plot = graphic.creat_bar_plot(xml_name, cluster=(self.xmls_keys.index(xml_name), len(self.xmls_keys)))
            plot = graphic.creat_line_plot(xml_name,  self.xmls_keys.index(xml_name)+1,  tick_mark_list[self.xmls_keys.index(xml_name)])
            plot_list.append(plot)
        
        graphic.area_add_plot(ar, plot_list)
        graphic.draws(ar)
        
    def gen_par_graphic(self, graphic_name):
        '''gen all par graphic'''
        for parallel in self.parallels:
            graphic_name = os.path.join(tmpdir,"%s_%s_P%d" % (graphic_name, self.tool, parallel))
            graphic = chart.Draw(list(map(list, list(zip(*self._get_all_par_data(parallel))))), graphic_name)
            xais = graphic.set_X("Index")
            yais = graphic.set_Y("Results")
            ar = graphic.creat_area((300, 100), xais, yais)
    
            plot_list = []
            for xml_name in self.xmls_keys:
            #plot = graphic.creat_bar_plot(xml_name, cluster=(self.xmls_keys.index(xml_name), len(self.xmls_keys)))
                plot = graphic.creat_line_plot(xml_name,  self.xmls_keys.index(xml_name)+1,  tick_mark_list[self.xmls_keys.index(xml_name)])
                plot_list.append(plot)
            graphic.area_add_plot(ar, plot_list)
            graphic.draws(ar)
        
    def gen_graphcis(self, writeType, graphic_name="cmp"):
        try:
            if writeType == "index":
                self.gen_index_graphic(graphic_name)
            else:
                self.gen_par_graphic(graphic_name)
        except Exception as e:
            lptlog.error("gen graphic error:%s" %e)
      
    def _tran_png_to_bmp(self, pngfile):
        bmpfile = pngfile.split('.')[0]+".bmp"
        Image.open(pngfile).convert("RGB").save(bmpfile)
        return bmpfile
        
 
    def write_index_img(self, index, graphic_name, row, col):
        
        try:
            graphic_name = os.path.join(tmpdir,"%s_%s_%s" % (graphic_name, self.tool, index))
            self.__gen_index_graphic(index, graphic_name, index)
        except Exception as e:
            lptlog.error("gen graphic error")
            lptlog.debug(e)
        else:
                #xlwt only support bmpfile, so we need to transate to bmpfile
            pngfile = graphic_name+".ps"
            if os.path.exists(pngfile):
                bmpfile = self._tran_png_to_bmp(pngfile)
                self.xls_write.insert_img(self.sheet, bmpfile, row, col)
                row = row + 9
            else:
                lptlog.error("NO found %s" % pngfile)
        finally:
            return row + 1
         
        
    def write_par_img(self, parallel, graphic_name, row, col):
        
        try:
            graphic_name = os.path.join(tmpdir,"%s_%s_P%d" % (graphic_name, self.tool, parallel))
            self.__gen_par_graphic(parallel, graphic_name, parallel)
        except Exception as e:
            lptlog.error("gen graphic error:%s" % e )
            #lptlog.exception('')
           
        else:
                #xlwt only support bmpfile, so we need to transate to bmpfile
            pngfile = graphic_name+".ps"
            if os.path.exists(pngfile):
                bmpfile = self._tran_png_to_bmp(pngfile)
                self.xls_write.insert_img(self.sheet, bmpfile, row, col)
                row = row + 9
            else:
                lptlog.error("NO found %s" % pngfile)
        finally:
            return row + 1
        
    def write_lmbench(self):
        ''' write compare lmbench xls'''
        colwidth = 5
        lptlog.debug("lmbench sheet 写入标题" ) 
        row = self.write_title(col_width=colwidth) + 1
        row_des = row
        row = self.write_tool_descriptions(row_des, colmin=1, colmax=1+colwidth) + 1
        row = self.write_parameters(row, 1, 1+colwidth, section="二")
        row = self.write_result_title(row, section="三")
        
        for lm_des in lmbench.des[1:]:
            #get group data ,type list
                #获取tiltle_keys切片，并获取该切片位置的 group tilte,然后转换成list
            data_title_list = list(lmbench.title_keys[lmbench.des.index(lm_des)])
            title_len = len(data_title_list)
            self.xls_write.lmbench_des(self.sheet, lm_des, row, 1, 1+title_len)
            row +=1
            self.xls_write.data_title(self.sheet, ["Test"], row)
            self.xls_write.data_title(self.sheet, data_title_list, row, col_start_index=2)
            row += 1
            
            parallel = self.get_parallels()[0]
            for xml_name in self.xmls_keys:
                self.xls_write.data_seq(self.sheet, xml_name, row)
                result_dict = self.get_parallel_result(self.xmls_dict[xml_name], parallel)
                keys = list(lmbench.lm_keys[lmbench.des.index(lm_des)])
                self.xls_write.data(self.sheet, list(map(float,[result_dict.get(key) for key in keys] )), row, col_start_index=2)
                row += 1
            row = row+1
            
            #调整格式
        self.sheet.col(1).width = 4000
        for col in range(2, 12):
            self.sheet.col(col).width = 3600
        self._set_text_format("descriptions", row_des+1, 1, colwidth+1+1)
         
def compare_tool_xls(tool, tool_sheet, xls_object, xmls_dict, writeType="parallel", chart=False):
    ''' tool xls compare report'''
    tool_cmp_object = CompareToolXls(tool, tool_sheet, xls_object, xmls_dict)
    
    if tool == "lmbench":
        tool_cmp_object.write_lmbench() 
        return 
    if writeType=="parallel":
        colwidth = len(tool_cmp_object.tool_indexs)
    elif writeType=="index":
        colwidth = len(tool_cmp_object.parallels)
        
    lptlog.debug("%s sheet 写入标题" % tool) 
    row = tool_cmp_object.write_title(col_width=colwidth) + 1  
    row_des = row
    row = tool_cmp_object.write_tool_descriptions(row_des, colmin=1, colmax=1+colwidth) + 1

    row_index_start = row 
    row = tool_cmp_object.write_tool_index(row, colmin=1, colmax=1+colwidth) + 1
    row = tool_cmp_object.write_parameters(row, 1, 1+colwidth)
    row = tool_cmp_object.write_result_title(row)
    #产生graphic
    #tool_cmp_object.gen_graphcis(writeType, graphic_name="lpt")
    if writeType=="parallel":
     #   row = 8
        for parallel in tool_cmp_object.parallels:
            tool_cmp_object.write_parallel_data_des(parallel, row)
            tool_cmp_object.write_parallel_data_title(row+1)
            row = tool_cmp_object.write_parallel_data(parallel, row+2)
            row = row + 1
            
            if colwidth <=4:
                for col in range(2, colwidth+1):
                    tool_cmp_object._set_col_width(col, 16000/colwidth)
            if chart:
                row = tool_cmp_object.write_par_img(parallel, "cmp", row ,2)
        
    elif writeType=="index":
       # row = 8
        #for parallel in tool_cmp_object.parallels:
        for index in tool_cmp_object.tool_indexs:
            tool_cmp_object.write_index_data_des(index, row)
            tool_cmp_object.write_index_data_title(row+1)
            row = tool_cmp_object.write_index_data(index, row+2)
            row = row + 1
            if colwidth==2:
                tool_cmp_object._set_col_width(2, 8000)
                tool_cmp_object._set_col_width(3, 8000)
            elif colwidth == 1:
                tool_cmp_object._set_col_width(2, 16000)
                
            if chart:
                row = tool_cmp_object.write_index_img(index, "cmp", row, 2)
            
    #调整表格宽度
   
    tool_cmp_object._set_text_format("descriptions", row_des+1, 1, colwidth+1+1)
    for index in INDEX_KEYS[tool]:
        tool_cmp_object._set_text_format(index, row_index_start+INDEX_KEYS[tool].index(index)+1, 1, 1+colwidth+1)
     
     
class Compare(object):
    '''creat对比测试报告'''
        
    def __init__(self, results_xml_list, report_file,
                  input_tools, input_name_list):
        '''获取对比工具集和result.xml集'''
        self.results_xml_list = results_xml_list
        self.num = self.get_cmp_num()
        self.report_file = report_file
        self.input_name_list = input_name_list
        self.input_tools = input_tools
        
    def get_cmp_num(self, limit=80):
        '''限定对比数'''
        num = len(self.results_xml_list)
        if num < 2:
            lptlog.warning("2<=期望result.xml数量<=%d" % limit)
        if num > limit:
            return limit
        else:
            return num
        
    def get_cmp_xml(self):
        return self.results_xml_list[:self.num]
    
    def set_xml_name(self):
        if not self.input_name_list:
            xml_name_list = [ "CMP_%s" % letter for letter in list(string.ascii_uppercase)]
        else:
            if len(list({}.fromkeys(self.input_name_list).keys())) < self.get_cmp_num():
                lptlog.warning("请输入正确的名称数，期望：不重复名称 >%d 个 " % self.get_cmp_num())
                sys.exit()
            else:
                xml_name_list = self.input_name_list[:self.get_cmp_num()]
        return xml_name_list
    
    def get_xmls_dict(self):
        xmls_dict = {}
        for l, v in zip(tuple(self.set_xml_name()), tuple(self.get_cmp_xml())):
            xmls_dict[l] = v
        return xmls_dict
    
    def get_cmp_tools(self):
        '''只对比多个result.xml中都包含的测试工具, 获取最终对比测试工具
        @return: 最终测试的tools列表'''
        if not self.input_tools:
            tools = lptxml.get_result_tools(self.results_xml_list[0])
        else:
            tools = self.input_tools
         
        for results_xml in self.get_cmp_xml()[1:]:
            results_xml_tools = lptxml.get_result_tools(results_xml)
            tools = [ tool for tool in tools if tool in results_xml_tools ]
        
        return tools
    
class XlsCompare(Compare):
    ''' Xls Compare report'''
    def __init__(self, results_xml_list, report_file, input_tools, input_name_list):
        super(XlsCompare, self).__init__(results_xml_list, report_file, input_tools, input_name_list)  
        self.xls_write = lptxls.Wxls()
        self.xmls_dict = self.get_xmls_dict()
    
    def cmp_tools(self, chart=False):
        tools =  self.get_cmp_tools()
        if not tools:
            raise ValueError("result.xml中不包含相同的tool")
        lptlog.info("----最终对比工具: %s " % utils.list_to_str(tools))
         #写入system info
        lptlog.info("写入system environment")
        infoxls = InfoXlsReport(self.xls_write )
        infoxls.write_keys()

        col = 3
        for key, value in self.xmls_dict.items():
            infoxls.write_values(value, key, col)
            col += 1
    
        for tool in tools:
            lptlog.debug("创建 %s sheet" % tool)
            tool_sheet = self.xls_write.sheet(tool)
            try:
                lptlog.info("开始创建 %s 对比测试报告"  % tool)
                if tool in ("iozone",):
                    writeType = "parallel"
                else:
                    writeType = "index"
                compare_tool_xls(tool, tool_sheet, self.xls_write, self.xmls_dict, writeType=writeType, chart=chart)
                lptlog.info("""
                 --------------------------------------------------------------
                         创建 %s 对比测试报告：PASS
                 --------------------------------------------------------------
                """ % tool)
            except Exception:
                lptlog.error("""
                 --------------------------------------------------------------
                         创建 %s 对比测试报告：FAIL
                 --------------------------------------------------------------
                """ % tool)
                lptlog.exception("")
                continue
            
    def save(self):
        self.xls_write.save(self.report_file)
        


    
