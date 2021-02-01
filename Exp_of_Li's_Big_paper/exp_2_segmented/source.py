# encoding=utf-8
import csv
import sys, time, os, random, importlib
from socket import *

import select

from choose_data import *
from multiprocessing import *
from config import *

cfg = Config()


def checkReady(sockfd, recv_Num):
    inputs = [sockfd]
    recv_ready_num = 0
    # 源端的一轮发送未结束,就始终接收邻居发来的信息.
    while True:
        r_list = select.select(inputs, [], inputs, 5)[0]
        if r_list:
            try:
                data, addr = sockfd.recvfrom(1024)
            except Exception:
                continue
            data = data.decode()
            if data == "ready":
                recv_ready_num += 1
                print(f"----------------------\n 共接收到 {recv_ready_num} 个 ready ! \n----------------------")
                if recv_ready_num == recv_Num:
                    break


# ack 校验进程函数   ack_neighbor是一个进程间全局消息  负责接收转发层的ack
def check_ack(still_need_sending, sockfd, ack_neighbor, Dest_ADDR):
    while still_need_sending.value:
        data, addr = sockfd.recvfrom(4096)
        if data.decode() == "ok":
            sockfd.sendto("got_it".encode(), addr)
            # print("\n---------------------------\n收到", addr, "的ack\n---------------------------")
            if addr not in ack_neighbor:
                ack_neighbor.append(addr)
            if len(ack_neighbor) == len(Dest_ADDR):
                still_need_sending.value = False
                for sendAddr in Dest_ADDR:
                    sockfd.sendto("stop_all".encode(), sendAddr)
        else:
            print("主机 %s 发来消息：%s" % (addr, data.decode()))


# 发送进程函数
def send(total_time, still_need_sending, ack_neighbor, Dest_ADDR, sockfd, min_unit, piece_num, round_idx, bytes_List, sendNum):
    dest_num = len(Dest_ADDR)  # 获取转发层节点个数

    # for bytes_List in Round_list:
    print(f"send piece_num: {piece_num}")

    recver_index = 0  # 记录当前要发给哪个转发层节点
    
    print(f"第{round_idx}轮发送")
    if round_idx == 1:
        for i in range(3):
            time.sleep(1)
            print("%ds 后开始发送数据" % (3 - i))
    t_begin = time.time()
    sendNum.value = 0  # 发送的数据包的个数
    
    # for _id in range(1, piece_num + 1):
    #     sendNum.value += 1
    #     preSendData = ""
    #     preSendData += str(_id) + "##"
    #     preSendData = preSendData.encode() + bytes_List[_id - 1]
    #     preSendData = (str(sendNum.value) + "~").encode() + preSendData
    #     cfg.send_with_loss_prob(sockfd, preSendData, Dest_ADDR[recver_index])
    #     recver_index = (recver_index + 1) % dest_num
    #     time.sleep(cfg.send_delay)


    print("------------------ direct sending over -----------------")

    # 第一段度分布
    p1 = get_robustSolition_degree_distribution(piece_num)
    p2 = get_newSolition_degree_distribution(piece_num)
    degreeChangePoint = 0.5  # 度分布切换点
    # 当仍然未解码, 开始编码发送
    while still_need_sending.value:
        for neighbor in Dest_ADDR:
            if len(ack_neighbor) < len(Dest_ADDR):
                if neighbor not in ack_neighbor:
                    sendNum.value += 1
                    print(f"第{sendNum.value}个包发给{neighbor}.")
                    if sendNum.value < degreeChangePoint * piece_num:  # 第一段
                        encoded_Data = get_encoded_data(piece_num, bytes_List, p1)
                    else:  # 第二段
                        encoded_Data = get_encoded_data(piece_num, bytes_List, p2)
                    encoded_Data = (str(sendNum.value) + "~").encode() + encoded_Data
                    cfg.send_with_loss_prob(sockfd, encoded_Data, neighbor)
                    time.sleep(cfg.send_delay)
            else:
                break
    t_end = time.time()
    total_time.value += t_end - t_begin
    print(f"第{round_idx}轮发送共用时: %lf 秒" % (t_end - t_begin))


# Socket 具有三大属性：域、类型、协议。
# 域：AF_UNIX（Unix 文件系统，地址为文件名，对应文件 IO） 和 AF_INET（Internet 网络，常用）两类
# 类型：SOCK_STREAM（流，对应 TCP） 和 SOCK_DGRAM（数据报，对应 UDP）
# 协议：只要底层的传输机制允许不止一个协议来提供要求的套接字类型，
# 我们就可以为套接字选择一个特定的协议。通常只需要使用默认值 0。

def main(min_unit, pieces_each_round, exp_index):
    # 创建套接字 这里对应的网络和UDP协议
    sockfd = socket(AF_INET, SOCK_DGRAM)
    sockfd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sockfd_r = socket(AF_INET, SOCK_DGRAM)
    sockfd_r.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    record_num = Config().record_num
    if min_unit == 68:
        piece_num = record_num
    else:
        piece_num = 68 * record_num // min_unit + (1 if (68 * record_num % min_unit) else 0)

    # 记录发送时间
    total_time = Value('d', 0)

    # 记录总共发送的数据包的个数
    sendNum = Value('i', 0)

    # source_ADDR 在 config.py 中
    self_ADDR = cfg.source_ADDR

    # 绑定自身地址和端口号
    sockfd.bind(self_ADDR)
    sockfd_r.bind(("127.0.0.1", 6666))
    # -------------------------------------
    big_piece_num = piece_num // pieces_each_round

    print("发送记录条数为: ", cfg.record_num)
    print("发送分段大小为: ", piece_num)

    # 获取所有的一轮中要发送的数据
    bytes_List = get_bytesList_of_a_generation(min_unit, piece_num)
    print("要发送的数据获取完毕")
    # 发送的大轮次的数量,即数据被分成几大段来发送
    Round_Num = big_piece_num
    Round_list = []
    for i in range(Round_Num):
        Round_list.append(bytes_List[:pieces_each_round])
        bytes_List = bytes_List[pieces_each_round:]

    if bytes_List and len(bytes_List) > pieces_each_round / 2:
        Round_list.append(bytes_List)
    elif bytes_List:
        Round_list[-1] = Round_list[-1] + bytes_List
    total_Round_Num = len(Round_list)  # 总共的发送轮次

    round_idx = 1
    # 记录已经确认解码的邻居的列表   多进程共享全局变量
    # -------------------------------------
    print(f"共分{len(Round_list)}次发送")

    # 在某一条件下一直以一代数据为单位,向转发层发送喷泉码
    for bytes_List in Round_list:
        for recv_addr in cfg.Dest_ADDR:
            sockfd.sendto("start".encode(), recv_addr)
        p_checkReady = Process(target=checkReady, args=(sockfd_r, len(cfg.Dest_ADDR)))
        p_checkReady.start()
        piece_num = len(bytes_List)
        # 记录是否还需要发送数据   多进程间共享全局变量
        still_need_sending = Value('i', True)
        ack_neighbor = Manager().list()
        # 定义发送子进程
        p_send = Process(target=send, args=(
            total_time, still_need_sending, ack_neighbor, cfg.Dest_ADDR, sockfd, min_unit, piece_num, round_idx,
            bytes_List, sendNum))
        # 定义ack校验子进程
        p_check_ack = Process(target=check_ack, args=(still_need_sending, sockfd, ack_neighbor, cfg.Dest_ADDR))

        # 开启ack校验进程
        p_check_ack.start()
        # 开启发送进程
        p_send.start()

        # 等待两个子进程执行结束再执行之后的代码
        p_checkReady.join()
        p_send.join()
        p_check_ack.join()
        round_idx += 1

    sockfd.close()
    print(f"共{round_idx-1}轮,全部发送完毕, 共用时 {total_time.value} s.")

    # 将源端发送总伦次写入文件中
    with open("Source_Summary" + f"_exp_{exp_index}" + ".csv", "w", newline="", encoding='utf-8') as datacsv:
        # dialect为打开csv文件的方式，默认是excel，delimiter="\t"参数指写入的时候的分隔符
        csvwriter = csv.writer(datacsv, dialect="excel")
        # csv文件插入一行数据，把下面列表中的每一项放入一个单元格（可以用循环插入多行）
        csvwriter.writerow(["总发送次数", "系统运行时间"])
        csvwriter.writerow([sendNum.value, "%2f" % total_time.value])

    return total_time.value


if __name__ == '__main__':
    main()
