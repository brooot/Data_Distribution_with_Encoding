#!/usr/bin/env python3
#encoding=utf-8
from socket import *
from multiprocessing import *
from Xor import *
from config import *
import sys, random, os, time


# 发送ack
def send_ack(need_to_resend_ack, sockfd, addr):
    send_time = 1 # 第几次发送
    while need_to_resend_ack.value:
        # 向源端发送 ack
        send_message = "ok"
        print("第" + str(send_time) + "次 ",end='')
        print("向源端发送ack信息 ")
        sockfd.sendto(send_message.encode(), addr)
        if send_time == 1:
            time.sleep(0.5)
            send_time += 1
        else:
            send_time += 1
            time.sleep(1)


# 确认源端收到ack
def confirm_ack(need_to_resend_ack, sockfd, addr, recv_data, unrecvIndex_List):
    while need_to_resend_ack.value:
        data, address = sockfd.recvfrom(1024)
        data = data.decode()
        # print("收到", data)
        if addr == address and data == "got_it":
            print("发送方已经收到ack")
            need_to_resend_ack.value = False
        else:
            recv_msg = data.split("&")
            msg_index = int(recv_msg[0])
            if msg_index in unrecvIndex_List:
                unrecvIndex_List.remove(msg_index)
            print("unrecvIndex_List: ", unrecvIndex_List)
            msg_data = recv_msg[1].encode()
            recv_data[msg_index] = msg_data
            # print("com____recv_data:",recv_data.keys())

    print("\n------------------------\n一轮接收完成!\n")


def recv_from_source(sockfd, ADDR):
    
    recv_num = 0
    
    # 待写入文件的数据字典
    recv_data = Manager().dict()
    unrecvIndex_List = Manager().list()
    while True:
            # 接受数据(与tcp不同)
            data, addr = sockfd.recvfrom(1024)
            # print("收到", data.decode())
            if data.decode() == "!": # 结束接受
                source_addr = addr
                break
            recv_num += 1   
            recv_msg = data.decode().split("&")
            msg_index = int(recv_msg[0])
            msg_data = recv_msg[1].encode()
            recv_data[msg_index] = msg_data
            print("recv_data:",recv_data.keys())

    need_to_resend_ack = Value('i', True)

    p_send_ack = Process(target=send_ack, args=(need_to_resend_ack, sockfd, source_addr))
    p_confirm_ack = Process(target=confirm_ack, args=(need_to_resend_ack, sockfd, source_addr, recv_data, unrecvIndex_List))

    # 开始反馈
    if len(recv_data) < subsection_num:
        p_confirm_ack.start()       
        # 获取为收到的消息的index集合
        for indx in list(set(range(subsection_num)) - set(recv_data.keys())):
            unrecvIndex_List.append(indx)
        print("unrecvIndex_List: ", unrecvIndex_List)
        while len(unrecvIndex_List)>0:
            for _index in unrecvIndex_List:
                time.sleep(0.1)
                print("发送", f"#{_index}")
                sockfd.sendto(f"#{_index}".encode(), source_addr)
    else:
        p_confirm_ack.start()       
    p_send_ack.start()      
    p_confirm_ack.join()
    p_send_ack.join()
    recv_data= sorted(recv_data.items(),key=lambda x:x[0])
 

    with open("NormalRecv" + str(ADDR) + ".txt",'wb') as f:
        # 数据存储
        for data in recv_data:
            f.write(data[1] + "\n".encode())
    print("无丢失收到 %d 个码字." % recv_num)
    print("共收到 %d 个码字." % subsection_num)

    print("\n数据已存放在 NormalRecv" + str(ADDR) + ".txt 中")

    sockfd.close()


def main():
    if len(sys.argv) < 3:
        print('''
            argv is error!
            run as
            python3 forward.py 127.0.0.1 8888
            ''')
        raise

    # 创建与源通信的套接字
    sockfd = socket(AF_INET, SOCK_DGRAM)
    # 绑定地址
    IP = sys.argv[1]
    PORT = int(sys.argv[2])
    ADDR = (IP, PORT)
    sockfd.bind(ADDR)
    print("主机 " + IP + ":" + sys.argv[2] + " 正在等待数据...\n")
    p1 = Process(target = recv_from_source, args=(sockfd,ADDR))
    p1.start()
    p1.join()


if __name__ == "__main__":
    main()


