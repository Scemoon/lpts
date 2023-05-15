# -*- coding:utf-8 -*-
'''
    @summary: 获取操作系统软、硬件信息
'''

import logging
import os,re
#import os
import regex as re
from lpt.lib.share import utils
import platform
import subprocess

import socket
def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def get_memory_size(unit_format='m'):
    '''获取内存大小
    '''
    size = utils.read_one_line("/proc/meminfo").split()[1]
    size = "%s%s" % (size, "k")
    size = utils.custom_format(size, base=1024, unit_format=unit_format)
    return size
    
def get_current_kernel_arch():
    """Get the machine architecture"""
    # this returns platform.uname()[4]
    return platform.machine()

    
def get_cc():
    try:
        return os.environ['CC']
    except KeyError:
        return 'gcc'


def get_vmlinux():
    """Return the full path to vmlinux

    Ahem. This is crap. Pray harder. Bad Martin.
    """
    vmlinux = '/boot/vmlinux-%s' % os.uname()[2]
    if os.path.isfile(vmlinux):
        return vmlinux
    vmlinux = '/lib/modules/%s/build/vmlinux' % os.uname()[2]
    if os.path.isfile(vmlinux):
        return vmlinux
    return None


def get_systemmap():
    """Return the full path to System.map

    Ahem. This is crap. Pray harder. Bad Martin.
    """
    map = '/boot/System.map-%s' % os.uname()[2]
    if os.path.isfile(map):
        return map
    map = '/lib/modules/%s/build/System.map' % os.uname()[2]
    if os.path.isfile(map):
        return map
    return None


def get_modules_dir():
    """Return the modules dir for the running kernel version"""
    kernel_version = os.uname()[2]
    return '/lib/modules/%s/kernel' % kernel_version


def get_cpu_info():
    """
    Reads /proc/cpuinfo and returns a list of file lines

    :returns: `list` of lines from /proc/cpuinfo file
    :rtype: `list`
    """
    f = open('/proc/cpuinfo', 'r')
    cpuinfo = f.readlines()
    f.close()
    return cpuinfo


def cpu_has_flags(flags):
    """
    Check if a list of flags are available on current CPU info

    :param flags: A `list` of cpu flags that must exists
    on the current CPU.
    :type flags: `list`
    :returns: `bool` True if all the flags were found or False if not
    :rtype: `list`
    """
    cpu_info = get_cpu_info()

    if not isinstance(flags, list):
        flags = [flags]

    for flag in flags:
        if not list_grep(cpu_info, '.*%s.*' % flag):
            return False
    return True


def list_grep(list, pattern):
    """True if any item in list matches the specified pattern."""
    compiled = re.compile(pattern)
    for line in list:
        match = compiled.search(line)
        if (match):
            return 1
    return 0


def get_cpu_vendor_name():
    """
    Get the current cpu vendor name

    :returns: string 'intel' or 'amd' or 'power7' depending
    on the current CPU architecture.
    :rtype: `string`
    """
    vendors_map = {
        'intel': ("GenuineIntel", ),
        'amd': ("AMD", ),
        'power7': ("POWER7", ),
        'mips':("Loongson", "mips64")
    }

    cpu_info = get_cpu_info()
    for vendor, identifiers in list(vendors_map.items()):
        for identifier in identifiers:
            if list_grep(cpu_info, identifier):
                return vendor
    return "N/A"


def get_cpu_arch():
    """Work out which CPU architecture we're running on"""
    f = open('/proc/cpuinfo', 'r')
    cpuinfo = f.readlines()
    f.close()
    if list_grep(cpuinfo, '^cpu.*(RS64|POWER3|Broadband Engine)'):
        return 'power'
    elif list_grep(cpuinfo, '^cpu.*POWER4'):
        return 'power4'
    elif list_grep(cpuinfo, '^cpu.*POWER5'):
        return 'power5'
    elif list_grep(cpuinfo, '^cpu.*POWER6'):
        return 'power6'
    elif list_grep(cpuinfo, '^cpu.*POWER7'):
        return 'power7'
    elif list_grep(cpuinfo, '^cpu.*PPC970'):
        return 'power970'
    elif list_grep(cpuinfo, 'ARM'):
        return 'arm'
    elif list_grep(cpuinfo, '^flags.*:.* lm .*'):
        return 'x86_64'
    else:
        return 'i386'


def get_current_kernel_arch():
    """Get the machine architecture"""
    # this returns platform.uname()[4]
    return platform.machine()


def get_file_arch(filename):
    # -L means follow symlinks
    if os.path.isfile(filename):
        file_data = subprocess.getoutput('file -L ' + filename)
        if file_data.count('80386'):
            return 'i386'
        return None
    else:
        logging.error('file does not exist')
        return False

def count_cpus():
    """number of CPUs in the local machine according to /proc/cpuinfo"""
    f = open('/proc/cpuinfo', 'r')
    cpus = 0
    for line in f.readlines():
        if line.lower().startswith('processor'):
            cpus += 1
    return cpus


def sysctl(key, value=None):
    """Generic implementation of sysctl, to read and write.

    :param key: A location under /proc/sys
    :param value: If not None, a value to write into the sysctl.

    :return: The single-line sysctl value as a string.
    """
    path = '/proc/sys/%s' % key
    if value is not None:
        utils.write_one_line(path, str(value))
    return utils.read_one_line(path)


def sysctl_kernel(key, value=None):
    """(Very) partial implementation of sysctl, for kernel params"""
    if value is not None:
        # write
        utils.write_one_line('/proc/sys/kernel/%s' % key, str(value))
    else:
        # read
        out = utils.read_one_line('/proc/sys/kernel/%s' % key)
        return int(re.search(r'\d+', out).group(0))


def _convert_exit_status(sts):
    if os.WIFSIGNALED(sts):
        return -os.WTERMSIG(sts)
    elif os.WIFEXITED(sts):
        return os.WEXITSTATUS(sts)
    else:
        # impossible?
        raise RuntimeError("Unknown exit status %d!" % sts)


def where_art_thy_filehandles():
    """Dump the current list of filehandles"""
    os.system("ls -l /proc/%d/fd >> /dev/tty" % os.getpid())


def print_to_tty(string):
    """Output string straight to the tty"""
    open('/dev/tty', 'w').write(string + '\n')


def dump_object(object):
    """Dump an object's attributes and methods

    kind of like dir()
    """
    for item in object.__dict__.items():
        print(item)
        try:
            (key, value) = item
            dump_object(value)
        except Exception:
            continue


def environ(env_key):
    """return the requested environment variable, or '' if unset"""
    if (env_key in os.environ):
        return os.environ[env_key]
    else:
        return ''


def prepend_path(newpath, oldpath):
    """prepend newpath to oldpath"""
    if (oldpath):
        return newpath + ':' + oldpath
    else:
        return newpath


def append_path(oldpath, newpath):
    """append newpath to oldpath"""
    if (oldpath):
        return oldpath + ':' + newpath
    else:
        return newpath


def avgtime_print(dir):
    """ Calculate some benchmarking statistics.
        Input is a directory containing a file called 'time'.
        File contains one-per-line results of /usr/bin/time.
        Output is average Elapsed, User, and System time in seconds,
          and average CPU percentage.
    """
    f = open(dir + "/time")
    user = system = elapsed = cpu = count = 0
    r = re.compile('([\d\.]*)user ([\d\.]*)system (\d*):([\d\.]*)elapsed (\d*)%CPU')
    for line in f.readlines():
        try:
            s = r.match(line)
            user += float(s.group(1))
            system += float(s.group(2))
            elapsed += (float(s.group(3)) * 60) + float(s.group(4))
            cpu += float(s.group(5))
            count += 1
        except Exception:
            raise ValueError("badly formatted times")

    f.close()
    return "Elapsed: %0.2fs User: %0.2fs System: %0.2fs CPU: %0.0f%%" % \
        (elapsed / count, user / count, system / count, cpu / count)


def running_config():
    """
    Return path of config file of the currently running kernel
    """
    version = os.uname()[2]
    for config in ('/proc/config.gz',
                   '/boot/config-%s' % version,
                   '/lib/modules/%s/build/.config' % version):
        if os.path.isfile(config):
            return config
    return None


def check_for_kernel_feature(feature):
    config = running_config()

    if not config:
        raise TypeError("Can't find kernel config file")

    if magic.guess_type(config) == 'application/x-gzip':
        grep = 'zgrep'
    else:
        grep = 'grep'
    grep += ' ^CONFIG_%s= %s' % (feature, config)

    if not utils.system_output(grep, ignore_status=True):
        raise ValueError("Kernel doesn't have a %s feature" % (feature))


#def cpu_online_map():
  #  """
 ##   Check out the available cpu online map
  #  """
 #   cpus = []
  #  for line in open('/proc/cpuinfo', 'r').readlines():
 #       if line.startswith('processor'):
 #           cpus.append(line.split()[2])  # grab cpu number
 #   return cpus


#def check_glibc_ver(ver):
#    glibc_ver = subprocess.getoutput('ldd --version').splitlines()[0]
#    glibc_ver = re.search(r'(\d+\.\d+(\.\d+)?)', glibc_ver).group()
#    if utils.compare_versions(glibc_ver, ver) == -1:
#        raise error.TestError("Glibc too old (%s). Glibc >= %s is needed." %
#                              (glibc_ver, ver))

def check_glibc_ver1():
    glibc_ver = subprocess.getoutput('ldd --version').splitlines()[0]
    glibc_ver = re.search(r'(\d+\.\d+(\.\d+)?)', glibc_ver).group()
    return glibc_ver


def check_kernel_ver(ver):
    kernel_ver = os.uname()[2]
    kv_tmp = re.split(r'[-]', kernel_ver)[0:3]
    # In compare_versions, if v1 < v2, return value == -1
    if utils.compare_versions(kv_tmp[0], ver) == -1:
        raise error.TestError("Kernel too old (%s). Kernel > %s is needed." %
                              (kernel_ver, ver))


def human_format(number):
    # Convert number to kilo / mega / giga format.
    if number < 1024:
        return "%d" % number
    kilo = float(number) / 1024
    if kilo < 1024:
        return "%.2fkiB" % kilo
    meg = kilo / 1024.0
    if meg < 1024:
        return "%.2fMiB" % meg
    gig = meg / 1024
    return "%.2fGiB" % gig


def to_seconds(time_string):
    """Converts a string in M+:SS.SS format to S+.SS"""
    elts = time_string.split(':')
    if len(elts) == 1:
        return time_string
    return str(int(elts[0]) * 60 + float(elts[1]))


def extract_all_time_results(results_string):
    """Extract user, system, and elapsed times into a list of tuples"""
    pattern = re.compile(r"(.*?)user (.*?)system (.*?)elapsed")
    results = []
    for result in pattern.findall(results_string):
        results.append(tuple([to_seconds(elt) for elt in result]))
    return results


def pickle_load(filename):
    return pickle.load(open(filename, 'r'))


# Return the kernel version and build timestamp.
def running_os_release():
    return os.uname()[2:4]


def running_os_ident():
    (version, timestamp) = running_os_release()
    return version + '::' + timestamp


def running_os_full_version():
    (version, timestamp) = running_os_release()
    return version


# much like find . -name 'pattern'
def locate(pattern, root=os.getcwd()):
    for path, dirs, files in os.walk(root):
        for f in files:
            if fnmatch.fnmatch(f, pattern):
                yield os.path.abspath(os.path.join(path, f))


def freespace(path):
    """Return the disk free space, in bytes"""
    s = os.statvfs(path)
    return s.f_bavail * s.f_bsize


def disk_block_size(path):
    """Return the disk block size, in bytes"""
    return os.statvfs(path).f_bsize


def get_cpu_family():
    procinfo = utils.system_output('cat /proc/cpuinfo')
    CPU_FAMILY_RE = re.compile(r'^cpu family\s+:\s+(\S+)', re.M)
    matches = CPU_FAMILY_RE.findall(procinfo)
    if matches:
        return int(matches[0])
    else:
        raise error.TestError('Could not get valid cpu family data')


def get_disks():
    df_output = utils.system_output('df')
    disk_re = re.compile(r'^(/dev/hd[a-z]+)3', re.M)
    return disk_re.findall(df_output)


def load_module(module_name):
    # Checks if a module has already been loaded
    if module_is_loaded(module_name):
        return False

    utils.system('/sbin/modprobe ' + module_name)
    return True


def unload_module(module_name):
    """
    Removes a module. Handles dependencies. If even then it's not possible
    to remove one of the modules, it will trhow an error.CmdError exception.

    :param module_name: Name of the module we want to remove.
    """
    l_raw = utils.system_output("/sbin/lsmod").splitlines()
    lsmod = [x for x in l_raw if x.split()[0] == module_name]
    if len(lsmod) > 0:
        line_parts = lsmod[0].split()
        if len(line_parts) == 4:
            submodules = line_parts[3].split(",")
            for submodule in submodules:
                unload_module(submodule)
        utils.system("/sbin/modprobe -r %s" % module_name)
        logging.info("Module %s unloaded" % module_name)
    else:
        logging.info("Module %s is already unloaded" % module_name)


def module_is_loaded(module_name):
    module_name = module_name.replace('-', '_')
    modules = utils.system_output('/sbin/lsmod').splitlines()
    for module in modules:
        if module.startswith(module_name) and module[len(module_name)] == ' ':
            return True
    return False


def get_loaded_modules():
    lsmod_output = utils.system_output('/sbin/lsmod').splitlines()[1:]
    return [line.split(None, 1)[0] for line in lsmod_output]


def get_cpu_vendor():
    cpuinfo = open('/proc/cpuinfo').read()
    vendors = re.findall(r'(?m)^vendor_id\s*:\s*(\S+)\s*$', cpuinfo)
    #for i in xrange(1, len(vendors)):
   #     if vendors[i] != vendors[0]:
    #        raise error.TestError('multiple cpu vendors found: ' + str(vendors))
    return vendors[0]


def ping_default_gateway():
    """Ping the default gateway."""

    network = open('/etc/sysconfig/network')
    m = re.search('GATEWAY=(\S+)', network.read())

    if m:
        gw = m.group(1)
        cmd = 'ping %s -c 5 > /dev/null' % gw
        return utils.system(cmd, ignore_status=True)

    raise error.TestError('Unable to find default gateway')


def process_is_alive(name_pattern):
    """
    'pgrep name' misses all python processes and also long process names.
    'pgrep -f name' gets all shell commands with name in args.
    So look only for command whose initial pathname ends with name.
    Name itself is an egrep pattern, so it can use | etc for variations.
    """
    return utils.system("pgrep -f '^([^ /]*/)*(%s)([ ]|$)'" % name_pattern,
                        ignore_status=True) == 0


def get_hwclock_seconds(utc=True):
    """
    Return the hardware clock in seconds as a floating point value.
    Use Coordinated Universal Time if utc is True, local time otherwise.
    Raise a ValueError if unable to read the hardware clock.
    """
    cmd = '/sbin/hwclock --debug'
    if utc:
        cmd += ' --utc'
    hwclock_output = utils.system_output(cmd, ignore_status=True)
    match = re.search(r'= ([0-9]+) seconds since .+ (-?[0-9.]+) seconds$',
                      hwclock_output, re.DOTALL)
    if match:
        seconds = int(match.group(1)) + float(match.group(2))
        logging.debug('hwclock seconds = %f' % seconds)
        return seconds

    raise ValueError('Unable to read the hardware clock -- ' +
                     hwclock_output)


def set_wake_alarm(alarm_time):
    """
    Set the hardware RTC-based wake alarm to 'alarm_time'.
    """
    utils.write_one_line('/sys/class/rtc/rtc0/wakealarm', str(alarm_time))


def set_power_state(state):
    """
    Set the system power state to 'state'.
    """
    utils.write_one_line('/sys/power/state', state)


def standby():
    """
    Power-on suspend (S1)
    """
    set_power_state('standby')


def suspend_to_ram():
    """
    Suspend the system to RAM (S3)
    """
    set_power_state('mem')


def suspend_to_disk():
    """
    Suspend the system to disk (S4)
    """
    set_power_state('disk')


def get_cpu_stat(key):
    """
    Get load per cpu from /proc/stat
    :return: list of values of CPU times
    """

    stats = []
    stat_file = open('/proc/stat', 'r')
    line = stat_file.readline()
    while line:
        if line.startswith(key):
            stats = line.split()[1:]
            break
        line = stat_file.readline()
    return stats


def get_uptime():
    """
    :return: return the uptime of system in secs in float
    in error case return 'None'
    """

    cmd = "/bin/cat /proc/uptime"
    (status, output) = subprocess.getstatusoutput(cmd)
    if status == 0:
        return output.split()[0]
    else:
        return None

def read_cpuinfo(match):
    '''  match must include two group
    return (name, value)'''
    cpuinfo = open('/proc/cpuinfo').read()
    re_match = re.findall(r'%s' %match, cpuinfo, re.I)
    if re_match:
        return re_match[-1]
    else:
        return ("N/A", "N/A")

def get_physicalCPU():
    try:
        num = int(read_cpuinfo('(physical\s+id)\s+:\s+(\S+)')[1]) + 1
        return str(num)
    except Exception:
        return "N/A"

def read_meminfo(match):
    meminfo = open('/proc/meminfo').read()
    re_match = re.findall(r'%s' % match, meminfo, re.I)
    if re_match:
        return re_match[-1]
    else:
        return ("N/A", "N/A")
    
def read_hardinfo():
    '''return dict'''
    hdinfo = open('/proc/partitions').readlines()[2:]
    partinfo = [line.split()[-1] for line in hdinfo]
    return " ".join(partinfo)


def get_RootFilesystem():
    '''return
    Filesystem     Type   Size  Used Avail Use% Mounted on
    '''
    try:
        output = utils.system_output('df -lhT|grep "/$"')
        return tuple(output.split())
    except Exception:
        return ("N/A","N/A","N/A","N/A","N/A","N/A","N/A")

def get_gccVersion():
    try:
        #output = utils.system_output('java -version')
        output = subprocess.getoutput("gcc -v")
        return output.split("\n")[-1]
    except Exception:
        return "N/A"

def get_javaVersion():
    try:
        #output = utils.system_output('java -version')
        output = subprocess.getoutput("java -version")
        return (output.split("\n")[0], output.split("\n")[1], output.split("\n")[2])
    except Exception:
        return ("N/A","N/A","N/A")
    
def get_cmd_output(cmd):
    try:
        output = subprocess.getoutput(cmd)
        return output
    except Exception:
        return "N/A"
    
def get_iptables_status():
    if os.path.exists("/usr/lib/systemd"):
        if os.path.isfile("/run/lock/sub/sys/iptables"):
            return "on"
        else:
            return "off"
    else:
        if os.path.isfile("/etc/sysconfig/iptables"):
            return "on"
        else:
            return "off"
        
def get_services():
    if os.path.exists("/usr/lib/systemd"):
        try:
            output = utils.system_output("systemctl -t service list-unit-files|grep enabled|awk  '{print $1}'")
            return ",".join(output.split())
        except Exception:
            return "N/A"
    else:
        try:
            output = utils.system_output("chkconfig  --list|grep -E '(5:启用|5:on)'|awk '{print $1}'")
            return ",".join(output.split())
        except Exception:
            return "N/A"
    
def get_OSRelease():
    try:
        status, output = subprocess.getstatusoutput("cat /etc/*-release")
        if status >0:
            return "N/A"
        else:
            return output.split("\n")[-1]
    except Exception:
        return "N/A"
   
def get_OSBuild():
    try:
        status ,output = subprocess.getstatusoutput("cat /etc/os-version")
        if status >0:
            return "N/A"
        else:
            return output.split("=")[-1]
    except Exception:
        return "N/A"

    
class OSInfo(object):
    '''get OS infor'''
    keys = { 
            "CpuVendor":get_cmd_output("cat /proc/cpuinfo |grep -i vendor_id |head -n 1 |awk '{print $NF}'"),
            "CpuModel":get_cmd_output("cat /proc/cpuinfo |grep -i model |head -n 1 |awk -F ':' '{print $2}'"),
            "CpuMhz":get_cmd_output("cat /proc/cpuinfo |grep -i MHz |head -n 1 |awk '{print $NF}'"),
            "Processor":platform.processor(),
            "Arch":" ".join(platform.architecture()),
            "BogoMIPS":read_cpuinfo('(bogomips)\s+:\s+(\S+)')[1],
            "PhysicalCpu":get_physicalCPU(),
            "CpuCores":"%d" % count_cpus(),
            "LogicCpu":"%d" % count_cpus(),
            "MemModel":"N/A",
            "MemMhz":"N/A",
            "MemTotal":"%s KiB" % read_meminfo('(MemTotal):\s+(\d+)')[1],
            "SwapTotal":"%s KiB" % read_meminfo('(SwapTotal):\s+(\d+)')[1],
            "Shmem":"%s KiB" % read_meminfo('(Shmem):\s+(\d+)')[1],
            "VmallocTotal":"%s KiB" % read_meminfo('(VmallocTotal):\s+(\d+)')[1],
            "Hugepagesize":"%s KiB" % read_meminfo('(Hugepagesize):\s+(\d+)')[1],
            
            "DiskInfo":read_hardinfo(),
            "DiskSize":"N/A",
            
            "CardModel":"N/A",
            "speed":"N/A",
            #"IP" :get_host_ip(),
            
            #"Platform":platform.platform(),
            "Release":get_OSRelease(),
            "Build":get_OSBuild(),
            "Kernel":platform.release(),
            #"OS": get_cmd_output("cat /etc/os-release").replace("\n", " "),
            "OS": get_cmd_output("cat /etc/issue.net").replace("\n", " "),
            "Version":platform.version(),
            "Filesystem":get_RootFilesystem()[0],
            "FilesystemType":get_RootFilesystem()[1],
            "FilesystemSize":get_RootFilesystem()[2],
            "Gcc":get_gccVersion(),
            #"Glibc":" ".join(platform.libc_ver()),
            "Glibc":check_glibc_ver1(), 
            "JavaVersion": get_javaVersion()[0],
            "JavaBuild": get_javaVersion()[1],
            "JavaMode": get_javaVersion()[2],
            "Python":platform.python_version(),
             
             "RpmNums":get_cmd_output("rpm -qa|wc -l"),
             "Runlevel":get_cmd_output("runlevel"),
             "Servers":get_services(),
             "IPtables":get_iptables_status(),
             "SELinux":get_cmd_output("getenforce"),
             "IOSchedule":"N/A",
             "KernelCmd":get_cmd_output("cat /proc/cmdline")

                  }
    
    info_keys = {
                 "CPU":["CpuVendor", "CpuModel", "CpuMhz", "Processor", "Arch", "PhysicalCpu", "CpuCores", "LogicCpu", "BogoMIPS"],
                 "Mem":["MemModel", "MemMhz", "MemTotal", "SwapTotal",  "Shmem", "VmallocTotal",  "Hugepagesize"],
                 "Disk":["DiskInfo", "DiskSize"],
                 "Network":["CardModel", "speed"],
                 "OS": [ "Release", 'Build', "Kernel", "OS", "Version",  "KernelCmd", "Runlevel", "IOSchedule",
                        "Filesystem", "FilesystemType","FilesystemSize", 
                        "Gcc", "Glibc", "JavaVersion", "JavaBuild", "JavaMode", "Python",
                        "RpmNums", "IPtables", "SELinux", "Servers"],
                     }
    type_keys = ["CPU", "Mem", "Disk", "Network", "OS"]
    
    def __setitem__(self, item, value):
        if item in self.keys:
            self.keys[item] = value
            
    def __getitem__(self, item):
        if item in self.keys:
            return self.keys[item]
        
    def get_type_keys(self, type):
        '''type = CPU、Mem、OS、Hard'''
        if type in self.type_keys:
            return self.type_keys[type]
