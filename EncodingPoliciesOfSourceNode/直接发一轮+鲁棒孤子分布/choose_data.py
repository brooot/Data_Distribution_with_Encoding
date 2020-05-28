# encoding=UTF-8
from Xor import *
from config import *
import operator
import random
import math
# 每行的长度是:68
# 每行的长度是:68
# (136, 136)


bytes_list = []


def get_bytesList_of_a_generation():  # k 表示读取的数据的条数
    global bytes_list
    if not bytes_list:
        bytes_list = []  # 一代数据列表 ['一条记录','一条记录',..., '一条记录'] 一代共 40 条
        with open("data.txt", "rb") as f:
            all_bytes = b""
            for i in range(record_num):  # 一代 k 片数据, 每一片表示一条68字符的完整的记录
                all_bytes += f.readline()
            for i in range(full_num):
                bytes_list.append(all_bytes[:smallest_piece])
                all_bytes = all_bytes[smallest_piece:]
            if left:
                bytes_list.append(all_bytes + "=".encode()
                                  * (smallest_piece - left))

        print("分段：")
        _idx = 1
        for i in bytes_list:
            print("%3d: " % _idx, end='')
            print(i)
            _idx += 1

        return bytes_list  # 返回记录的字节码列表
    else:
        return bytes_list


# 二进制分布
def get_Bit_distribution():
    p = {}
    p[1] = 1/pow(2, 1)
    pre = p[1]
    for i in range(2, piece_num):
        p[i] = 1/pow(2, i) + pre
        pre = p[i]
    p[piece_num] = 1/pow(2, piece_num-1) + p[piece_num-1]
    return p



# 理想孤子分部(仅供鲁棒孤子分布计算调用)
def get_idealSolition_degree_distribution():
    p = {0: 0, 1: 1 / piece_num}
    for i in range(2, piece_num + 1):
        p[i] = 1/i/(i-1)
        pre = p[i]
    return p  # 返回度分布的概率字典



# 鲁棒孤子分布
def get_robustSolition_degree_distribution():
    c = 0.5
    delta = loss_rate
    p_ideal = get_idealSolition_degree_distribution()
    p = {0:0}
    R = c * math.log(piece_num) * math.sqrt(piece_num)
    tau = [0]
    for i in range(1, math.floor(piece_num / R)):
        tau.append(R / i / piece_num)
    if delta == 0:
        raise Exception("丢失率 loss_rate 不能为 0.")
    tau.append(R * math.log(R / delta) / piece_num)
    while len(tau) < piece_num + 1:
        tau.append(0)
    beta = 0
    for i in range(1, piece_num + 1):
        beta += p_ideal[i] + tau[i]
    for i in range(1, piece_num + 1):
        p[i] = (p_ideal[i] + tau[i]) / beta + p[i-1]
        # print(p[i])
    return p





# 获取随机的编码度
def get_Degree(p):
    # 获取随机数, 根据它依概率所处的 0-1 的相对位置来获取此次的度
    rand_num = random.random()
    for i in range(1, piece_num + 1):
        if(p[i] >= rand_num):  # 返回匹配到的度
            return i


def data_coding(source_data, d):
    m_info = ""
    codeList = []
    for _id in random.sample(range(1, piece_num+1), d):
        # 添加码字信息
        if(m_info == ""):
            m_info += str(_id)
        else:
            m_info += "@" + str(_id)
        # 码子编码
        codeList.append(source_data[_id-1])
    m_code = bytesList_Xor_to_Bytes(codeList)
    # 已经编码后的字节码数据
    data = (m_info + "##").encode() + m_code
    print("发送数据的编码信息: " + m_info + "\n---------------------------\n")
    return data


# 获取编码后的数据  这是度分布的实验
def get_encoded_data(p):
    # 获取一代的字节码列表
    global bytes_list
    if not bytes_list:
        print("-----------------------------------")
        bytes_list = get_bytesList_of_a_generation()
    # 获取随机的编码度
    encode_degree = get_Degree(p)
    print("编码度: ", encode_degree)
    return data_coding(bytes_list, encode_degree)


def get_forward_data_1_degree(L_decoded, L_undecoded):
    if len(L_decoded) > 0 and len(L_undecoded) > 0:
        ran_Int = random.randint(1, 2)
        if ran_Int == 1:
            m_info = random.sample(L_decoded.keys(), 1)[0]  # 随机一个字典中的key，第二个参数为限制个数
            # 添加码字信息
            m_code = L_decoded[m_info]
            data = (m_info + "##").encode() + m_code
            print("转发信息:", m_info)
            return data
        else:
            m_info = ""
            a = random.sample(list(L_undecoded), 1)  # 从中随机选出一个编码包
            for i in a[0][0]:
                if (m_info == ""):
                    m_info += str(i)
                else:
                    m_info += "@" + str(i)
            print("转发信息:", m_info)
            data = (m_info + "##").encode() + a[0][1]
            return data
    elif len(L_decoded)>0:
        m_info = random.sample(L_decoded.keys(), 1)[0]  # 随机一个字典中的key，第二个参数为限制个数
        # 添加码字信息
        m_code = L_decoded[m_info]
        data = (m_info + "##").encode() + m_code
        print("转发信息:", m_info)
        return  data
    elif len(L_undecoded)>0:
        m_info = ""
        a = random.sample(list(L_undecoded), 1)  # 从中随机选出一个编码包
        print(a)
        for i in a[0][0]:
            if (m_info == ""):
                m_info += str(i)
            else:
                m_info += "@" + str(i)
        print("转发信息:", m_info)
        data = (m_info + "##").encode() + a[0][1]
        return data