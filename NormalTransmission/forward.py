#!/usr/bin/env python3
#encoding=utf-8
from socket import *
from multiprocessing import *
from Xor import *
from config import *
import sys, random, os, time


def recv_from_source():
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
    recv_num = 0

    print("主机 " + ADDR[0] + ":" + str(ADDR[1]) + " 正在等待数据...\n")

    with open("NormalRecv" + str(ADDR) + ".txt",'wb') as f:
        while recv_num != subsection_num:
            # 接受数据(与tcp不同)
            data, addr = sockfd.recvfrom(1024)
            recv_num += 1
            # 数据存储
            f.write(data + "\n".encode())

    # decode_log = ""
    # for i in recvNum_and_decodeNum:
    #     decode_log += "(%d, %d)," % i
    # 实验次数, 设备id, 实验结果
    # content = (exp_time , device_id, decode_log)

    # 插入语句
    # SQL = "insert into Normal_Transmission (exp_time, device_id, decode_log) values (%d,%s,'%s');" % content

    # 执行插入语句
    # cursor.execute(SQL)

    # 提交
    # db.commit()
    # print("解码过程信息存放在 10.1.18.79 的数据库 中")
    print("共收到 %d 个码字." % recv_num)
    print("\n数据已存放在 NormalRecv" + str(ADDR) + ".txt 中")

    sockfd.close()


def main():
    # 打开数据库连接
    # db = pymysql.connect(host="10.1.18.79",port=3306,user="root",passwd="chain",db="exp_data",charset='utf8')
    
    # 使用 cursor() 方法创建一个游标对象 cursor
    # cursor = db.cursor()

    # 获取上一次实验的实验次数
    # cursor.execute("select exp_time from Normal_Transmission order by id DESC limit 1;")
    # db.commit()
    # data = cursor.fetchone()
    # if data:
    #     exp_time = data[0] + 1  # 实验次数加 1
    # else:
    #     exp_time = 1
    # device_id = sys.argv[1].split(".")[-1]

    # p1 = Process(target = recv_from_source, args=(db, cursor, exp_time, device_id))
    p1 = Process(target = recv_from_source)
    p1.start()
    p1.join()


if __name__ == "__main__":
    main()


