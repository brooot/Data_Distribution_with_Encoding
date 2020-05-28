#!/usr/bin/env python3
# encoding=utf-8
from socket import *
from multiprocessing import *
from Xor import *
from config import *
from choose_data import  *
from config import *

import sys, random, os, time, copy, time, threading, select, csv




# 返回自己没有的码字部分
#            {'2','3'}   b"hello"
def recv_Handler(m_info_set, m_data, L_decoded, L_undecoded):
    L = []
    for c_info in L_decoded.keys():
        if c_info in m_info_set:  # 如果新码字中包含已解码码字,就将其剔除
            m_info_set.remove(c_info)  # 将该码字信息剔除
            L.append(L_decoded[c_info])  # 将其对应的字节码加入列表等待异或解码

    # print("L = ", L, "m_info_set",m_info_set)
    if (not L) and len(m_info_set) > 1 and ([m_info_set, m_data] not in L_undecoded):  # 如果没有相同的数据,表示无法解码,放入未解码的列表中
        L_undecoded.append([m_info_set, m_data])
        # print("添加到未解码: ", [m_info_set, m_data])

    elif m_info_set:  # 表示剥除部分且还有剩余
        # 异或解码
        L.append(m_data)
        new_data = bytesList_Xor_to_Bytes(L)

        # 判断剩下的码字度是多少
        if len(m_info_set) == 1:  # 如果剩下的度为1, 递归解码
            # print("度为1,进行递归解码")
            recursion_Decode(list(m_info_set)[0], new_data, L_decoded, L_undecoded)
        elif m_info_set and [m_info_set, m_data] not in L_undecoded:  # 否则加入到未解码列表中
            # print("度大于1,添加到未解码: ", [m_info_set, m_data])
            L_undecoded.append([m_info_set, m_data])


# 递归解码
#   info: '2'  data: b"hello"     码字格式: [{'2','3'},b"hello world"]
def recursion_Decode(_info, _data, L_decoded, L_undecoded):
    L_decoded[_info] = _data  # 将其加入到已解码集合中
    decode_List = []  # 等待递归解码列表
    for info, data in L_decoded.items():
        for cw in L_undecoded:
            c_info = cw[0]
            c_data = cw[1]
            if info in c_info:  # 如果其中含有刚解码出的码字, 就将其剥离
                # 更新码字信息
                # print("从" ,c_info, "中删减码字信息",info,end='')
                c_info = c_info - {info}
                # print(" 得到 ",c_info)
                if len(c_info) == 0:  # 如果信息为空,就将该码字移出未解码列表
                    L_undecoded.remove(cw)
                    continue

                c_data = bytesList_Xor_to_Bytes([c_data, data])
                L_undecoded.remove(cw)
                if [c_info, c_data] not in L_undecoded:
                    L_undecoded.append([c_info, c_data])

                if len(c_info) == 1 and [c_info, c_data] not in decode_List:  # 若解码后的码字度为1, 加入递归解码的列表,等待递归解码
                    decode_List.append([c_info, c_data])

    for cw in decode_List:
        if cw[0] and cw[1][0] != 0:
            c_info = list(cw[0])[0]
        else:
            continue
        if c_info not in L_decoded:
            recursion_Decode(c_info, cw[1], L_decoded, L_undecoded)


# 发送ack
def send_ack(source_not_confirmed, sockfd, addr):
    send_time = 1  # 第几次发送
    while source_not_confirmed.value:
        # 向源端发送 ack
        send_message = "ok"
        print("第" + str(send_time) + "次 ", end='')
        print("向源端发送ack信息 ")
        send_with_loss_prob(sockfd, send_message.encode(), addr)
        if send_time == 1:
            time.sleep(0.5)
            send_time += 1
        else:
            send_time += 1
            time.sleep(1) 


# 确认源端收到ack 假设最终的还有转发层服务器没有解码出全量，那么已经解码出全部的服务器还需要继续工作的。
def confirm_ack(source_not_confirmed, need_to_forwardrecv, sockfd, source_addr):
    while need_to_forwardrecv.value:
        data, address = sockfd.recvfrom(4096)
        if source_addr == address and data.decode() == "got_it":
            print("发送方已经收到ack")
            source_not_confirmed.value = False
        elif source_addr == address and data.decode() == "stop_all":
            print("所有转发层节点都已解码, 转发层通信终止.")
            need_to_forwardrecv.value = False
    print("\n------------------------\n一轮接收完成!\n")


# 从转发层邻居收到的交换信息
def recv_from_peer(nei_Need_Map, sockfd_withPeer, Neigh_ADDR, L_decoded, L_undecoded, Q_need_to_sendback, need_to_forwardrecv, lock_of_L):
    inputs = [sockfd_withPeer]
    # 记录从转发层邻居收到的数据
    recv_Peer_num = 0
    # 源端的一轮发送未结束,就始终接收邻居发来的信息.
    while need_to_forwardrecv.value:
        r_list = select.select(inputs, [], inputs, 1)[0]
        if r_list:
            try:
                data, addr = sockfd_withPeer.recvfrom(4096)
            except Exception as e:
                print("peer接收套接字异常, 错误信息: ", e)
            
            # 如果是邻居且是发来的交换请求
            if addr in Neigh_ADDR:
                # 收到来自peer 的数据个数 + 1
                recv_Peer_num += 1
                data = data.decode()
                codes_peer_need = data.split("&")[:-1]
                # if codes_peer_need: # 如果带有请求数据
                data = data.split('&')[-1]
                # 记录对方需要的数据
                nei_Need_Map[addr] = codes_peer_need

                # 如果是请求数据, 则需要回应
                if data[0] == '!':
                    data = data[1:]
                    print(time.ctime().split(" ")[4], "收到  交换请求 <--- ", addr)
                    if(Q_need_to_sendback.qsize() < len(Neigh_ADDR)):
                        Q_need_to_sendback.put(addr)
                    # print("Q_need_to_sendback is empty: ", Q_need_to_sendback.empty())
                else:
                    print(time.ctime().split(" ")[4], "收到  反馈信息 <--- ", addr)

                # else:
                #     # 如果是新的交换数据请求
                #     if data[0] == '!':
                #         data = data[1:]
                #         # 将地址传给发送进程, 告知其回发数据的地址
                #         # if(Q_need_to_sendback.qsize() < len(Neigh_ADDR)):
                #         #     Q_need_to_sendback.put(addr)
                #         # print(time.ctime().split(" ")[4], "收到  交换请求 <--- ", addr)
                #     # 是反馈数据
                #     else:
                #         print(time.ctime().split(" ")[4], "收到  反馈信息 <--- ", addr)

                m_info_set = set(data.split("##", 1)[0].split("@"))
                # 获取码字数据(字符串的字节码)
                m_data = data.split("##", 1)[1].encode()
                # print("\n 从",addr[1] ,"收到 转发层 信息：", m_info_set, "\n")
                # 给 lock_of_L & L_undecoded 上锁
                with lock_of_L:
                    # 解码
                    recv_Handler(m_info_set, m_data, L_decoded, L_undecoded)
                    # print("收到码字")
    print("从转发层共收到 %d 个码字." % recv_Peer_num)

                # 记录 解码 曲线
                # if len(L_decoded) > decoded_num:
                #     # 当解码个数有变化的时候,记录此时的接受数量与解码数量的关系
                #     decoded_num = len(L_decoded)
                #     recvNum_and_decodeNum.append((recv_num, decoded_num))

                # print("\n未解码个数:  ", len(L_undecoded))
                # print("已解码个数:   ", len(L_decoded))
                # print("\n")

                # print("\n------------------------------\n")



def feedback_to_peer(nei_Need_Map, sockfd_withPeer, Q_need_to_sendback, time_queue, L_decoded, L_undecoded, start_index, source_not_confirmed, need_to_forwardrecv):
    while len(L_decoded) + len(L_undecoded) == 0:
        pass

    # 当一轮传输未结束, 仍然反馈邻居的交换请求
    while need_to_forwardrecv.value:
        while not Q_need_to_sendback.empty():
            peerAddr = Q_need_to_sendback.get()
            # 选出数据发送给该邻居
            if peerAddr in nei_Need_Map:
                need_codes = nei_Need_Map[peerAddr]
            else:
                need_codes = []
            # print("feedback needcode:", need_codes)
            encoded_Data = get_forward_encoded_data(need_codes, time_queue, L_decoded, L_undecoded, start_index)
            if encoded_Data:
                print(time.ctime().split(" ")[4], "发送  应答码字 ---> ", peerAddr)
                start_index += 1
                # print("start_index: ", start_index)
                send_with_loss_prob(sockfd_withPeer, encoded_Data, peerAddr)
                time.sleep(forward_send_delay) # 延迟
            # else:
            #     print("None, 不反馈")
                




# 转发层之间互相发送使用的端口比转发层接收源的端口加1
def comm_with_peer(ADDR, L_decoded, L_undecoded, source_not_confirmed, lock_of_L, need_to_forwardrecv):
    # 记录邻居需要的码字表
    nei_Need_Map = Manager().dict()
    # 创建与转发层邻居通信的套接字
    sockfd_withPeer = socket(AF_INET, SOCK_DGRAM)
    sockfd_withPeer.settimeout(forward_send_delay)

    # 绑定转发层通信地址(相对源通信套接字端口偏移)
    sockfd_withPeer.bind(get_forward_selfADDR(ADDR))
    # 获取转发层交互邻居
    Neigh_ADDR = get_forward_Neighbor(ADDR)

    # 通信管道, 接收的线程告诉主进程需要回发的邻居地址
    Q_need_to_sendback = Queue(len(Neigh_ADDR))

    # 接收转发层数据的线程
    t_recv_from_peer = threading.Thread(target=recv_from_peer, args=(nei_Need_Map, sockfd_withPeer, Neigh_ADDR, L_decoded, L_undecoded, Q_need_to_sendback, need_to_forwardrecv, lock_of_L))
    
    # 开始接受线程
    t_recv_from_peer.start()

    # 以下是发送转发
    # 开始下标
    start_index = 0
    # 时间序列
    time_queue = getDegreeSququeGC(piece_num) # 参数改成 record_num
    
    # 回发进程
    t_feedback_to_peer = threading.Thread(target=feedback_to_peer, args=(nei_Need_Map, sockfd_withPeer, Q_need_to_sendback, time_queue, L_decoded, L_undecoded, start_index, source_not_confirmed, need_to_forwardrecv))
    # 开始回馈线程
    t_feedback_to_peer.start()
    
    while len(L_decoded) + len(L_undecoded) < 1:
        pass

    # 开始转发层发送
    while source_not_confirmed.value:
        # 获取随机peer地址
        dest_addr = Neigh_ADDR[random.randint(0, len(Neigh_ADDR) - 1)]
        # if len(L_decoded)>ratio_to_pull*record_num and len(L_decoded)<record_num:
        request_infos = "" # 需要的信息
        for i in range(1,record_num+1):
            if str(i) not in L_decoded.keys():
                request_infos += str(i) + '&'
        if dest_addr in nei_Need_Map:
            need_codes = nei_Need_Map[dest_addr]
        else:
            need_codes = []
        # print("need codes: ", need_codes)
        forward_encoded_data = get_forward_encoded_data(need_codes, time_queue, L_decoded, L_undecoded, start_index)
        # print("encoded data: ", forward_encoded_data)
        if forward_encoded_data: # 仅当需要发送时发送
            # print("需要的码字:", request_infos)
            encoded_Data = (request_infos + '!').encode() + forward_encoded_data
            start_index += 1
            print(time.ctime().split(" ")[4], "发送  请求码字 ---> ", dest_addr)
            send_with_loss_prob(sockfd_withPeer, encoded_Data, dest_addr)
            time.sleep(forward_send_delay) # 延迟
        # else:
            # print("无对方没有的一度包, 故不发送")


        # else:
        #     # 获取编码后用于转发层交换的数据
        #     forward_encoded_data = get_forward_encoded_data(nei_Need_Map[dest_addr], time_queue, L_decoded, L_undecoded, start_index)
        #     if forward_encoded_data: # 仅当需要发送时发送
        #         encoded_Data = '!'.encode() + forward_encoded_data
        #         print("\n\n", time.ctime().split(" ")[4], "转发层 发送请求 ---> :", dest_addr)
        #         start_index += 1
        #         send_with_loss_prob(sockfd_withPeer, encoded_Data, dest_addr)
        #         time.sleep(forward_send_delay) # 延迟
        #     else:
        #         print("无对方没有的一度包, 故不发送")

    t_feedback_to_peer.join()
    t_recv_from_peer.join()



def comm_with_source(ADDR, L_decoded, L_undecoded, source_not_confirmed, lock_of_L, need_to_forwardrecv):
    
    # 创建与源通信的套接字
    sockfd = socket(AF_INET, SOCK_DGRAM)
    # 绑定地址
    sockfd.bind(ADDR)

    print("主机 " + ADDR[0] + ":" + str(ADDR[1]) + " 正在等待数据...\n")

    sendRound_and_decodeNum = []
    recvNum_and_decodeNum = []
    recv_num = 0
    decoded_num = 0
    while True:
        # 接受数据(与tcp不同)
        data, addr = sockfd.recvfrom(4096)
        # 源端接收数据个数 + 1
        recv_num += 1
        # 数据解码
        data = data.decode()

        # 提取源的发送轮次
        send_round, data = data.split("~", 1)

        m_info_set = set(data.split("##", 1)[0].split("@"))
        # 获取码字数据(字符串的字节码)


        m_data = data.split("##", 1)[1].encode()
        # print("\n从源收到：", m_info_set)

        # 给 lock_of_L & L_undecoded 上锁
        with lock_of_L:
            # 使用刚刚接收到的数据进行解码
            recv_Handler(m_info_set, m_data, L_decoded, L_undecoded)

        sendRound_and_decodeNum.append((send_round, len(L_decoded)))
        # if len(L_decoded) > decoded_num:
        #     # 当解码个数有变化的时候,记录此时的接受数量与解码数量的关系
        #     decoded_num = len(L_decoded)
        #     recvNum_and_decodeNum.append((recv_num, decoded_num))


        # print("\n------------------------------")
        # print("未解码个数:  ", len(L_undecoded))
        # print("已解码个数:  ", len(L_decoded))
        # print("------------------------------\n")


        # 若解码完成
        if len(L_decoded) == piece_num:

            print("\n\n解码完成!")

            p_send_ack = threading.Thread(target=send_ack, args=(source_not_confirmed, sockfd, source_ADDR))
            p_confirm_ack = threading.Thread(target=confirm_ack, args=(source_not_confirmed, need_to_forwardrecv, sockfd, source_ADDR))

            p_confirm_ack.start()
            p_send_ack.start()

            p_confirm_ack.join()
            p_send_ack.join()


            # 将解码数据记录到excel表格中
            with open("Decoding_Log" + str(ADDR) + ".csv","w",newline="") as datacsv:
                #dialect为打开csv文件的方式，默认是excel，delimiter="\t"参数指写入的时候的分隔符
                csvwriter = csv.writer(datacsv,dialect = ("excel"))
                #csv文件插入一行数据，把下面列表中的每一项放入一个单元格（可以用循环插入多行）
                csvwriter.writerow(["源的发送序号", "已解码个数"])
                for sen_round, deco_num in sendRound_and_decodeNum:
                    csvwriter.writerow([sen_round, deco_num])


            
            # 将解码出的数据存放到txt文件中
            with open("GCforward_Recv" + str(ADDR) + ".txt", 'wb') as f:
                data_to_save = sorted(L_decoded.items(), key=lambda x: int(x[0]))
                for piece in data_to_save:
                    f.write(piece[1].split("=".encode(), 1)[0])
            print("\n解码数据已经存放在 PureFountainCode_Recv" + str(ADDR) + ".txt 中")

            # with open("Decoding_Log" + str(ADDR) + ".txt", 'wb') as f:
            #     for i in recvNum_and_decodeNum:
            #         f.write("(%d, %d),".encode() % i)
            # print("解码过程信息存放在 PureFountainCode_Log" + str(ADDR) + ".txt 中")
            print("从源端共收到 %d 个码字." % recv_num)
            print("总记录条数: %d" % record_num)
            

            break
    sockfd.close()


def main():

    if len(sys.argv) < 3:
        print('''
            argv is error!
            run as
            python new_forward.py 127.0.0.1 8888
            ''')
        raise
 
    IP = sys.argv[1]
    PORT = int(sys.argv[2])
    ADDR = (IP, PORT)

    L_decoded = Manager().dict()
    L_undecoded = Manager().list()
    lock_of_L = Lock()

    need_to_forwardrecv = Value('i', True)
    source_not_confirmed = Value('i', True)

    p1 = threading.Thread(target=comm_with_source, args=(ADDR, L_decoded, L_undecoded, source_not_confirmed, lock_of_L, need_to_forwardrecv))
    p2 = threading.Thread(target=comm_with_peer, args=(ADDR, L_decoded, L_undecoded, source_not_confirmed, lock_of_L, need_to_forwardrecv))

    p1.start()
    p2.start()

    p1.join()
    p2.join()


if __name__ == "__main__":
    main()


