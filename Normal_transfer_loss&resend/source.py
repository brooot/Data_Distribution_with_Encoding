#encoding=utf-8
import sys, time, os, random
from socket import *
from Xor import *
from choose_data import *
from multiprocessing import *
from config import *



# 发送进程函数
def send(Dest_ADDR, subsection_num, send_delay, sockfd, L_msg):
    print("发送记录的条数: ", subsection_num)
    # 根据分段的个数k, 确定度的概率分布
    for i in range(3):
        time.sleep(1)
        print("%ds 后开始发送数据" % (3-i))
    t_begin = time.time()
    send_time = 1;
    for msg in L_msg:
        msg_index = L_msg.index(msg)
        # print(msg_index)
        for neighbor in Dest_ADDR:
            if random.random()<Channel_loss_probability: # 信道丢失率 为 0.3
                print("第%3d 次发送失败(丢失)" % send_time)
                send_time += 1
                continue
            else:
                print("第%3d 次发送成功" % send_time)
                send_time += 1
                time.sleep(send_delay)
                msg = (str(msg_index) + "&").encode() + msg  # 编号 + & + 数据
                # print(msg, neighbor)
                sockfd.sendto(msg, neighbor)

    # 通知邻居自己已经发送完成
    for nei in Dest_ADDR:
        sockfd.sendto("!".encode(), nei)
    print("\n-----------初次发送完毕-----------\n")
    # 给邻居拉取丢失信息的机会
    ack_neighbor = []
    still_need_sending = Value('i', True)
    while still_need_sending.value:
        data, addr = sockfd.recvfrom(1024)
        data = data.decode()
        if data == "ok":
            sockfd.sendto("got_it".encode(),addr)
            print("\n---------------------------\n收到",addr,"的ack\n---------------------------\n")
            if addr not in ack_neighbor:
                ack_neighbor.append(addr)
                if len(ack_neighbor) == len(Dest_ADDR):
                    still_need_sending.value = False
            
        # 接受端来拉取信息
        elif data[0] == "#": 
            send_index = int(data[1:])
            msg = L_msg[send_index]
            msg = (str(send_index) + "&").encode() + msg  # 编号 + & + 数据
            if random.random()<Channel_loss_probability: # 信道丢失率 为 0.3
                print(f"第%3d 次发送，丢失. 重发第{send_index}条信息给{addr}." % send_time)
                send_time += 1
                continue
            else:
                print(f"第%3d 次发送成功.   重发第{send_index}条信息给{addr}." % send_time)
                send_time += 1
                sockfd.sendto(msg, addr)

        else:
            print("主机 %s 发来消息：%s" % (addr, data.decode()))

            
    t_end = time.time()
    print("\n---------------------------\n发送完成!\n\n")
    print("共用时: %lf 秒" % (t_end - t_begin))


def main():
    # 创建套接字
    sockfd = socket(AF_INET, SOCK_DGRAM)
    # 设置端口立即释放
    sockfd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    # 设置ip地址和端口号
    IP = "127.0.0.1"
    PORT = 6661
    self_ADDR = (IP, PORT)
    # 绑定自身地址和端口号
    sockfd.bind(self_ADDR)


    

    # 在某一条件下一直以一代数据为单位,向转发层发送
    while True:
        # 获取要发送的数据
        L_msg = get_bytesList_of_a_generation(subsection_num)
        # 记录是否还需要发送数据
        still_need_sending = Value('i', True)

        # 定义ack校验子进程
        p_send = Process(target=send, args=(Dest_ADDR, subsection_num, send_delay, sockfd, L_msg))

        # p_resend = Process(target=resend, args=(still_need_sending, sockfd, Dest_ADDR, L_msg))

        # 开启发送进程
        p_send.start()

        # 等待子进程执行结束再执行之后的代码
        p_send.join()

        # 暂时只发送一代,所以break退出循环
        break

    sockfd.close()



if __name__ == '__main__':
    main()


