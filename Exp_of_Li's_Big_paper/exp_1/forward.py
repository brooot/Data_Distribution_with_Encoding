# encoding=utf-8
from socket import *
from multiprocessing import *
from choose_data import *
from config import *

cfg = Config()

import sys, random, os, time, copy, time, threading, select, csv


# 返回自己没有的码字部分
#            {'2','3'}   b"hello"
def recv_Handler(m_info_set, m_data, L_decoded, L_undecoded, piece_num):
    L = []
    for c_info in L_decoded.keys():
        if c_info in m_info_set:  # 如果新码字中包含已解码码字,就将其剔除
            m_info_set.remove(c_info)  # 将该码字信息剔除
            L.append(L_decoded[c_info])  # 将其对应的字节码加入列表等待异或解码

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
            if int(list(m_info_set)[0]) > piece_num:
                pass
                # print(f"======\n\n======================= {list(m_info_set)[0]}=======================\n\n====== ")
            else:
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
        # print("第" + str(send_time) + "次 ", end='')
        # print("向源端发送ack信息 ")
        cfg.send_with_loss_prob(sockfd, send_message.encode(), addr)
        if send_time == 1:
            time.sleep(0.5)
            send_time += 1
        else:
            send_time += 1
            time.sleep(1)

        # 确认源端收到ack 假设最终的还有转发层服务器没有解码出全量，那么已经解码出全部的服务器还需要继续工作的。


def confirm_ack(source_not_confirmed, need_to_forwardrecv, sockfd, source_addr):
    while need_to_forwardrecv.value:
        data, address = sockfd.recvfrom(1024 * 1024 + 2000)
        if source_addr == address and data.decode() == "got_it":
            # print("发送方已经收到ack")
            source_not_confirmed.value = False
        elif source_addr == address and data.decode() == "stop_all":
            # print("所有转发层节点都已解码, 转发层通信终止.")
            need_to_forwardrecv.value = False
    # print("\n------------------------\n一轮接收完成!\n")


# 从转发层邻居收到的交换信息
def recv_from_peer(self_Addr, interval_map, forward_send_num, nei_Need_Map, sockfd_withPeer, Neigh_ADDR, L_decoded,
                   L_undecoded,
                   Q_need_to_sendback,
                   need_to_forwardrecv, lock_of_L, min_unit, piece_num, recvNumFromPeer, decodeQueue):
    inputs = [sockfd_withPeer]
    # 记录从转发层邻居收到的数据
    recv_Peer_num = 0
    # 源端的一轮发送未结束,就始终接收邻居发来的信息.
    get_num = 0
    while need_to_forwardrecv.value:
        r_list = select.select(inputs, [], inputs, 10)[0]
        if r_list:
            try:
                data, addr = sockfd_withPeer.recvfrom(1024 * 1024 + 2000)
                get_num += 1
                # print(f"+++++++++++++++++++++ 收到数据 {get_num} +++++++++++++++++++++++++++")
            except Exception as e:
                continue
                # print("peer接收套接字异常, 错误信息: ", e)
            recvNumFromPeer.value += 1  # 从转发层收到数据量 + 1
            data = data.decode()
            if data == "i need codes":
                if Q_need_to_sendback.qsize() < len(Neigh_ADDR):
                    # print(" 加入到 反馈 Queue")
                    Q_need_to_sendback.put(addr)
                continue
            # 先将 info 和 data 分离
            try:
                split_str = data.split("##", 1)
                m_info = split_str[0]  # 得到 info 部分
                m_data = split_str[1].encode()
                if len(m_data) < 2:
                    print(f"m_info: {m_info}  m_data: {m_data}")
                    raise Exception("收到无效数据")
            except Exception as e:
                print("data出现问题")
                print(data)
                continue
            # print("m_info: ", m_info)
            # print("m_data: ", m_data)
            # 如果是邻居且是发来的交换请求
            if addr in Neigh_ADDR:
                left_info = m_info
                # 收到来自peer 的数据个数 + 1
                recv_Peer_num += 1
                # 如果是带有map的请求数据
                if left_info[0] == '+':
                    #  剥离 '+'
                    split_info = left_info[1:].split("&")
                    codes_peer_need = split_info[:-1]
                    left_info = split_info[-1]
                    # print("codes_peer_need: ", codes_peer_need)
                    # print("left info: ", left_info)
                    if codes_peer_need:  # 如果带有请求数据
                        if codes_peer_need[0] == "end":  # 移除已解码的邻居节点的map
                            interval_map[addr] = forward_send_num.value
                            nei_Need_Map[addr] = ["end"]
                            # print("收到 end")
                        else:
                            nei_Need_Map[addr] = codes_peer_need
                            interval_map[addr] = forward_send_num.value
                            if Q_need_to_sendback.qsize() < len(Neigh_ADDR):
                                Q_need_to_sendback.put(addr)
                            # print("收到map")
                # 记录对方需要的数据

                # 如果是请求数据, 则需要回应
                if left_info[0] == '!':
                    left_info = left_info[1:]
                    # print(time.ctime().split(" ")[4], "收到  交换请求 <--- ", addr)
                else:
                    # print("收到返回数据")
                    pass
                    # print(time.ctime().split(" ")[4], "收到  反馈信息 <--- ", addr)
                m_info_set = set(left_info.split("@"))
                # print("码字信息: ", m_info_set)
                with lock_of_L:
                    # 解码
                    if len(m_data) == min_unit:
                        # print("转发层收到信息: ", m_info_set)
                        for info in m_info_set:
                            if int(info) > piece_num:
                                print(
                                    f"---------------------------\n 收到 非法info:{info} 来自{addr}\n---------------------------")
                                continue
                        # recv_Handler(m_info_set, m_data, L_decoded, L_undecoded, piece_num)
                        decodeQueue.put([m_info_set, m_data])
                    else:
                        print("errorororororo, sleeping...")
                        time.sleep(1000)


def feedback_to_peer(nei_Need_Map, sockfd_withPeer, Q_need_to_sendback, L_decoded, L_undecoded,
                     source_not_confirmed, need_to_forwardrecv, _a, _b, _c):
    while len(L_decoded) + len(L_undecoded) == 0:
        pass

    # 当一轮传输未结束, 仍然反馈邻居的交换请求
    while need_to_forwardrecv.value:
        while not Q_need_to_sendback.empty():
            peerAddr = Q_need_to_sendback.get()
            # 选出数据发送给该邻居
            # 取消!!!!!!!!!!
            # if peerAddr in nei_Need_Map:
            #     need_codes = nei_Need_Map[peerAddr]
            # else:
            #     need_codes = []
            encoded_Data = get_rand_package_from_decoded_or_undecoded(L_decoded, L_undecoded)  # 随机获取已解码或未解码中的一个
            if encoded_Data:
                # print(time.ctime().split(" ")[4], "发送  应答码字 ---> ", peerAddr)
                cfg.send_with_loss_prob(sockfd_withPeer, encoded_Data, peerAddr)
                time.sleep(cfg.forward_send_delay)  # 延迟
            # else:
            #     print("None, 不反馈")


# 转发层之间互相发送使用的端口比转发层接收源的端口加100
def comm_with_peer(ADDR, L_decoded, L_undecoded, source_not_confirmed, lock_of_L, need_to_forwardrecv, min_unit, T_slot,
                   a, b, c, piece_num, recvNumFromPeer, decodeQueue):
    # 记录邻居需要的码字表
    nei_Need_Map = Manager().dict()
    interval_map = Manager().dict()

    # 创建与转发层邻居通信的套接字
    sockfd_withPeer = socket(AF_INET, SOCK_DGRAM)
    sockfd_withPeer.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sockfd_withPeer.settimeout(cfg.forward_send_delay)

    # 绑定转发层通信地址(相对源通信套接字端口偏移)
    self_Addr = cfg.get_forward_selfADDR(ADDR)
    sockfd_withPeer.bind(self_Addr)

    # 获取转发层交互邻居
    Neigh_ADDR = cfg.get_forward_Neighbor(ADDR)

    Q_need_to_sendback = Queue(len(Neigh_ADDR))

    forward_send_num = Value('i', 1)
    # 通信管道, 接收的线程告诉主进程需要回发的邻居地址
    # 接收转发层数据的线程
    t_recv_from_peer = threading.Thread(target=recv_from_peer, args=(self_Addr, interval_map, forward_send_num,
                                                                     nei_Need_Map, sockfd_withPeer, Neigh_ADDR,
                                                                     L_decoded, L_undecoded, Q_need_to_sendback,
                                                                     need_to_forwardrecv,
                                                                     lock_of_L, min_unit, piece_num, recvNumFromPeer, decodeQueue))

    # 开始接受线程
    t_recv_from_peer.start()

    # 以下是发送转发
    # time_queue = getDegreeSququeGC(piece_num)  # 参数改成 record_num

    # 回发进程
    t_feedback_to_peer = threading.Thread(target=feedback_to_peer, args=(
        nei_Need_Map, sockfd_withPeer, Q_need_to_sendback, L_decoded, L_undecoded,
        source_not_confirmed, need_to_forwardrecv, a, b, c))
    # 开始回馈线程
    t_feedback_to_peer.start()

    while len(L_decoded) + len(L_undecoded) < 1:
        pass

    send_map_index = 1  # 发送map的间隔下标
    # 开始转发层发送
    # while source_not_confirmed.value:
    while need_to_forwardrecv.value:
        # 获取随机peer地址
        dest_addr = Neigh_ADDR[random.randint(0, len(Neigh_ADDR) - 1)]
        request_infos = ""  # 需要的信息
        # 到了需要发送map的轮次
        # 注释掉!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # if send_map_index == T_slot:
        #     send_map_index = 1
        #     request_infos += "+"
        #     if len(L_decoded) < piece_num:
        #         for i in range(1, piece_num + 1):
        #             if str(i) not in L_decoded.keys():
        #                 request_infos += str(i) + '&'
        #     # 当自身已经解码, 告知邻居, 不要给自己发送码字了, 但是可以请求
        #     else:
        #         request_infos += 'end&'
        # else:
        #     send_map_index += 1

        if dest_addr in nei_Need_Map:
            need_codes = nei_Need_Map[dest_addr]
        else:
            need_codes = []
        if dest_addr in interval_map:
            u = forward_send_num.value - interval_map[dest_addr]
        else:
            u = 0
        if need_codes != ["end"]:
            # forward_encoded_data = get_forward_GA_data(need_codes, u, L_decoded, L_undecoded, a, b, c)
            forward_encoded_data = get_rand_package_from_decoded_or_undecoded(L_decoded, L_undecoded)  # 随机获取已解码或未解码中的一个
            if forward_encoded_data:  # 仅当需要发送时发送
                encoded_Data = (request_infos + '!').encode() + forward_encoded_data
                # print(time.ctime().split(" ")[4], "发送  请求码字 ---> ", dest_addr)
                cfg.send_with_loss_prob(sockfd_withPeer, encoded_Data, dest_addr)
                forward_send_num.value += 1  # 转发层发送数量 + 1
                time.sleep(cfg.forward_send_delay)  # 延迟
            else:
                time.sleep(cfg.forward_send_delay)  # 延迟
        else:
            cfg.send_with_loss_prob(sockfd_withPeer, "i need codes".encode(), dest_addr)
            forward_send_num.value += 1  # 转发层发送数量 + 1

    t_feedback_to_peer.join()
    t_recv_from_peer.join()


def comm_with_source(sockfd, ADDR, L_decoded, L_undecoded, source_not_confirmed, lock_of_L, need_to_forwardrecv,
                     piece_num, min_unit, recvNumFromSource, exp_index, decodeQueue):
    # print("主机 " + ADDR[0] + ":" + str(ADDR[1]) + " 正在等待数据...\n")

    sendRound_and_decodeNum = []
    recvNumFromSource.value = 0
    # decoded_num = 0
    pt_idx = 0
    while True:
        # 接受数据(与tcp不同)
        try:
            data, addr = sockfd.recvfrom(1024 * 1024 + 2000)
        except Exception as e:
            continue
        # 源端接收数据个数 + 1
        recvNumFromSource.value += 1
        # 数据解码
        data = data.decode()

        # 提取源的发送轮次
        send_round, data = data.split("~", 1)

        m_info_set = set(data.split("##", 1)[0].split("@"))
        # 获取码字数据(字符串的字节码)
        try:
            m_data = data.split("##", 1)[1].encode()
        except Exception:
            continue
        print("\n从源收到：", m_info_set)

        # 给 lock_of_L & L_undecoded 上锁
        with lock_of_L:
            # 使用刚刚接收到的数据进行解码
            if len(m_data) == min_unit:
                # recv_Handler(m_info_set, m_data, L_decoded, L_undecoded, piece_num)
                decodeQueue.put([m_info_set, m_data])
            else:
                print("len: ", len(m_data))
                print("m_data: ", m_data)
                print("min_unit:", min_unit)
                print("sleeping...")
                time.sleep(1000)
                pass

        sendRound_and_decodeNum.append((send_round, len(L_decoded)))
        pt_idx += 1
        if pt_idx == 5:
            pt_idx = 0
            print(f"decoded num: {len(L_decoded)}/{piece_num}")

        if len(L_decoded) > piece_num:
            print("超出piece_num大小, 已解码:")
            print(sorted(L_decoded.keys(), key=lambda x: int(x)))
            # for key in L_decoded.keys():
            #     print(key, end=", ")
            #     if len(L_decoded[key]) != min_unit:
            #         print("error len: ", len(L_decoded[key]))
            #         print("true len:  ", min_unit)
            raise Exception("length error! ")

        # 若解码完成
        if len(L_decoded) == piece_num:
            # print("\n\n解码完成!")
            p_send_ack = threading.Thread(target=send_ack, args=(source_not_confirmed, sockfd, cfg.source_ADDR))
            p_confirm_ack = threading.Thread(target=confirm_ack,
                                             args=(source_not_confirmed, need_to_forwardrecv, sockfd, cfg.source_ADDR))

            p_confirm_ack.start()
            p_send_ack.start()

            p_confirm_ack.join()
            p_send_ack.join()
            # 将解码数据记录到excel表格中
            with open(f"Decoding_Log_exp_{exp_index}_" + str(ADDR) + ".csv", "w", newline="", encoding='utf-8') as datacsv:
                # dialect为打开csv文件的方式，默认是excel，delimiter="\t"参数指写入的时候的分隔符
                csvwriter = csv.writer(datacsv, dialect="excel")
                # csv文件插入一行数据，把下面列表中的每一项放入一个单元格（可以用循环插入多行）
                csvwriter.writerow(["源的发送序号", "已解码个数"])
                for sen_round, deco_num in sendRound_and_decodeNum:
                    csvwriter.writerow([sen_round, deco_num])

            break

# 解码函数
def Decoder(L_decoded, L_undecoded, decodeQueue, piece_num, need_to_forwardrecv):
    while need_to_forwardrecv.value:
        while not decodeQueue.empty():
            m_info_set, m_data = decodeQueue.get()
            recv_Handler(m_info_set, m_data, L_decoded, L_undecoded, piece_num)
            if not need_to_forwardrecv.value:
                break



def main(ip, port, min_unit, T_slot, a, b, c, pieces_each_round, exp_index):
    ADDR = (ip, port)
    # 创建与源通信的套接字
    sockfd = socket(AF_INET, SOCK_DGRAM)
    sockfd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sockfd_r = socket(AF_INET, SOCK_DGRAM)
    sockfd_r.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sockfd_r.bind(("127.0.0.1", port + 200))

    # 绑定地址
    sockfd.bind(ADDR)
    lock_of_L = Lock()
    record_num = Config().record_num
    if min_unit == 68:
        piece_num = record_num
    else:
        piece_num = 68 * record_num // min_unit + (1 if (68 * record_num % min_unit) else 0)

    # 获取每一轮的数据量
    Round_Num = piece_num // pieces_each_round
    A_round_piece_num = pieces_each_round
    left_piece_num = piece_num % pieces_each_round
    if left_piece_num and left_piece_num > A_round_piece_num / 2:
        total_rouond = Round_Num + 1
    else:
        total_rouond = Round_Num

    PIECE_NUM_list = []
    for i in range(Round_Num):
        PIECE_NUM_list.append(A_round_piece_num)
    if total_rouond > Round_Num:
        PIECE_NUM_list.append(left_piece_num)
    elif left_piece_num:
        PIECE_NUM_list[-1] = PIECE_NUM_list[-1] + left_piece_num

    print("piece_num_list: ", PIECE_NUM_list)
    # 获取要发送的次数
    for piece_num in PIECE_NUM_list:
        while True:
            r_data, r_addr = sockfd.recvfrom(1024)
            if r_addr == cfg.source_ADDR:
                if r_data == "start".encode():
                    break

        need_to_forwardrecv = Value('i', True)
        source_not_confirmed = Value('i', True)
        recvNumFromSource = Value('i', 0)
        recvNumFromPeer = Value('i', 0)
        L_decoded = Manager().dict()
        L_undecoded = Manager().list()
        decodeQueue = Queue(10000) # 解码队列

        p1 = threading.Thread(target=comm_with_source,
                              args=(sockfd, ADDR, L_decoded, L_undecoded, source_not_confirmed, lock_of_L,
                                    need_to_forwardrecv, piece_num, min_unit, recvNumFromSource, exp_index, decodeQueue))
        p2 = threading.Thread(target=comm_with_peer,
                              args=(ADDR, L_decoded, L_undecoded, source_not_confirmed, lock_of_L, need_to_forwardrecv,
                                    min_unit, T_slot, a, b, c, piece_num, recvNumFromPeer, decodeQueue))
        p3 = threading.Thread(target=Decoder, args=(L_decoded, L_undecoded, decodeQueue, piece_num, need_to_forwardrecv))
        
        p1.start()
        p2.start()
        p3.start()
        
        p1.join()
        p2.join()
        p3.join()

        # 记录从源和转发层节点收到的数据的个数
        with open(f"RecvNum_exp_{exp_index}_" + str(ADDR) + f".csv", "w", newline="", encoding='utf-8') as datacsv:
            # dialect为打开csv文件的方式，默认是excel，delimiter="\t"参数指写入的时候的分隔符
            csvwriter = csv.writer(datacsv, dialect="excel")
            # csv文件插入一行数据，把下面列表中的每一项放入一个单元格（可以用循环插入多行）
            csvwriter.writerow(["从源收到的个数", "从转发层收到的个数"])
            csvwriter.writerow([recvNumFromSource.value, recvNumFromPeer.value])

        sockfd_r.sendto("ready".encode(), ("127.0.0.1", 6666))
        # print("发送 ready ........")
        # print(f"{ADDR} is ready for next round.")
        del L_decoded, L_undecoded
    sockfd.close()
    sockfd_r.close()


if __name__ == "__main__":
    main()
