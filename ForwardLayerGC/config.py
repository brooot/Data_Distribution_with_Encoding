import random

# 一代发送的编码分段大小
subsection_num = 50

# 端口偏移
PortOffset = 100


source_ADDR = ("127.0.0.1", 6000)

Dest_ADDR = [
                    ("127.0.0.1", 7001),
                    ("127.0.0.1", 7002),
                    ("127.0.0.1", 7003),
                    ("127.0.0.1", 7004),
                ]
# 源端发送延迟
send_delay = 0

# 转发层发送延迟
forward_send_delay = len(Dest_ADDR) * send_delay + 0.2

# 当已解码的比例超过该值时, 开始拉取未解码的内容.
ratio_to_pull = 0.9

# 传输丢失率
loss_rate = 0

# 获取转发层自身地址
def get_forward_selfADDR(selfAddr):
     if selfAddr not in Dest_ADDR:
          print("地址不存在分发列表中.")
          raise
     return (selfAddr[0], selfAddr[1]+PortOffset)


# 获取转发层的邻居
def get_forward_Neighbor(selfAddr):
     if selfAddr not in Dest_ADDR:
          print("地址不存在分发列表中.")
          raise
     Peer_ADDR = []
     Dest_ADDR.remove(selfAddr)
     for addr in Dest_ADDR:
          Peer_ADDR.append((addr[0], addr[1]+PortOffset))
     return Peer_ADDR

# 依概率发送的函数
def send_with_loss_prob(sockfd, encoded_msg, addr):
     if random.random() > loss_rate:
          sockfd.sendto(encoded_msg, addr)
     else:
          print("发送丢失...")
