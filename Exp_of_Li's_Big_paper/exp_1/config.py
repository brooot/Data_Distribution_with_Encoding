# coding=utf-8
import random
from jsonFile import *


class Config:
    # 发送延迟
    send_delay = 0.3

    # 一代发送的数据条数 , 每一条数据的大小是 68 个字符
    record_num = 300

    # 定义将数据分成几大段, 每一段作为一轮编码发送的数据
    # big_piece_num = 1

    # 每轮发送的数量
    # pieces_each_round = 48

    # big_piece_num = (piece_num // pieces_each_round) + (1 if ((piece_num % pieces_each_round) > (pieces_each_round/2)) else 0)


    # 传输丢失率
    loss_rate = 0

    # 转发层挑选已解码的一度包的概率
    fenzi = 1  # 分子
    fenmu = 3  # 分母

    # 转发层互相发送的端口相对于原始端口的偏移, 不宜小于转发层节点个数
    PortOffset = 100

    # 源端地址
    source_ADDR = ("127.0.0.1", 6060)

    # 目的地地址
    Dest_ADDR = [
        ("127.0.0.1", 7001),
        ("127.0.0.1", 7002),
        ("127.0.0.1", 7003)
    ]

    # 转发层发送延迟
    forward_send_delay = send_delay

    # 获取转发层自身地址
    def get_forward_selfADDR(self, selfAddr):
        if selfAddr not in self.Dest_ADDR:
            print("地址不存在分发列表中.")
            print("addr: ", selfAddr)
            print("destAddr: ", self.Dest_ADDR)
            raise
        return selfAddr[0], selfAddr[1] + self.PortOffset

    # 获取转发层的邻居
    def get_forward_Neighbor(self, selfAddr):
        if selfAddr not in self.Dest_ADDR:
            print("地址不存在分发列表中.")
            raise
        Peer_ADDR = []
        for addr in self.Dest_ADDR:
            if addr != selfAddr:
                Peer_ADDR.append((addr[0], addr[1] + self.PortOffset))
        return Peer_ADDR

    # 依概率发送的函数
    def send_with_loss_prob(self, sockfd, encoded_msg, addr):
        if random.random() > self.loss_rate:
            sockfd.sendto(encoded_msg, addr)

# forward_send_delay = len(Dest_ADDR) * send_delay + 0.2
