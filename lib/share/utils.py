# -*- coding:utf-8 -*-

"""
 常用方法集合
"""

import os, sys, time
import shutil
import subprocess
import pickle
import string
import re
import fnmatch
import stat
import string
import random

from lpt.lib import lptlog
from lpt.lib.error import *
#import subprocessFix as subprocess
import subprocess
from . import magic_bak

try:
    import hashlib
except ImportError:
    import md5
    import sha
    
    
def hash_method(type, input=None):
    """
    Returns an hash object of type md5 or sha1. This function is implemented in
    order to encapsulate hash objects in a way that is compatible with python
    2.4 and python 2.6 without warnings.

    Note that even though python 2.6 hashlib supports hash types other than
    md5 and sha1, we are artificially limiting the input values in order to
    make the function to behave exactly the same among both python
    implementations.

    :param input: Optional input string that will be used to update the hash.
    """
    if type not in ['md5', 'sha1']:
        raise ValueError("Unsupported hash type: %s" % type)

    try:
        hash = hashlib.new(type)
    except NameError:
        if type == 'md5':
            hash = md5.new()
        elif type == 'sha1':
            hash = sha.new()

    if input:
        hash.update(input)

    return hash

def hash_file(filename, size=None, method="md5"):
    """
    Calculate the hash of filename.
    If size is not None, limit to first size bytes.
    Throw exception if something is wrong with filename.
    Can be also implemented with bash one-liner (assuming size%1024==0):
    dd if=filename bs=1024 count=size/1024 | sha1sum -

    :param filename: Path of the file that will have its hash calculated.
    :param method: Method used to calculate the hash. Supported methods:
            * md5
            * sha1
    :return: Hash of the file, if something goes wrong, return None.
    """
    chunksize = 4096
    fsize = os.path.getsize(filename)

    if not size or size > fsize:
        size = fsize
    f = open(filename, 'rb')

    try:
        hash = hash_method(method)
    except ValueError:
        lptlog.error("Unknown hash type %s, returning None" % method)

    while size > 0:
        if chunksize > size:
            chunksize = size
        data = f.read(chunksize)
        if len(data) == 0:
            lptlog.debug("Nothing left to read but size=%d" % size)
            break
        hash.update(data)
        size -= len(data)
    f.close()
    return hash.hexdigest()

def sh_escape(command):
    """
    Escape special characters from a command so that it can be passed
    as a double quoted (" ") string in a (ba)sh command.

    Args:
            command: the command string to escape.

    Returns:
            The escaped command string. The required englobing double
            quotes are NOT added and so should be added at some point by
            the caller.

    See also: http://www.tldp.org/LDP/abs/html/escapingsection.html
    """
    command = command.replace("\\", "\\\\")
    command = command.replace("$", r'\$')
    command = command.replace('"', r'\"')
    command = command.replace('`', r'\`')
    return command



def run_cmd(command, args=[], timeout=None, ignore_status=False, output_tee=None):
    """
    Run a command on the host.

    @param command: the command line string.
    @param timeout: time limit in seconds before attempting to kill the
            running process. The run() function will take a few seconds
            longer than 'timeout' to complete if it has to kill the process.
    @param ignore_status: do not raise an exception, no matter what the exit

    @param ignore_status: do not raise an exception, no matter what the exit
            code of the command is.
    @param stdout_tee: optional file-like object to which stdout data
            will be written as it is generated (data will still be stored
            in result.stdout).
    @param args: sequence of strings of arguments to be given to the command
            inside " quotes after they have been escaped for that; each
            element in the sequence will be given as a separate command
            argument

    :return: a CmdResult object

    :raise CmdError: the exit code of the command execution was not 0
    """

    if not isinstance(args, list):
        raise TypeError('Got a string for the "args" keyword argument, '
                        'need a list.')
    for arg in args:
        command += ' "%s"' % sh_escape(arg)
    lptlog.debug("执行命令:%s" % command)
    p = subprocess.Popen(command,  stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, output_err = p.communicate()
    if timeout and isinstance(timeout, int):
        lptlog.info('sleep')
        time.sleep(timeout)
        retcode = p.poll()
        if retcode:
            lptlog.error('运行 %d 秒，%s 程序无响应' %(timeout, command))
            raise  CalledProcessError()
    output = str(output,'utf-8')
    #output=output[2:-1]
    if p.wait():
        lptlog.error("执行命令: %s, 输出错误信息:\n%s" %(command, output_err))
        if not ignore_status:
            lptlog.info('ignore_status')
            raise CalledProcessError(p.poll(), command)
    elif output_tee:
        lptlog.debug("执行命令: %s, 输出信息:\n %s" %(command, output))
        return output 
    else:
        lptlog.debug("执行命令: %s, 输出信息:\n %s" %(command, output))
        return 0
        
        

   
def system_output(command, args=[], timeout=None, ignore_status=False):
    """
    Run a command and return the stdout output.

    @param command: command string to execute.
    @param timeout: time limit in seconds before attempting to kill the
            running process. The function will take a few seconds longer
            than 'timeout' to complete if it has to kill the process.
    @param ignore_status: do not raise an exception, no matter what the exit
            code of the command is.
    @param args: sequence of strings of arguments to be given to the command
            inside " quotes after they have been escaped for that; each
            element in the sequence will be given as a separate command
            argument
    @return: a string with the stdout output of the command.
    """
    
    out = run_cmd(command, args, timeout, ignore_status, output_tee=True)
    if out[-1:] == '\n':
        out = out[:-1]
    return out



def system(command, args=[], timeout=None, ignore_status=False ):
    """
    Run a command

    @param timeout: timeout in seconds
    @param ignore_status: if ignore_status=False, throw an exception if the
            command's exit code is non-zero
            if ignore_status=True, return the exit code.
    @param verbose: if True, lptlog the command being run.

    :return: exit status of command
            (note, this will always be zero unless ignore_status=True)
    """
    return  run_cmd(command, args, timeout, ignore_status,  output_tee=False)


def cat_file_to_cmd(file, command, ignore_status=False, return_output=False):
    """
    equivalent to 'cat file | command' but knows to use
    zcat or bzcat if appropriate
    """
    if not os.path.isfile(file):
        raise NameError('invalid file %s to cat to command %s'
                        % (file, command))

    if return_output:
        run_cmd_to = system_output
    else:
        run_cmd_to = system
    if magic_bak.guess_type_bak(file) == 'application/x-bzip2':
        cat = 'bzcat'
        lptlog.info('bzcat')
    elif magic_bak.guess_type_bak(file) == 'application/x-gzip':
        cat = 'zcat'
        lptlog.info('zcat')
    else:
        cat = 'cat'
        lptlog.info('cat')
    lptlog.info('%s %s | %s' %(cat,file,command))
    return run_cmd_to('%s %s | %s' % (cat, file, command), ignore_status=ignore_status)
    
def extract_tarball_to_dir(tarball, srcdir):
    """
    Extract a tarball to a specified directory name instead of whatever
    the top level of a tarball is - useful for versioned directory names, etc
    """
    
    extracted = cat_file_to_cmd(tarball, 'tar xCvf %s - 2>/dev/null' % srcdir,
                                return_output=True).splitlines()
    
    if not extracted[0]:
        raise NameError('extracting tarball produced no dir')
    else:
        return os.path.join(srcdir, extracted[0])
   
 
def configure(extra=None, configure='./configure'):
    """
    Run configure passing in the correct host, build, and target options.

    :param extra: extra command line arguments to pass to configure
    :param configure: which configure script to use
    """
    args = []
    if 'CHOST' in os.environ:
        args.append('--host=' + os.environ['CHOST'])
    if 'CBUILD' in os.environ:
        args.append('--build=' + os.environ['CBUILD'])
    if 'CTARGET' in os.environ:
        args.append('--target=' + os.environ['CTARGET'])
    if extra:
        args.append(extra)
    lptlog.info('configure:')
    lptlog.info(configure)
    lptlog.info('args:')
    lptlog.info(args)
    system(configure, args=args)

def make(extra='', make='make', timeout=None, ignore_status=False):
    """
    Run make, adding MAKEOPTS to the list of options.

    :param extra: extra command line arguments to pass to make.
    """
    cmd = '%s %s %s' % (make, os.environ.get('MAKEOPTS', ''), extra)
    return system(cmd, timeout=timeout, ignore_status=ignore_status)

def has_gcc():
    if os.path.isfile('/usr/bin/gcc') or os.path.isfile('/bin/gcc') or os.path.isfile('/sbin/gcc'):
        lptlog.info("gcc 检查:PASS")
    else:
        lptlog.error("gcc 检查:FAIL")
        raise DespendException("gcc")
  
def has_file(name, *args):
    for file in args:
        if not os.path.isfile(file):
            raise DespendException("缺少 %s 包"  % name) 
        else:
            continue
    lptlog.info("%s 检查: PASS" % name )
        
def run_shell(cmd, args_list=[]):
    '''
        采用os.system执行shell
    '''
    args_string_list = list(map(str, args_list))
    commands = cmd + " " + " ".join(args_string_list)
    try:
        lptlog.debug("执行命令:%s" % commands)
        os.system(commands)
    except Exception:
        #lptlog.exception("执行 %s 发生Error:" % commands)
        lptlog.error("执行 %s 发生Error:" % commands)
        raise RunShellError()
    
def run_shell2(cmd, args_list=[], file=None):
    '''
        采用subprocess.call执行测试
    '''
    args_list.insert(0, cmd)
    args_string_list = list(map(str, args_list))
    
    lptlog.info("执行命令: %s" % " ".join(args_string_list))
                 
    if file:
        fd = open(file, 'w')
    else:
        fd=None
    lptlog.info(file)
    lptlog.info(args_string_list)
    status = subprocess.call(args_string_list, stdout=fd, stderr=fd)
    #status = subprocess.call(args_string_list)
    
    if status > 0:
        lptlog.error("执行 %s 发生Error:" % " ".join(args_string_list))
        raise  RunShellError()
    
    if file:
        fd.close()
        
def str_to_int(strings):
    '''
    把数字字符串转换成整型
    '''
    return int(strings)

def string_to_float(string_list):
    '''字符数字转换成浮点型
    @return: list 
    '''
    return [float(x) for x in string_list]
    

def strwidth(strs, width=20, position='left', fillchar=' '):
    '''扩充字符串长度
    '''
    if position == 'left':
        return strs.ljust(width, fillchar)
    elif position == 'right':
        return strs.rjust(width, fillchar)
    elif position == 'center':
        return strs.center(width, fillchar)
    else:
        return strs.ljust(width, fillchar)

def check_int_list(strings, ops=','):
    '''
    把数字字符串转换成数字
    @param string: 
    @param ops: 
    @return: int list或NameError
    '''
    int_list = []
    strings_list = strings.split(ops)
    for int_str in strings_list:
        try:
            int_no = str_to_int(int_str)
        except ValueError:
            raise FormatterError()
        int_list.append(int_no)
    
    return int_list
        
def search_string_value(substr, strings, pos, ops=None):
    '''获取substr对应的value
    '''
    if re.search(r'%s' % substr, strings):
        value = strings.split(ops)[pos]
       # lptlog.debug(value)
        try:
            float(value)
        except NameError:
            value = 0
    else:
        value = 0
         
    return value

def int_to_str_list(int_list):
     
    return list(map(str, int_list))


def sum_list(num_list):
    '''定义list求和方法
    '''
    return sum(num_list)


def average_list(num_list, bits=2):
    '''定义list求平均值方法
    '''
    if len(num_list) !=0 :
        return round(sum(num_list)/len(num_list), bits)
    else:
        return 0
        

def check_size_format(size, match="\d+(k|m|g|t)?"):
    '''检查size格式满足1,  1k, 1m, 1g, 1t
    match
    '''
    r = re.compile(r"%s" % match, re.I)
    return r.match(r'%s' % size)

def transale_to_size(size, base=1024):
    '''把格式化的size转换成全数字
    @param size: 
    @param base: 
    @return: size 
    @type return: float
    '''
    size = str(size)
    
    if check_size_format(size):
        if size[-1] in ("k", "K"):
            size = float(size[:-1])*base
        elif size[-1] in ("m","M"):
            size = float(size[:-1])*base**2
        elif size[-1] in ("g","G"):
            size = float(size[:-1])*base**3
        elif size[-1] in ("t","T"):
            size = float(size[:-1])*base**4
        else:
            size = float(size)
        
    return size

def custom_format(size, base=1024, unit_format=None, auto=False):
    '''个性化输出格式
    @param size: 
    @param base: 支持1000和1024
    @param unit_format: "k" or ""
    '''
    prefixes = ['k', 'm', 'g', 't']
    #获取数字表示方法
    size = transale_to_size(size, base=base)
    
    if auto:
        i = 0
        while size > float(base):
            size /= float(base)
            i += 1
        else:
            if i == 0:
                return size
            else:
                return '%.2f%s' % (size, prefixes[i-1].upper())
    
    if unit_format is None:
        return size
    
    elif unit_format.lower() in prefixes:
        return '%.2f%s' %( size/float(base**(prefixes.index(unit_format)+1)), unit_format)
    else:
        return size

def human_format(number):
    # Convert number to kilo / mega / giga format.
    if number < 1024:
        return "%d" % number
    kilo = float(number) / 1024.0
    if kilo < 1024:
        return "%.2fk" % kilo
    meg = kilo / 1024.0
    if meg < 1024:
        return "%.2fM" % meg
    gig = meg / 1024.0
    return "%.2fG" % gig


def read_one_line(filename):
    '''读取第一行
    '''
    return open(filename, 'r').readline().rstrip('\n')

def copy(src, dst):
    '''@attention: first,如果src为file,赋予 777 权限
        '''
    try:
        if os.path.isfile(src):
            os.chmod(src, stat.S_IRWXU)
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            pass
    except Exception:
        lptlog.error("文件/文件夹不存在或权限不足, copy失败")
        raise PermitsError()
    
def read_all_lines(file):
    '''open a file ,return all lines
        '''
    fd = open(file ,'r')
    result_lines = fd.readlines()
    fd.close()
    return result_lines

def change_type(value, changeType=float, defaultValue=0):
    '''change value to changeType
        @return: 返回新类型， change失败，返回默认值
        '''
    try:
        return changeType(value)
    except Exception:
        return defaultValue
    
def list_to_str(value_list, ops=","):
    '''把list转换成字符串
    '''
    return ops.join(map(str, value_list))
        
       
def gen_random_strs(num=5, custom=None):
    '''产生随机字符或者数字
	@param Type: str or int 
        @param num: 选择数量
    '''
    if custom is None:
    	strs = string.ascii_letters    
    else:
        strs = custom
    return ''.join(random.sample(strs, num))

#获取版本号
def get_version(file):
    version = read_one_line(file)
    if version:
        return version
    else:
        return "LPT3"

def to_unicode(strs, zfj="utf-8"):
    '''把strs转换成unicode字符'''
    return strs.encode('utf-8').decode(zfj)

def from_unicode(ustrs, zfj="utf-8"):
    return ustrs.encode(zfj)
