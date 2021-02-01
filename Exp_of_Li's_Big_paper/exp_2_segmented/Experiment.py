import multiprocessing.pool
import sys
import time
import forward
import source
from config import *
from multiprocessing import Process
cfg = Config()


class NoDaemonProcess(multiprocessing.Process):

    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)


class MyPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess


def run(min_unit, T_slot, a, b, c, pieces_each_round, exp_index, runType):
    if runType == -1: # 自动化方式
        pool = MyPool(15)
        for ip, port in cfg.Dest_ADDR:
            pool.apply_async(func=forward.main, args=(ip, port, min_unit, T_slot, a, b, c, pieces_each_round, exp_index))  # 转发
    
        time.sleep(3)
        send_num = pool.apply_async(func=source.main, args=(min_unit, pieces_each_round, exp_index))  # 源
    
        pool.close()
    
        print("wait process to join...")
        pool.join()
        print("process joined")
        return send_num.get()


    # 源节点单独运行
    elif runType == 0:
        p_source = Process(target=source.main, args=(min_unit, pieces_each_round, exp_index))
        p_source.start()
        p_source.join()
        
        
    # 转发层节点单独运行
    elif len(sys.argv) == 3 and sys.argv[1] == 'forward':
        forward_index = int(sys.argv[2])
        ip, port = cfg.Dest_ADDR[forward_index-1]
        p_forward = Process(target=forward.main, args=(ip, port, min_unit, T_slot, a, b, c, pieces_each_round, exp_index))
        p_forward.start()
        p_forward.join()
    else:
        raise Exception("出现未知错误!!!!")
    
    # 需要返回:
    # 1.源节点发送的总轮次
    # 2.系统运行时间
    # 3.节点从源节点接收到的数据个数
    # 4.节点从转发层节点接收到的个数
    # 5.源节点发送轮次-节点已解码个数 关系

