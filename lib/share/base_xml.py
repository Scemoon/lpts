# -*- coding:utf-8 -*-


import os, sys
import xml.etree.cElementTree as ET


class XmlTree(object):
    '''
    create_tree:创建xml 树
    add_root_node:添加根节点
    '''
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.tree = None
        
    def create_tree(self):
        '''
        tree对象,返回tree
        '''
        self.tree = ET.ElementTree()
        
        
    def create_root_node(self, root_tag):
        root= ET.Element(root_tag)
        self.tree._setroot(root)
        
        return root
    
    
    def save_file(self):
        self.tree.write(self.xml_file, encoding='utf-8')
        
    
    def init_tree(self):
        '''
        获取tree对象
        '''
        self.tree = ET.parse(self.xml_file)
            
    def get_root(self):
        '''获取root节点
        '''
        return self.tree.getroot()
    
    

class ElementRead(XmlTree):
    '''
    定义node（element)读取、修改xml方法
    '''
    def __init__(self, xml_file):
        super(ElementRead, self).__init__(xml_file)
    
    def get_node_tag(self, node):
        '''
        '''
        return node.tag
   
    def get_elements(self, node):
        '''
        返回node所有elements
        '''
        #list(node),python2.7
        #return list(node)
        return node.getchildren()

    def get_node_attrib_dict(self, node):
        '''
        @return: dict
        '''
        return node.attrib
    
    def get_node_attrib_list(self, node):
        '''
        @return:[(name,value),(name, value)]
        '''
        return node.items()
    
    def get_element_text(self, element):
        '''
        @return: string OR None
        '''        
        return element.text

    def get_node_attrib_keys(self, node):
        
        return node.keys()
    
    def get_node_attrib_value(self, node, key):
        '''
        @return: string
        '''
        return node.get(key)

    def set_node_attrib_value(self, node, key, value):
        
        node.set(key, value)
        
    def find_node_by_tag(self, node, match_tag):
        '''
        搜索匹配match_tag的node实例
        
        @return: 返回第一个node实例或者None,
        '''
        return node.find(match_tag)
    
    def find_nodes_by_tag(self, node, match_tag):
        '''
        搜索匹配match_tag的node所有实例
        @return: 返回所有实例nodes或者None
        '''
        return node.findall(match_tag)
    
    def find_elements_by_tag(self, node, match_tag):
        '''
        搜索匹配match_tag的nodes所有实例
        @return: 返回所有实例nodes或者None
        '''
        return node.findall(match_tag)
    
    def find_text_by_tag(self, node, match_tag):
        '''
        搜索匹配match_tag的element实例
        
        @return: 返回第一个实例对应的text或者None
        '''
        return node.findtext(match_tag)

    def insert_element_by_position(self, node, index, element):
        '''
        指定位置插入element
        
        @return: 返回True
        @raise TypeError: 
        '''
        if isinstance(index, int):
            node.insert(index, element)
        else:
            raise TypeError()
        
    
class ElementWrite(XmlTree):
    '''
        定义Element写方法:
        
        create_node:创建节点
        extend_elements：向节点中扩充elements
        save_file:保存xml到file
        add_node:添加节点方法
        create_element:向节点中添加element
        
    '''
    def __init__(self, xml_file):
        super(ElementWrite, self).__init__(xml_file)

    def add_node(self, father_node, node):
        '''
        添加子节点方法
        '''
        father_node.append(node)
        
    def create_node(self, node_tag, attrib={}):
        '''
            创建节点方法
            
            @param node_tag: 节点标签
            @param node: 节点属性，传入字典
            @param attrib: 节点属性
            @return: 返回节点
            '''
        subnode = ET.Element(node_tag, attrib)
    
        return subnode
    
    def create_node_by_text(self, xmltext):
        '''
        创建node,通过text字符
        @attention: xmltext必须是包含正确xml格式的文档
        @return: 一个node对象
        '''
        return ET.fromstring(xmltext)
    
    def extend_elements(self, node, elements):
        '''
        @attention: python2.7
        
        '''
        node.extend(elements)
    
    def create_element(self, node, element_tag,  text, attrib={}):
        '''
            向节点中添加元素
            @param node: 节点名称
            @param element_tag:  元素标签
            @param text: 标签内容
            @param attrib: 标签属性
            '''
        subelement = ET.SubElement(node, element_tag, attrib)
        subelement.text = text
        
        
class RWXml(ElementRead, ElementWrite):
    '''
    定义xml 都、写、添加、修改、删除等方法，继承Read和Write类 以及自定义的xml操作方法
    '''
    def __init__(self, xml_file):
        super(RWXml, self).__init__(xml_file)
       
    def modefy_element_text(self, element, old_text, new_text):
        
        if element.text == old.text:
            element.text = new_text
            
    def remove_element(self, node, element):
        '''
        @attention: 确定是否存在node和element
        '''
        if ET.iselement(element):
            node.remove(element)
        
    def modefy_node_attrib_value(self, node, key, new_value):
        '''
        @attention: 首先判断是否存在 
        '''
        if self.get_node_attrib_value(node, key):
            node.set(key, new_value)
        
    
        
