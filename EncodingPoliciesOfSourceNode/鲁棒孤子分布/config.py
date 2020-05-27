import random

# 一代发送的数据条数 , 每一条数据的大小是 67 个字符
record_num = 10

# 最小编码单元大小 (如果按照每一条数据的大小来算的话是 68)
smallest_piece = 68

# 传输丢失率
loss_rate = 0

# 转发层挑选已解码的一度包的概率
# fenzi = 1 # 分子
# fenmu = 3 # 分母

# 记录能直接被填满的个数
full_num = 68*record_num //smallest_piece

# 余数
left = 68*record_num % smallest_piece

# 记录分段的个数, 在运行的时候被赋值
piece_num = full_num + (1 if left else 0)


# 转发层互相发送的端口相对于原始端口的偏移, 不宜小于转发层节点个数
PortOffset = 100

source_ADDR = ("127.0.0.1", 6000)

Dest_ADDR = [
                    ("127.0.0.1", 7001),
                    ("127.0.0.1", 7002),
                    ("127.0.0.1", 7003),
                    # ("127.0.0.1", 7004),
                ]
# 源端发送延迟
send_delay = 0.5

# 转发层发送延迟
forward_send_delay = send_delay 
# forward_send_delay = len(Dest_ADDR) * send_delay + 0.2

# 当已解码的比例超过该值时, 开始拉取未解码的内容.
# ratio_to_pull = 0 # 此处不要修改, 因为总是需要告知自己的未解码数据给对方



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
