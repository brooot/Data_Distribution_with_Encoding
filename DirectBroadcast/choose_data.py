#encoding=UTF-8
import random
from Xor import *

# 每行的长度是:68
# 每行的长度是:68
# (136, 136)

# 一代中切片的个数是40

# 获取一代中的 k 条数据的编码后的字节码列表
def get_bytesList_of_a_generation(k):
    file_Lines = []  # 一代数据列表 ['一条记录','一条记录',..., '一条记录'] 一代共 40 条
    num = 0
    with open("data.txt", "r") as f:
        for i in range(k):  # 一代 k 片数据, 每一片表示一条68字符的完整的记录
            line = f.readline().strip('\n')
            file_Lines.append(line.encode())
    return file_Lines  # 返回记录的字节码列表


# 根据分段的个数k, 确定度的概率分布
def get_degree_distribution(k):
    p = {}
    p[1] = 1/k
    pre = p[1]
    for i in range(2, k + 1):
        p[i] = 1/i/(i-1) + pre
        pre = p[i]
    return p  # 返回度分布的概率字典


# 获取随机的编码度
def get_Degree(k, p):
    # 获取随机数, 根据它依概率所处的 0-1 的相对位置来获取此次的度
    rand_num = random.random()
    for i in range(1, k + 1):
        if(p[i] >= rand_num):  # 返回匹配到的度
            return i


def data_coding(source_data, d):
    m_info = ""
    codeList = []
    for _id in random.sample(range(1,len(source_data)+1), d):
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


# 获取编码后的数据
def get_encoded_data(k, p):
    # 获取一代的字节码列表
    bytes_list = get_bytesList_of_a_generation(k)
    # 获取随机的编码度
    encode_degree = get_Degree(k, p)
    # if encode_degree > 5:
    #     encode_degree = 1
    print("编码度: ",encode_degree)
    return data_coding(bytes_list, encode_degree)