# -*- coding:utf-8 -*-

'''
  设置LPT运行环境
'''

import os
import sys
import new
import imp


def get_lpt_root():
    '''
    获取lpt根目录
    @return: string or None
    '''
    return os.getenv('LPTROOT')
    

def set_lpt_root(path):
    '''
    设置lpt系统环境
    '''
    os.environ['LPTROOT']= path
    
       
 
class CheckDeps:
    pass



def _create_module(name):
    """
    添加 module 到 sys.modules
    """
    module = new.module(name)
    sys.modules[name] = module
    return module
    

def _create_module_and_parents(name):
    """
    创建一个moduls, 并且把所有的parents modules添加到sys.modulues
    @param name: Module name, such as 'lib.'.
	"""
    parts = name.split(".")
    # first create the top-level module
    parent = _create_module(parts[0])
    created_parts = [parts[0]]
    parts.pop(0)

    # now, create any remaining child modules
    while parts:
        child_name = parts.pop(0)
        module = new.module(child_name)
        setattr(parent, child_name, module)
        created_parts.append(child_name)
        sys.modules[".".join(created_parts)] = module
        parent = module

def import_module(module, from_where):
    """
    Equivalent to 'from from_where import module'.

    @param module: Module name.
    @param from_where: Package from where the module is being imported.
    @return: The corresponding module.
    """
    from_module = __import__(from_where, globals(), locals(), [module])
    return getattr(from_module, module)


def setup(base_path, root_module_name="lpt"):
        
    if sys.modules.has_key(root_module_name):
    # already set up
        return

    _create_module_and_parents(root_module_name)
    imp.load_package(root_module_name, base_path)

    # Allow locally installed third party packages to be found.
    # This is primarily for the benefit of frontend and tko so that they
    # may use libraries other than those available as system packages.
    
    sys.path.insert(0, os.path.join(base_path, "site-packages"))

        
if __name__ == '__main__':
    pass
