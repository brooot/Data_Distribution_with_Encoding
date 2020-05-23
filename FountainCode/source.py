#encoding=utf-8
import sys, time, os, random
from socket import *
from Xor import *
from choose_data import *
from multiprocessing import *
from config import *

# ack 校验进程函数
def check_ack(still_need_sending, sockfd, ack_neighbor, Dest_ADDR):
        while still_need_sending.value:
            data, addr = sockfd.recvfrom(1024)
            if data.decode() == "ok":
                print("\n---------------------------\n收到",addr,"的ack\n---------------------------\n")
                if addr not in ack_neighbor:
                    ack_neighbor.append(addr)
                    if len(ack_neighbor) == len(Dest_ADDR):
                        still_need_sending.value = False
                sockfd.sendto("got_it".encode(),addr)
            
            else:
                print("主机 %s 发来消息：%s" % (addr, data.decode()))

# 发送进程函数
def send(still_need_sending, ack_neighbor, Dest_ADDR, subsection_num, send_delay, sockfd):
    print("发送分段大小为: ", subsection_num)
    # 根据分段的个数k, 确定度的概率分布
    p = get_degree_distribution(subsection_num)
    for i in range(3):
        time.sleep(1)
        print("%ds 后开始发送数据" % (3-i))
    t_begin = time.time()
    send_num = 0
    while still_need_sending.value:
        for neighbor in Dest_ADDR:
            if len(ack_neighbor) < len(Dest_ADDR) :
                if neighbor not in ack_neighbor:
                    encoded_Data = get_encoded_data(subsection_num, p)
                    send_num += 1
                    time.sleep(send_delay)
                    sockfd.sendto(encoded_Data, neighbor)
            else:
                break
    t_end = time.time()
    print("\n---------------------------\n接收方已经全部解码完成!\n\n")
    print("共用时: %lf 秒" % (t_end - t_begin))
    print("共发送了 %d 个数据" % send_num)





def main():
    # 创建套接字
    sockfd = socket(AF_INET, SOCK_DGRAM)

    # 设置id地址和端口号

    IP = "10.1.18.29"
    PORT = 6630

    self_ADDR = (IP, PORT)
    # 绑定自身地址和端口号
    sockfd.bind(self_ADDR)

    # 在某一条件下一直以一代数据为单位,向转发层发送喷泉码
    while True:
        
        # 记录已经确认解码的邻居的列表
        ack_neighbor = Manager().list()
        # 记录是否还需要发送数据
        still_need_sending = Value('i', True)
        
        # 定义ack校验子进程
        p_send = Process(target=send, args=(still_need_sending, ack_neighbor, Dest_ADDR, subsection_num, send_delay, sockfd))
        # 定义发送子进程
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

