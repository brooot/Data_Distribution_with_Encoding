
#encoding=utf-8
import sys, time, os, random
from socket import *
from Xor import *
from  choose_data import *
from multiprocessing import *
from config import *

# ack 校验进程函数   ack_neighbor是一个进程间全局消息  负责接收转发层的ack
def check_ack(still_need_sending, sockfd, ack_neighbor, Dest_ADDR):
        while still_need_sending.value:
            data, addr = sockfd.recvfrom(1024)
            if data.decode() == "ok":
                sockfd.sendto("got_it".encode(), addr)
                print("\n---------------------------\n收到",addr,"的ack\n---------------------------\n")
                if addr not in ack_neighbor:
                    ack_neighbor.append(addr)
                if len(ack_neighbor) == len(Dest_ADDR):
                    still_need_sending.value = False
                    for sendAddr in Dest_ADDR:
                        sockfd.sendto("stop_all".encode(), sendAddr)
                    break
                
            else:
                print("主机 %s 发来消息：%s" % (addr, data.decode()))

# 发送进程函数
def send(still_need_sending, ack_neighbor, Dest_ADDR, subsection_num, sockfd):
    print("发送分段大小为: ", subsection_num)
    # 根据分段的个数k, 确定度的概率分布
    p = get_Bit_distribution(subsection_num)
    for i in range(3):
        time.sleep(1)
        print("%ds 后开始发送数据" % (3-i))
    t_begin = time.time()
    send_num = 0
    while still_need_sending.value:
        for neighbor in Dest_ADDR:
            if len(ack_neighbor) < len(Dest_ADDR) :
                if neighbor not in ack_neighbor:
                    #这个方法在choose_data里
                    #度时刻转换序列
                    # 度分布函数
                    # encoded_Data = get_encoded_data_sort(subsection_num, p,send_num,len(Dest_ADDR))
                    encoded_Data = get_encoded_data(subsection_num, p)
                    send_num += 1
                    send_with_loss_prob(sockfd, encoded_Data, neighbor)
                    time.sleep(send_delay)
            else:
                break
    t_end = time.time()
    print("\n---------------------------\n接收方已经全部解码完成!\n\n")
    print("共用时: %lf 秒" % (t_end - t_begin))
    print("共发送了 %d 个数据" % send_num)

# Socket 具有三大属性：域、类型、协议。
# 域：AF_UNIX（Unix 文件系统，地址为文件名，对应文件 IO） 和 AF_INET（Internet 网络，常用）两类
# 类型：SOCK_STREAM（流，对应 TCP） 和 SOCK_DGRAM（数据报，对应 UDP）
# 协议：只要底层的传输机制允许不止一个协议来提供要求的套接字类型，
# 我们就可以为套接字选择一个特定的协议。通常只需要使用默认值 0。

def main():
    # 创建套接字 这里对应的网络和UDP协议
    sockfd = socket(AF_INET, SOCK_DGRAM)

    # source_ADDR 在 config.py 中
    self_ADDR = source_ADDR

    # 绑定自身地址和端口号
    sockfd.bind(self_ADDR)
   
    # 在某一条件下一直以一代数据为单位,向转发层发送喷泉码
    while True:
        # 记录已经确认解码的邻居的列表   多进程共享全局变量
        ack_neighbor = Manager().list()
        # 记录是否还需要发送数据   多进程间共享全局变量
        still_need_sending = Value('i', True)
        
        # 定义发送子进程
        p_send = Process(target=send, args=(still_need_sending, ack_neighbor, Dest_ADDR, subsection_num, sockfd))
        # 定义ack校验子进程  subsection_num, send_delay这两个参数都是在config文件中的  sockfd是UDP套接字
        p_check_ack = Process(target=check_ack, args=(still_need_sending, sockfd, ack_neighbor, Dest_ADDR))
        
        # 开启ack校验进程
        p_check_ack.start()
        # 开启发送进程
        p_send.start()

        # 等待两个子进程执行结束再执行之后的代码
        p_send.join()
        p_check_ack.join()

        # 暂时只发送一代,所以break退出循环
        break

    sockfd.close()


if __name__ == '__main__':
    main()

