# -*- coding:utf-8 -*-

lm_basic = ( 'Mhz', 'tlb', 'line_size', 'mem_load_par', "scal_load" )
lm_process = ('lat_syscall', 'lat_io', 'lat_stat', 'lat_openclose', 'lat_tcp_select',
              'lat_siginstall', 'lat_sigcatch','lat_nullproc', 'lat_simpleproc', 'lat_shproc' )
lm_int = ( 'integer_bit', 'integer_add','integer_mul', 'integer_div','integer_mod' )
lm_int64  = ( 'int64_bit', 'int64_add','int64_mul', 'int64_div','int64_mod' )
lm_float =  ( 'float_add', 'float_mul', 'float_div', 'float_bogomflops' )
lm_double = ( 'double_add', 'double_mul', 'double_div','double_bogomflops' )
lm_ctx = ( 'lat_ctx0_2', 'lat_ctx16_2','lat_ctx64_2', 'lat_ctx16_8',
            'lat_ctx64_8', 'lat_ctx16_16','lat_ctx64_16' )
lm_ipc_local = ( 'lat_ctx0_2', 'lat_pipe','lat_unix', 'lat_udp_local',
            'lat_rpc_udp_local', 'lat_tcp_local','lat_rpc_tcp_local', 'lat_tcp_connect_local' )
lm_file_vm = ('fs_create_0k', 'fs_create_10k','fs_delete_0k', 'fs_delete_10k', 
              'lat_mappings', 'lat_protfault','lat_pagefault', "lat_fd_select" )
lm_bw_ipc_local = ( 'bw_pipe', 'bw_unix', 'bw_tcp_local', 'bw_reread', "bw_mmap",
                    'bw_bcopy_libc', 'bw_bcopy_unrolled','bw_mem_rdsum' , 'bw_mem_wr' )
lm_mem = ( 'lat_l1', 'lat_l2', 'lat_mem', "lat_mem_rand" )  
lm_keys = (lm_basic, lm_process, lm_int, lm_int64, lm_float, 
                lm_double, lm_ctx, lm_ipc_local, lm_file_vm, 
                lm_bw_ipc_local, lm_mem)

des = ("Basic system parameters", 
          "Processor, Processes - times in microseconds - smaller is better",
          "Basic integer operations - times in nanoseconds - smaller is better",
          "Basic uint64 operations - times in nanoseconds - smaller is better",
          "Basic float operations - times in nanoseconds - smaller is better",
          "Basic double operations - times in nanoseconds - smaller is better",
          "Context switching - times in microseconds - smaller is better",
          "*Local* Communication latencies in microseconds - smaller is better",
          "File & VM system latencies in microseconds - smaller is better",
          "*Local* Communication bandwidths in MB/s - bigger is better",
          "Memory latencies in nanoseconds - smaller is better")    
title_basic = ("Mhz", "tlb pages", "cache line bytes", "mem par", "scal load")
title_process = ("null call", "null I/O", "stat", "open clos", 
                "slct TCP", "sig inst", "sig hndl", "fork proc", "exec proc", "sh proc")
title_int = ("intgr bit", "intgr add", "intgr mul", "intgr div", "intgr mod")
title_int64 = ("int64bit", "int64 add", "int64 mul", "int64 div", "int64 mod")
title_float=("float add", "float mul", "float div", "float bogo")
title_double=('double add', "double mul", "double div", "double bogo")
title_ctx = ("2p/0k ctxsw","2p/16k ctxsw", "2p/64k ctxsw", 
             "8p/16k ctxsw", "8p/64k ctxsw", "16p/16k ctxsw", "16p/64k ctxsw")
title_ipc_local=("2p/0k ctxsw", "Pipe", "AF UNIX", "UDP", "RPC/UDP", "TCP", "RPC/TCP", "TCP conn")
title_file_vm=("0K File Create", "0K File Delete", "10K File Create", "10K File Delete",
               "Mmap Latency", "Prot Fault", "Page Fault", "100fd selct")
title_bw_ipc_local=("Pipe", "AF UNIX", "TCP", "File reread", "Mmap reread",
                    "Bcopy(libc)", "Bcopy(hand)", "Mem read", "Mem write")
title_mem = ("L1 $", "L2 $", "Main mem", "Rand mem")

#需要存储的测试数据

title_keys=(title_basic, title_process, title_int, title_int64, 
            title_float, title_double, title_ctx, title_ipc_local, 
            title_file_vm, title_bw_ipc_local, title_mem)

lmbench_keys=(des, lm_keys, title_keys)

def get_index_list():
    index_list = []
    for key in lm_keys[1:]:
        index_list = index_list+list(key)

    return index_list

class LmbenchData:
    '''get lmbench data'''
    def __init__(self, file, times, parallels):
        self.file = file
        self.times = times
        self.parallels = parallels
        self.lines = self._get_lines()
    
    def _get_lines(self):
        fp = open(self.file, "r")
        return fp.readlines()
    
    def _set_float_formt(self, value):
        value_split = str(value).split(".")
        if len(value_split) == 2:
            if len(value_split[0]) >=4:
                return "%d" % float(value)
            elif len(value_split[0]) == 3:
                return "%3.1f" % float(value)
            elif len(value_split[0]) ==2:
                return "%2.2f" % float(value)
            else:
                return "%1.3f" % float(value)
        else:
            return "%s" % value
        
    def get_basic(self):
        basic_dic = {}
        basic_index = self.lines.index(des[0]+"\n") + 6
        for l,v in zip(lm_basic, tuple(self.lines[basic_index].split()[-5:])):
            basic_dic[l] = v
        return basic_dic
    
    def _append_sum_dict(self, sum_dict, result_dict):
        for key in sum_dict.keys():
            sum_dict[key] = self._set_float_formt(float(sum_dict[key]) + float(result_dict[key]))
        return sum_dict
    
    def _append_average_dict(self, sum_dict):
        average_dict = {}
        for key in sum_dict.keys():
            average_dict[key] = self._set_float_formt(float(sum_dict[key])/self.times)
        return average_dict

            
    def get_data(self, attrib={}):
        results_list = []
        sum_dic={}
        for iter in range(self.times):
            iter_dic = {}
            for lm_des in lmbench_keys[0][1:]:
                lm_index = self.lines.index(lm_des+"\n") + 5
                iter_index = lm_index + iter
                #get lm_des index of des and it is the index of lm_keys
                des_index = des.index(lm_des)
                #get the keys of lm_keys by des_index 
                lm_index_keys = lm_keys[des_index]
                for l,v in  zip(lm_index_keys, tuple(self.lines[iter_index].split()[-len(lm_index_keys):])):
                    iter_dic[l] = self._set_float_formt(v)
            if not sum_dic:
                sum_dic = iter_dic.copy()
            else:
                sum_dic = self._append_sum_dict(sum_dic, iter_dic)
            results_list.append([dict({"iter":str(iter+1), "times":str(self.times),  "parallels":str(self.parallels), "parallel":str(self.parallels)}, 
                                        **attrib), iter_dic])
        if sum_dic:
            parallel_average_dic = self._append_average_dict(sum_dic)
            results_list.append([dict({"iter":"Average", "times":str(self.times),  "parallels":str(self.parallels), "parallel":str(self.parallels)}, 
                                        **attrib), parallel_average_dic]) 
        return results_list
                