#encoding=utf-8
import sys, time, os, random
from socket import *
from Xor import *
from choose_data import *
from multiprocessing import *
from config import *

send_num = 0

# 发送进程函数
def send(Dest_ADDR, subsection_num, sockfd):
    print("发送记录的条数: ", subsection_num)
    # 根据分段的个数k, 确定度的概率分布
    for i in range(3):
        time.sleep(1)
        print("%ds 后开始发送数据" % (3-i))

    t_begin = time.time()
    for msg in get_bytesList_of_a_generation(subsection_num):
        for neighbor in Dest_ADDR:
                    send_with_loss_prob(sockfd, msg, neighbor)
                    print(msg, " --> ", neighbor)
                    time.sleep(send_delay)
            
    t_end = time.time()
    print("\n---------------------------\n发送完成!\n\n")
    print("共用时: %lf 秒" % (t_end - t_begin))



def main():
    # 创建套接字
    sockfd = socket(AF_INET, SOCK_DGRAM)
    # 设置端口立即释放
    sockfd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    # 绑定自身地址和端口号
    sockfd.bind(source_ADDR)


    # 在某一条件下一直以一代数据为单位,向转发层发送
    while True:
        # 定义ack校验子进程
        p_send = Process(target=send, args=(Dest_ADDR, subsection_num, sockfd))

        # 开启发送进程
        p_send.start()

        # 等待子进程执行结束再执行之后的代码
        p_send.join()

        # 暂时只发送一代,所以break退出循环
        break

    sockfd.close()



if __name__ == '__main__':
    main()


