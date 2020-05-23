import random
# 一代发送的编码分段大小
subsection_num = 30

# 发送延迟
send_delay = 0.1


# 源端发送延迟
send_delay = 0.5


# 传输丢失率
loss_rate = 0

# 源地址
source_ADDR = ("127.0.0.1", 6000)

# 目的地址
Dest_ADDR = [
                    ("127.0.0.1", 7001),
                    ("127.0.0.1", 7002),
                    ("127.0.0.1", 7003),
                    # ("127.0.0.1", 7004),
            ]



# 依概率发送的函数
def send_with_loss_prob(sockfd, encoded_msg, addr):
     if random.random() > loss_rate:
          sockfd.sendto(encoded_msg, addr)
     else:
          print("发送丢失...")