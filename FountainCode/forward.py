#!/usr/bin/env python3
#encoding=utf-8
from socket import *
from multiprocessing import *
from Xor import *
from config import *
import sys, random, os, time, pymysql



#            {'2','3'}   b"hello"
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
  

#   info: '2'  data: b"hello"     码字格式: [{'2','3'},b"hello world"]
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


# 在未解码中寻找能解码的
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


def recv_from_source(db, cursor, exp_time, device_id):
    if len(sys.argv) < 3:
        print('''
            argv is error!
            run as
            python3 udp client_udp.py 127.0.0.1 8888
            ''')
        raise
    # 创建与源通信的套接字
    sockfd = socket(AF_INET, SOCK_DGRAM)
    # 绑定地址
    IP = sys.argv[1]
    PORT = int(sys.argv[2])
    ADDR = (IP, PORT)
    sockfd.bind(ADDR)
    L_decoded = {}
    L_undecoded = []
    recvNum_and_decodeNum = []
    recv_num = 0
    decoded_num = 0
    print("主机 " + ADDR[0] + ":" + str(ADDR[1]) + " 正在等待数据...\n")
    while True:
        # 接受数据(与tcp不同)
        data, addr = sockfd.recvfrom(4096)

        recv_num += 1
        # 数据解码
        data = data.decode()
        
        m_info_set = set(data.split("##",1)[0].split("@"))
        # 获取码字数据(字符串的字节码)
        m_data = data.split("##",1)[1].encode()
        print("收到码字数据的信息是：", m_info_set)
        print("\n")
        
        # 使用刚刚接收到的数据进行解码
        recv_Handler(m_info_set, m_data, L_decoded, L_undecoded)
        if len(L_decoded) > decoded_num:
            # 当解码个数有变化的时候,记录此时的接受数量与解码数量的关系
            decoded_num = len(L_decoded)
            recvNum_and_decodeNum.append((recv_num, decoded_num))

        # 在未解码的码字中寻找解码机会
        # Redecode_in_undecoded()
        

        print("\n未解码个数: ", len(L_undecoded))
        print("\n")
        print("已解码个数: ", len(L_decoded))

        print("\n------------------------------\n")

        # 若解码完成
        if len(L_decoded) == subsection_num:
            
            print("\n\n解码完成!")
            if (recv_num, subsection_num) not in recvNum_and_decodeNum:
                recvNum_and_decodeNum.append((recv_num, subsection_num))

            need_to_resend_ack = Value('i',True)
            
            p_send_ack = Process(target=send_ack, args=(need_to_resend_ack, sockfd, addr))
            p_confirm_ack = Process(target=confirm_ack, args=(need_to_resend_ack, sockfd, addr))

            p_confirm_ack.start()
            p_send_ack.start()

            p_confirm_ack.join()
            p_send_ack.join()

            # 将解码出的数据存放到txt文件中
            with open("PureFountainCode_Recv" + str(ADDR) + ".txt",'wb') as f:
                data_to_save = sorted(L_decoded.items(),key=lambda x:int(x[0]))
                for line in data_to_save:
                    record = line[1] + "\n".encode()
                    f.write(record)
            print("\n解码数据已经存放在 PureFountainCode_Recv" + str(ADDR) + ".txt 中")

            decode_log = ""
            for i in recvNum_and_decodeNum:
                decode_log += "(%d, %d)," % i
            # 实验次数, 设备id, 实验结果
            content = (exp_time , device_id, decode_log)

            # 插入语句
            SQL = "insert into FountainCode (exp_time, device_id, decode_log) values (%d,%s,'%s');" % content

            # 执行插入语句
            cursor.execute(SQL)

            # 提交
            db.commit()
            print("解码过程信息存放在 10.1.18.79 的数据库 中")
            print("共收到 %d 个码字." % recv_num)
            break
        # print("主机 " + ADDR[0] + ":" + str(ADDR[1]) + " 正在等待数据...\n")

    sockfd.close()




def main():
    # 打开数据库连接
    db = pymysql.connect(host="10.1.18.79",port=3306,user="root",passwd="chain",db="exp_data",charset='utf8')
     
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    # 获取上一次实验的实验次数
    cursor.execute("select exp_time from FountainCode order by id DESC limit 1;")
    db.commit()
    data = cursor.fetchone()
    if data:
        exp_time = data[0] + 1  # 实验次数加 1
    else:
        exp_time = 1
    device_id = sys.argv[1].split(".")[-1]
    p1 = Process(target = recv_from_source, args=(db, cursor, exp_time, device_id))
    p1.start()
    p1.join()

if __name__ == "__main__":
    main()


