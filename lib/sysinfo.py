# -*- coding:utf-8 -*-
'''
    @summary: 获取操作系统软、硬件信息
'''

import os
from lpt.lib.share import utils
import platform

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

    
def get_os_vendor():
    """
    Try to guess what's the os vendor.
    """
    logging.warn('utils.get_os_vendor() is deprecated, please use '
                 'autotest.client.shared.distro.detect() instead')

    vendor = 'Unknown'
    if os.path.isfile('/etc/SuSE-release'):
        return 'SUSE'

    issue = '/etc/issue'

    if not os.path.isfile(issue):
        return vendor

    if file_contains_pattern(issue, 'Red Hat'):
        vendor = 'Red Hat'
    if file_contains_pattern(issue, 'CentOS'):
        vendor = 'Red Hat'
    elif file_contains_pattern(issue, 'Fedora'):
        vendor = 'Fedora'
    elif file_contains_pattern(issue, 'SUSE'):
        vendor = 'SUSE'
    elif file_contains_pattern(issue, 'Ubuntu'):
        vendor = 'Ubuntu'
    elif file_contains_pattern(issue, 'Debian'):
        vendor = 'Debian'

    logging.debug("Detected OS vendor: %s", vendor)
    return vendor


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
        'power7': ("POWER7", )
    }

    cpu_info = get_cpu_info()
    for vendor, identifiers in vendors_map.items():
        for identifier in identifiers:
            if list_grep(cpu_info, identifier):
                return vendor
    return None


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
    file_data = system_output('file -L ' + filename)
    if file_data.count('80386'):
        return 'i386'
    return None


def count_cpus():
    """number of CPUs in the local machine according to /proc/cpuinfo"""
    f = file('/proc/cpuinfo', 'r')
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
    for item in object.__dict__.iteritems():
        print item
        try:
            (key, value) = item
            dump_object(value)
        except Exception:
            continue


def environ(env_key):
    """return the requested environment variable, or '' if unset"""
    if (os.environ.has_key(env_key)):
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


def cpu_online_map():
    """
    Check out the available cpu online map
    """
    cpus = []
    for line in open('/proc/cpuinfo', 'r').readlines():
        if line.startswith('processor'):
            cpus.append(line.split()[2])  # grab cpu number
    return cpus


def check_glibc_ver(ver):
    glibc_ver = commands.getoutput('ldd --version').splitlines()[0]
    glibc_ver = re.search(r'(\d+\.\d+(\.\d+)?)', glibc_ver).group()
    if utils.compare_versions(glibc_ver, ver) == -1:
        raise error.TestError("Glibc too old (%s). Glibc >= %s is needed." %
                              (glibc_ver, ver))


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
    kilo = float(number) / 1024.0
    if kilo < 1024:
        return "%.2fk" % kilo
    meg = kilo / 1024.0
    if meg < 1024:
        return "%.2fM" % meg
    gig = meg / 1024.0
    return "%.2fG" % gig


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
    for i in xrange(1, len(vendors)):
        if vendors[i] != vendors[0]:
            raise error.TestError('multiple cpu vendors found: ' + str(vendors))
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
    (status, output) = commands.getstatusoutput(cmd)
    if status == 0:
        return output.split()[0]
    else:
        return None
