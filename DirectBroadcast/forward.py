#!/usr/bin/env python3
#encoding=utf-8
from socket import *
from multiprocessing import *
from Xor import *
from config import *
import sys, random, os, time, pymysql


# 收到码字后,第一次处理码字,若解码出 1 度包就转到 "递归解码"
#      数据格式   {'2','3'}   b"hello"
def recv_Handler(m_info_set, m_data, L_decoded, L_undecoded):
    L = []
    for c_info in L_decoded.keys():  
        if c_info in m_info_set:   # 如果新码字中包含已解码码字,就将其剔除
            m_info_set.remove(c_info)  # 将该码字信息剔除
            L.append(L_decoded[c_info])  # 将其对应的字节码加入列表等待异或解码
    
    # print("L = ", L, "m_info_set",m_info_set)

    if (not L) and len(m_info_set)>1 and ([m_info_set, m_data] not in L_undecoded):  # 如果没有相同的数据,表示无法解码,放入未解码的列表中
        L_undecoded.append( [m_info_set, m_data] )
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
            L_undecoded.append( [m_info_set, m_data] )
  
# 递归解码
#   info: '2'  data: b"hello"   已解码码字格式: '3':b"123456"  未解码码字格式: [{'2','3'},b"hello world"]
def recursion_Decode(_info, _data, L_decoded, L_undecoded):
    L_decoded[_info] = _data   # 将其加入到已解码集合中
    decode_List = []  # 等待递归解码列表
    for info, data in L_decoded.items():
        for cw in L_undecoded:
            c_info = cw[0]
            c_data = cw[1]
            if info in c_info: # 如果其中含有刚解码出的码字, 就将其剥离
                # 更新码字信息
                # print("从" ,c_info, "中删减码字信息",info,end='')
                c_info = c_info - {info}
                # print(" 得到 ",c_info)
                if len(c_info) == 0:  # 如果信息为空,就将该码字移出未解码列表
                    L_undecoded.remove(cw)
                    continue


                c_data= bytesList_Xor_to_Bytes([c_data, data])
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


# 在未解码列表中尝试解码
def Redecode_in_undecoded():
    pass

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
def confirm_ack(need_to_resend_ack, sockfd, addr):
    while need_to_resend_ack.value:
        data, address = sockfd.recvfrom(1024)
        if addr == address and data.decode() == "got_it":
            print("发送方已经收到ack")
            need_to_resend_ack.value = False
    print("\n------------------------\n一轮接收完成!\n")


# 从转发层接收数据, 立即广播出去后进行解码
def recv_from_source(ADDR, broad_ADDR, L_decoded, L_undecoded, lock, Has_decoded_all, recvNum, recvNum_and_decodeNum, db, cursor, exp_time, device_id):
    if len(sys.argv) < 3:
        print('''
            argv is error!
            run as
            python3 udp client_udp.py 127.0.0.1 8888
            ''')
        raise
    # 创建与源通信的套接字
    sockfd = socket(AF_INET, SOCK_DGRAM)
    sockfd_broadcast = socket(AF_INET, SOCK_DGRAM)
    sockfd.bind(ADDR)
    # 设置端口立即释放
    sockfd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sockfd_broadcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    # 设置套接字可以发送接受广播
    sockfd_broadcast.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    recvNum.value = 0
    print("主机 " + ADDR[0] + ":" + str(ADDR[1]) + " 正在等待数据...\n")
    # 在一轮开始前,将已全部解码设置为 False
    Has_decoded_all.value = False
    while True:
        # 接受数据(与tcp不同)
        data, addr = sockfd.recvfrom(4096)

        sockfd_broadcast.sendto(data, broad_ADDR)

        recvNum.value += 1
        # 数据解码
        data = data.decode()
        
        m_info_set = set(data.split("##",1)[0].split("@"))
        # 获取码字数据(字符串的字节码)
        m_data = data.split("##",1)[1].encode()
        print("源进程发出广播：", m_info_set)
        print("\n")

        # 使用刚刚接收到的数据进行解码
        with lock:
            # print("已经开锁")
            recv_Handler(m_info_set, m_data, L_decoded, L_undecoded)

            if len(L_decoded) == subsection_num:
                    Has_decoded_all.value = True
            else:
                pre_decoded_num = len(L_decoded)
                recv_Handler(m_info_set, m_data, L_decoded, L_undecoded)
                after_decoded_num = len(L_decoded)
                if (after_decoded_num > pre_decoded_num):
                    recvNum_and_decodeNum[recvNum] = after_decoded_num # 若有新增的解码内容,就更新记录解码过程的字典 {收到的码字个数:已解码的码字个数}
                recv_Handler(m_info_set, m_data, L_decoded, L_undecoded)
                print("源端进程解码结束")
                if len(L_decoded) == subsection_num:
                    Has_decoded_all.value = True
                    print("\n\n全部解码完成!")
        # # 在未解码的码字中寻找解码机会
        # # Redecode_in_undecoded()
        

        # print("\n未解码个数: ", len(L_undecoded))
        # print("\n")
        # print("已解码个数: ", len(L_decoded))

        # print("\n------------------------------\n")

        # 若解码完成
        if len(L_decoded) == subsection_num:
            Has_decoded_all.value = True
            print("\n\n解码完成!")
            need_to_resend_ack = Value('i',True)
            
            p_send_ack = Process(target=send_ack, args=(need_to_resend_ack, sockfd, addr))
            p_confirm_ack = Process(target=confirm_ack, args=(need_to_resend_ack, sockfd, addr))

            p_confirm_ack.start()
            p_send_ack.start()

            p_confirm_ack.join()
            p_send_ack.join()

            # 将解码出的数据存放到txt文件中
            with open("Decoded Data of " + str(ADDR) + ".txt",'wb') as f:
                data_to_save = sorted(L_decoded.items(),key=lambda x:int(x[0]))
                for line in data_to_save:
                    record = line[1] + "\n".encode()
                    f.write(record)
            print("\n解码数据已经存放在 Decoded Data of " + str(ADDR) + ".txt中")
            
            decode_log = ""
            for i in recvNum_and_decodeNum:
                decode_log += "(%d, %d)," % i
            # 实验次数, 设备id, 实验结果
            content = (exp_time , device_id, decode_log)

            # 插入语句
            SQL = "insert into direct_broadcast (exp_time, device_id, decode_log) values (%d,%s,'%s');" % content

            # 执行插入语句
            cursor.execute(SQL)

            # 提交
            db.commit()
            print("解码过程信息存放在 10.1.18.79 的数据库 中")

            print("共收到%d个码字." %recvNum.value )
            break

    sockfd.close()

# 接受广播,并解码
def forward_exchange(self_ADDR, broad_ADDR, L_decoded, L_undecoded, lock, Has_decoded_all, recvNum, recvNum_and_decodeNum):
    # 广播套接字
    broadcast_sockfd = socket(AF_INET, SOCK_DGRAM)
    # 设置端口立即释放
    broadcast_sockfd.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    # 设置套接字可以发送接受广播
    broadcast_sockfd.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    # 固定接受端口
    broadcast_sockfd.bind(('0.0.0.0', 9870))

    

    # 如果还没有解码出一轮中所有的码字
    while not Has_decoded_all.value:
        data, addr = broadcast_sockfd.recvfrom(4096)
        if addr[0] == self_ADDR[0]:
            continue
        # 收到其他节点的广播，告知源端接受进程进行解码
        else:
            recvNum.value += 1
            print("收到来自", addr,"的数据包")
            # print("自身地址", self_ADDR)
            data = data.decode()
            m_info_set = set(data.split("##",1)[0].split("@"))
            # 获取码字数据(字符串的字节码)
            m_data = data.split("##",1)[1].encode()
            print("收到 ",addr, "的'广播' 码字数据的信息：", m_info_set, '\n')
            # 使用刚刚接收到的数据进行解码
            # print("需要开锁")
            with lock:
                if len(L_decoded) == subsection_num:
                    break
                # print("已经开锁")
                pre_decoded_num = len(L_decoded)
                recv_Handler(m_info_set, m_data, L_decoded, L_undecoded)
                after_decoded_num = len(L_decoded)
                if (after_decoded_num > pre_decoded_num):
                    recvNum_and_decodeNum[recvNum.value] = after_decoded_num # 若有新增的解码内容,就更新记录解码过程的字典 {收到的码字个数:已解码的码字个数}
                # print("转发层进程解码完毕")
                if len(L_decoded) == subsection_num:
                    Has_decoded_all.value = True
                    # print("\n\n解码完毕!!!!!!!!!!!!!!")
    

def main():
    # 绑定地址
    IP = sys.argv[1]
    PORT = int(sys.argv[2])
    ADDR = (IP, PORT)
    broad_ADDR = ("10.1.18.255",9870)

    L_decoded = Manager().dict()
    L_undecoded = Manager().list()
    # 记录收到的数据包的数量
    recvNum = Value('i', 0)
    # 记录收到的数据包数据量和解码数量的关系的字典
    recvNum_and_decodeNum = Manager().dict()
    # 解码互斥锁,防止同时解码造成数据错乱
    lock = Lock()
    # 设置一个信号量标识一轮是否已经解码完成
    Has_decoded_all = Value('i',False)
    # 打开数据库连接
    db = pymysql.connect(host="10.1.18.79",port=3306,user="root",passwd="chain",db="exp_data",charset='utf8')
     
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    # 获取上一次实验的实验次数
    cursor.execute("select exp_time from direct_broadcast order by id DESC limit 1;")
    db.commit()
    data = cursor.fetchone()
    if data:
        exp_time = data[0] + 1  # 实验次数加 1
    else:
        exp_time = 1
    device_id = sys.argv[1].split(".")[-1]
    p1 = Process(target = recv_from_source, args=(ADDR, broad_ADDR, L_decoded, L_undecoded, lock, Has_decoded_all, recvNum, recvNum_and_decodeNum, db, cursor, exp_time, device_id))
    p2 = Process(target = forward_exchange, args=(ADDR, broad_ADDR, L_decoded, L_undecoded, lock, Has_decoded_all, recvNum, recvNum_and_decodeNum))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print("执行main函数完毕")


if __name__ == "__main__":
    main()


