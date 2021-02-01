import sys

import Experiment
from config import *
import csv

cfg = Config()


def main():
    min_unit, T_slot, a, b, c = 68, 1, 0.88652179221, 0.25726495726, 0.0073070866
    exp_times = 1  # 实验次数
    record_num = cfg.record_num
    # send_time_list = []
    # 获取分段的数量
    if min_unit == 68:
        piece_num = record_num
    else:
        piece_num = 68 * record_num // min_unit + (1 if (68 * record_num % min_unit) else 0)

    # 获取每轮发送的数量的数组
    # pieces_each_round = 4  # 初始值
    # with open("TimeOFpiecesEachRound.csv", "w", newline="", encoding="utf-8") as datacsv:
    #     csvwriter = csv.writer(datacsv, dialect="excel")
    #     csvwriter.writerow(["pieces_each_round", "已解码个数"])
    #
    #     while pieces_each_round <= piece_num:  # 何时间终止
    #         print(f"\n--------------------------------------------\n")
    #         print(f"\n|        pieces_each_round = %4d           |\n" %(pieces_each_round, ))
    #         print(f"\n--------------------------------------------\n")
    #         send_time = Experiment.run(min_unit, T_slot, a, b, c, pieces_each_round)
    #         send_time_list.append(send_time)
    #         print(send_time_list)
    #         # 保存
    #         csvwriter.writerow([pieces_each_round, send_time])
    #         print("所有轮次发送时间之和:  ", send_time)
    #         pieces_each_round += 2  # 每轮增加的值

    pieces_each_round = piece_num  # 只发送一轮 !!!!!
    print("开始实验...")
    if len(sys.argv) == 1:
        print("自动化")
        for exp_index in range(1, exp_times+1):
            print(f"\n开始第{exp_index}次实验...")
            sendNum = Experiment.run(min_unit, T_slot, a, b, c, pieces_each_round, exp_index, -1)
            print(f"第{exp_index}次实验的发送次数是{sendNum}\n---------------------------")
    elif len(sys.argv) == 2 and sys.argv[1] == 'source':
        print("源端单独运行")
        send_time = Experiment.run(min_unit, T_slot, a, b, c, pieces_each_round, 1, 0)
        print(f"源端运行完毕, 实验的时间是{send_time}\n---------------------------")
    elif len(sys.argv) == 3 and sys.argv[1] == 'forward':
        forward_index = int(sys.argv[2])
        if forward_index > len(cfg.Dest_ADDR):
            print("转发层节点下标超出上限")
        print(f"第{forward_index}个转发层单独运行")
        Experiment.run(min_unit, T_slot, a, b, c, pieces_each_round, 1, forward_index)
        print("转发层运行完毕.")
    else:
        print("""格式错误!
                 自动化: python exp_main.py
                 源  端: python exp_main.py source
                 转发层: python exp_main.py forward 2 (数字表示第几个源端, 需要和config中的地址一一对应)
        """)
    # with open("TimeOFpiecesEachRound.csv", "w", newline="", encoding="utf-8") as datacsv:
    #     csvwriter = csv.writer(datacsv, dialect="excel")
    #     csvwriter.writerow(["发送时间"])
    #     print("开始实验...")
    #     send_time = Experiment.run(min_unit, T_slot, a, b, c, pieces_each_round)
    #     send_time_list.append(send_time)
    #     print("send_time_list: ", send_time_list)
    #     # 保存
    #     csvwriter.writerow([send_time])
    #     print("发送时间:  ", send_time)


if __name__ == "__main__":
    main()
