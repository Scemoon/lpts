# -*- coding:utf-8 -*-
# filename: lptxml.py

'''
'''

from lpt.lib.share import base_xml
import os, sys
from lpt.lib import readconfig
from lpt.lib import lptlog
from lpt.lib.error import *
from lpt.lib.share import utils
import datetime
from lpt.lib import sysinfo

LPTROOT = os.getenv('LPTROOT')
PARAMETER_FILE = os.path.join(LPTROOT, 'config/parameter.conf')
DB_DIR = os.path.join(LPTROOT, 'db')
JOBS_XML = os.path.join(DB_DIR, 'jobs.xml')

JOB_ELEMENT = '''
<job, jobid= %s>
        <tools>%s</tools>
        <resultsdb>%s</resultsdb>
        <parameter_md5>%s</parameter_md5>
</job> 
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
        'dbench_fio':['Throughtput', 'max_latency']
           
                   
        }
class ConfigToXml(readconfig.BaseConfig, base_xml.RWXml):
    '''
    把标准的ConfigParser文件转换成xml文件
    '''
    def __init__(self, config_file, xml_file ):
        #super(ConfigToXml, self).__init__(config_file, xml_file)
        readconfig.BaseConfig.__init__(self, config_file)
        base_xml.RWXml.__init__(self, xml_file)
        
         # define:需要转换section
        self.custom_sections = None
        
    def add_test_group(self, test_list):
        '''
        定义测试集合
        '''
        if isinstance(test_list, list)  and test_list:
            self.custom_sections = test_list
        else:
            #self.custom_sections = self.get_sections()  #获取全部
            #lptlog.error("测试工具为空， 请指定测试工具集")
            raise CreateJobException, "测试工具为空， 请指定测试工具集"
        return 
        
    def add_configparser_node(self, father_node, node_tag, node_attrib):
        '''
        向father_node中添加包含ParserConfig信息的节点
        @param fathor_node:父节点
        @param node_tag: 节点标签
        @param node_attrib: 节点属性
            '''
            
        sections = self.custom_sections
        lptlog.info('测试工具集：%s' % ' ,'.join(sections))
        for section in sections:
            subnode = self.create_node(node_tag, dict({'id':section}, **node_attrib))
            self.add_node(father_node, subnode)
            options = self.get_options(section)
            for option in options:
                value = self.get_str_value(section, option)
                self.create_element(subnode, option, value)
                
        
    def transfer(self, root_tag, father_node_tag, node_tag, node_attrib):
        '''
        把ParserConfig信息的节点添加到根节点
        
        @param root_tag: 
        @param father_node_tag: 
        @param node_tag: 
        @param node_attrib: 列表
        '''
         #判断self.tree是否未空
        if not self.tree:
            self.create_tree()
            
        #创建主节点
        root = self.create_root_node(root_tag)
        #创建父节点
       
        father_node = self.create_node(father_node_tag)  
        self.add_node(root, father_node)
        self.add_configparser_node(father_node, node_tag, node_attrib)
        
        #save to xml
        self.save_file()


def config_to_xml(config_file, xml_file, root_tag, father_node_tag, node_tag, node_attrib, test_list):
    '''
    定义ParserConfig标准文件转换成xml文件，xml深度为3
    @param config_file:ParserConfig配置文件
    @param xml_file: 生成的xml的文件
    @param root_tag: 根节点标签
    @param father_node_tag: 父节点标签
    @param node_attrib: 节点属性 
    @param test_list: 测试集合
    '''
    
    confxml = ConfigToXml(config_file, xml_file)
    
    if node_attrib is None:
        node_attrib = {}
    if test_list is not None:
        confxml.add_test_group(test_list)
    confxml.transfer(root_tag, father_node_tag, node_tag, node_attrib)
    

class Jobs(base_xml.RWXml):
    '''create jobs.xml
    '''
    def __init__(self, xml_file=JOBS_XML):
        super(Jobs, self).__init__(xml_file)
        
        #初始化
        if not os.path.exists(self.xml_file):
            if  self.tree is None:
                self.create_tree()
                
                #创建主节点
            self.root = self.create_root_node('jobs')
    
        else:
            self.init_tree()
            self.root = self.get_root()
            
    def create_job(self, tools_list, parameter, job_attrib={}, resultXmlName="results"):
        '''创建jobs.xml结构
        '''
        DateString = datetime.datetime.now().strftime('%y%m%d%H%M%S')
        #results = 'result_%s.xml' % DateString
        results = '%s_%s.xml' % (resultXmlName, DateString)
        
        job = self.create_node('job', dict({'id':DateString, 'status':"N/A"}, **job_attrib))
        lptlog.info('任务ID: %s' % DateString)
        
        self.create_element(job, 'resultsDB', results)
        lptlog.info('xml results文件:  %s' % results)
        
        lptlog.debug("创建参数")
        conftoxml = ConfigToXml(parameter, self.xml_file)
        conftoxml.add_test_group(tools_list)
        try:
            conftoxml.add_configparser_node(job, 'tool', {'status':'no'})
        except Exception, e:
            #lptlog.exception('parameter.conf转换xml失败')
            #lptlog.error('parameter.conf转换xml失败')
            raise CreatNodeError, 'parameter.conf转换xml失败: %s' % e
        
        if job is None:
            raise CreatJobsError()
        else:
            return job
        
    def add_job(self, job_node):
        '''
        '''
        #添加job节点到主节点
        self.add_node(self.root, job_node )
        
        #保存到文件
        self.save_file()
    
    def get_new_job(self):
        '''
        @return: 获取最后一个job或IndexError
        '''
        return self.root[-1]
    

    def search_job_node(self, match_tag):
        '''
        返回匹配的第一个node或None
        '''
        return self.find_node_by_tag(self.root, match_tag)
    
    def search_job_nodes(self, match_tag):
        '''
        返回匹配的所有nodes或None
        '''
        return self.find_nodes_by_tag(self.root, match_tag)
    
    
    def search_job_texts(self, element_tag):
        '''
        返回匹配的所有text或None
        @attention: element_tag,应为job_tag下，如job/results
        @return: text,type list 
        '''
        return self.find_texts_by_tag(self.root, element_tag)
    
    def get_job_text(self, job_node, element_tag):
        '''
        获取job中指定tag的text
        '''
        element = self.find_node_by_tag(job_node, element_tag)
        return self.get_element_text(element)
    
    def get_tools_nodes(self, job_node):
        '''
        获取工具所在的节点
        @return: node list or None
        '''
        tools_nodes_list = self.find_nodes_by_tag(job_node, 'tool')
        
        return tools_nodes_list
    
    def get_noexec_tools_nodes(self, job_node):
        '''@return: list 
        '''
        #python 2.7
        #return job_node.findall("tool[@status='no']")
        #python 2.6
        return   filter(lambda x:x.get('status')=='no', job_node.findall("tool"))
    
    def get_tool_attrib(self, tool_node, key):
        return self.get_node_attrib_value(tool_node, key)
    
    def get_tool_name(self, tool_node):
        return self.get_node_attrib_value(tool_node, 'id')
    
    
    #def get_job_test_status(self, tool_node):
       # '''获取工具节点执行状态ok or no
        #'''
       # return self.get_node_attrib_value(tool_node, 'status')
    
    def get_tool_status(self, tools_nodes, tool):
        '''
        获取工具执行状态：
        @param tools_nodes: 所有工具节点
        @param tool: 工具名称
        @return: 'ok' 或 ' no' or None
        '''

        for node in tools_nodes:
            if self.get_node_attrib_value(node, 'id') == tool:
                return self.get_node_attrib_value(node, 'status')
            else:
                continue
    
    def set_tool_status(self, tool_node, status='ok'):
        '''
        用于测试完成后，更改执行状态
        '''
        self.modefy_node_attrib_value(tool_node, 'status', status)
        
    def get_tool_text(self, tool_node, element_tag):
        '''
        @return: 获取标签为element_tag 对应的内容
        '''
        element = self.find_node_by_tag(tool_node, element_tag)
        return self.get_element_text(element)
    
  
def add_job(xml_file, tools_list, parameter, job_attrib={}, resultXmlName="results"):
    '''保存测试任务到xml_file文件
    @param xml_file: 记录测试任务
    @param tools_list:测试结合
    @type tools_list: list 
    '''
    #初始化实例
    jobs = Jobs(xml_file)
    job = jobs.create_job(tools_list, parameter, job_attrib=job_attrib, resultXmlName=resultXmlName)
    #添加job
    jobs.add_job(job)

def search_job_node(node_tag, xml_file=JOBS_XML):
    #初始化实例
    jobs = Jobs(xml_file) 
    return jobs.search_job_node(node_tag)

def search_job_nodes(node_tag, xml_file=JOBS_XML):
    #初始化实例
    jobs = Jobs(xml_file) 
    return jobs.search_job_nodes(node_tag)

def get_job_text(element_tag, xml_file=JOBS_XML, job_node=None):
    '''获取xml_file中job标签的内容，默认取最后一个job
    @param job_tag: 匹配的element的内容
    @return: 返回text
    '''
   #初始化实例
    jobs = Jobs(xml_file)
    if job_node is None:
        job_node = jobs.get_new_job()
        
    return jobs.get_job_text(job_node, element_tag)

def get_job_attrib_value(key, xml_file=JOBS_XML, job_node=None):
    '''获取xml_file中job的属性，默认取最后一个job
    @param key: 匹配的key的属性
    @return: 返回string
    '''
    #初始化实例
    jobs = Jobs(xml_file)
    if job_node is None:
        job_node = jobs.get_new_job()
    
    return job_node.get(key)

def search_job_texts(element_tag, xml_file=JOBS_XML):
    '''搜索element_tag的所有value
    '''
    #初始化实例
    jobs = Jobs(xml_file)
    return jobs.search_job_texts(element_tag)

def get_tools_nodes(job_node, jobs_xml=JOBS_XML):
    '''get all nodes under job_node
    '''
    jobs = Jobs(jobs_xml)
    return jobs.get_tools_nodes(job_node)

def get_tool_node(tool, jobs_xml=JOBS_XML, job_node=None):
    '''获取工具节点
    '''
    jobs = Jobs(jobs_xml)
    if job_node is None:
        job_node = jobs.get_new_job()
   #python 2.7
   # return job_node.find("tool[@id='%s']" % tool)
   #python 2.6
    return filter(lambda x:x.get('id')==tool, jobs.get_tools_nodes(job_node))[0]

        
def get_job_result_file(jobs_xml=JOBS_XML, job_node=None):
    '''
    获取最新job的数据文件
    '''
    result_xml = get_job_text('resultsDB', jobs_xml, job_node)
    result_xml_abspath = os.path.join(DB_DIR, result_xml)
    return result_xml_abspath

    
def get_tool_parameter(tool_node, element_tag, xml_file=JOBS_XML):
    '''获取工具参数
    @param xml_file: jobs数据文件
    @param tool_node: 工具节点
    @param element_tag: 参数名称
    @return: 参数value
    '''
    jobs = Jobs(xml_file)
    return jobs.get_tool_text(tool_node, element_tag)
    #return jobs.find_text_by_tag(tool_node, element_tag)
    
class XmlResults(base_xml.RWXml):
    '''
    定义保存测试数据到xml方法
    '''
    def __init__(self, xml_file):
        super(XmlResults, self).__init__(xml_file)
        self.root_attrib = sysinfo.OSInfo.keys
      
        #初始化
        if not os.path.exists(self.xml_file):
            #if  self.tree is None:
            if not self.tree:
                self.create_tree()
                
             #创建主节点
            self.root = self.create_root_node('results', self.root_attrib)
    
        else:
            self.init_tree()
            self.root = self.get_root()

    #def _get_root_attrib(self):
     #  for subdic in sysinfo.OSysinfo.keys.itervalues():
      #      root_dic = dict(root_dic, **subdic)
       # return root_dic
    
  
    def save_result_node(self, result_node_tag, result_node_attrib, result_list, **kargs):
        '''
        result_list = [ [{}, {}], [{},{}] ]
        第一层测试组数（几次）
        第二层list包含两组数据，第一个dict为测试次数，并行数的信息；第二个dict为测试数据
        @param result_node_tag: 创建的节点标签
        @param result_node_attrib: 附加的节点属性
        @param result_list: 测试数据，格式为: [ [{}, {}], [{},{}] ]
        '''
    
        for result_list_one in result_list:
            result_node = self.create_node(result_node_tag, dict(result_node_attrib, **result_list_one[0]))
            
            #测试数据以字典形式保存，字典是没有顺序的，unixbench输出有顺序，因此格式化key顺序，其他工具如果有需要可以在此定义
            if result_node_tag in INDEX_KEYS.keys():
                keys = INDEX_KEYS.get(result_node_tag)
            else:
                keys = result_list_one[1].keys()
            for key in keys:
                self.create_element(result_node, key, result_list_one[1][key])
            self.add_node(self.root, result_node)
       
        self.save_file()
        
    def get_result_tools(self):
        ''' 获取测试工具'''
        tools = map(lambda x: x.tag, list(self.root))
        #去除重复
        return {}.fromkeys(tools).keys()
    
    def search_tool_result_nodes(self, tool_name):
        '''返回nodes(list)或None
        '''
        return self.find_nodes_by_tag(self.root, tool_name)
    
    def get_tool_element_tag(self, node):
        '''
        @return: list, get all element tag
        '''
        return map(lambda x:x.tag, self.get_elements(node))
    
    def get_tool_result_parallels(self, tool_name, key='parallels'):
        '''返回测试并行数
        @return: None或value(string)
        '''
        tool_nodes = self.search_tool_result_nodes(tool_name)
        return self.get_node_attrib_value(tool_nodes[0], key)
    
    def search_tool_result_parallel_nodes(self, tool_name, parallel):
        '''返回nodes或None
        '''
        #python 2.7
        #return self.find_nodes_by_tag(self.root, "./%s[@parallel='%s']" % (tool_name, parallel))
        #python 2.6
       # print map(lambda x:x.get("parallel"), self.find_nodes_by_tag(self.root, "%s" % tool_name))
        return filter(lambda x:x.get("parallel")==str(parallel), self.find_nodes_by_tag(self.root, "%s" % tool_name))
    
    
    def search_tool_result_by_elementTag(self, tool_name, elementTag):
        '''
        @return: return all elements by tag
        '''
        return self.find_elements_by_tag(self.root, "%s/%s" % (tool_name, elementTag))
    
    def search_element_by_tagAndtimes(self, tool, element_tag, parallel, times):
        '''
        @attention: 搜索到一个列表
        @return: list
        '''
        #python 2.7
        #return self.find_text_by_tag(self.root, "%s[@iter='%s'][@parallel='%s']/%s" % (tool, times, parallel, element_tag))
        #python 2.6
        match_nodes = filter(lambda x:x.get("parallel")==str(parallel) and x.get("iter")==str(times), 
                             self.find_nodes_by_tag(self.root, tool))
        return map(lambda y:self.find_text_by_tag(y, element_tag), match_nodes)
    
    
    def search_nodes_by_parallelAndtimes(self, tool, parallel, times):
        #python 2.6
        match_nodes = filter(lambda x:x.get("parallel")==str(parallel) and x.get("iter")==str(times), 
                             self.find_nodes_by_tag(self.root, tool))
        return match_nodes
    
    
    def get_result_text(self, result_node, element_tag):
        '''
        @param result_node: result节点
        @param element_tag: 元素标签
        @return: text或者None
        '''
        element = self.find_node_by_tag(result_node, element_tag)
        return self.get_element_text(element)
    
    def get_result_attrib(self, result_node, key):
        '''@param key: node attrib 
        '''
        return self.get_node_attrib_value(result_node, key)
        
def get_result_tools(resultDB):
    '''获取resultDB中所有测试工具
    '''
    xmlresult = XmlResults(resultDB)
    return xmlresult.get_result_tools()

def get_result_parallels(resultDB, tool):
    xmlresult = XmlResults(resultDB)
    return xmlresult.get_tool_result_parallels(tool)



  

    
    
    
    
