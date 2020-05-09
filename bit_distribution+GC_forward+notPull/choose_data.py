#encoding=UTF-8
from Xor import *
from config import *
import operator
# 每行的长度是:68
# 每行的长度是:68
# (136, 136)


bytes_list = []

# 一代中切片的个数是40
# 获取一代中的 k 条数据的编码后的字节码列表
def get_bytesList_of_a_generation(k):
    global bytes_list
    file_Lines = []  # 一代数据列表 ['一条记录','一条记录',..., '一条记录'] 一代共 40 条
    num = 0
    with open("data.txt", "r") as f:
        for i in range(k):  # 一代 k 片数据, 每一片表示一条68字符的完整的记录
            line = f.readline().strip('\n')
            file_Lines.append(line.encode())
    bytes_list = file_Lines
    return bytes_list  # 返回记录的字节码列表


# 二进制分布
def get_Bit_distribution(k):
    p = {}
    p[1] = 1/pow(2,1)
    pre = p[1]
    for i in range(2, k):
        p[i] = 1/pow(2,i) + pre
        pre = p[i]
    p[k] = 1/pow(2, k-1) + p[k-1]
    return p

# 根据分段的个数k, 确定度的概率分布
def get_degree_distribution(k):
    p = {}
    p[1] = 1/2
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



# 获取编码后的数据  这是度分布的实验
def get_encoded_data(k, p):
    # 获取一代的字节码列表
    global bytes_list
    if not bytes_list:
        get_bytesList_of_a_generation(k)
    # 获取随机的编码度
    encode_degree = get_Degree(k, p)

    print("编码度: ",encode_degree)
    return data_coding(bytes_list, encode_degree)


# 工具类：得到源端的度时刻转换序列
def getDegreeSquque(nsource):
    time_queue = []
    for i in range(5000):
        if i < 129 * nsource:
            time_queue.append(1)
        elif i >= 129 * nsource and i < 200 * nsource:
            time_queue.append(2)
        elif i >= 200 * nsource and i < 300 * nsource:
            time_queue.append(3)
        elif i >= 300 * nsource and i < 338 * nsource:
            time_queue.append(4)
        elif i >= 338 * nsource and i < 353 * nsource:
            time_queue.append(5)
        elif i >= 353 * nsource and i < 362 * nsource:
            time_queue.append(6)
        else:
            time_queue.append(7)
    return time_queue

# 工具类，转发层度时刻转换序列
def getDegreeSququeGC(nsource):
    time_queue = []
    for i in range(5000):
        if i < 70 * nsource:
            time_queue.append(1)
        elif i >= 70 * nsource and i < 120 * nsource:
            time_queue.append(2)
        elif i >= 120 * nsource and i < 200 * nsource:
            time_queue.append(3)
        elif i >= 200 * nsource and i < 270 * nsource:
            time_queue.append(4)
        elif i >= 270 * nsource and i < 350 * nsource:
            time_queue.append(5)
        elif i >= 350 * nsource and i < 450 * nsource:
            time_queue.append(6)
        elif i >= 450 * nsource and i < 550 * nsource:
            time_queue.append(7)
        else:
            time_queue.append(8)
    return time_queue

# 转发层编码使用的方法，假如选出一个包，这个包比我的度小，就ok
# time_queue  时间序列  L_decoded 已解码序列  L_undecoded未解码序列   n_index时间转换序列的轮次
def get_forward_encoded_data(nei_Need_codes, time_queue, L_decoded, L_undecoded, n_index):
    m_info = ""
    if time_queue[n_index] == 1: # 序列为1
        if len(L_decoded) == 0: # 没有已解码的
            a = L_undecoded[0]  # 取未解码中的第一个包发出去
            for i in list(a[0]):
                if (m_info == ""):
                    m_info += str(i)
                else:
                    m_info += "@" + str(i)
            data = (m_info + "##").encode() + a[1]
            return data
        elif nei_Need_codes:
            for key in L_decoded.keys(): # 优先取出对方要且我有的发给他
                if key in nei_Need_codes:
                    return (key + "##").encode() + L_decoded[key]
        else:
            a = random.sample(L_decoded.keys(), 1)  # 随机一个字典中的key，第二个参数为限制个数
            b = a[0]
            data = (b + "##").encode() + L_decoded[b]
            return  data

    else:
        m_info_list = []
        degreeMax = time_queue[n_index]
        codeList = []
        maxIter = 50
        _iter = 0
        only_undecoded = False # 已解码中没有对方需要的
        while degreeMax > 0 and _iter < maxIter:
            _iter += 1
            # 随机数为1的话就选择从已解码中选取
            if not only_undecoded and random.randint(1,fenmu) <= fenzi:
                added = False # 记录是否找到对方没有的一度包
                for key in L_decoded.keys(): # 优先取出对方要且我有的发给他
                    if key in nei_Need_codes and key not in m_info_list:
                        m_info_list.append(key)
                        if (m_info == ""):
                            m_info += str(key)
                        else:
                            m_info += "@" + str(key)
                        codeList.append(L_decoded[key])
                        degreeMax -= 1
                        added = True

                if not added: # 如果没找到对方要的就标记只发未解码中的
                    only_undecoded = True
                    
            else: # 从未解码中找
                if len(L_undecoded) != 0: # 如果有未解码的码字
                    # 先找未解码中全都是对方需要的码字
                    added = False # 标记是否找到全为对方需要的未解码包
                    for info_set, data_byte in L_undecoded:
                        if info_set - set(nei_Need_codes) == set() and len(info_set)<=degreeMax: # 此未解码包中尽是对方没有的
                            added = True
                            degreeMax -= len(info_set)
                            for i in info_set: # 记录info信息
                                if (m_info == ""):
                                    m_info += str(i)
                                else:
                                    m_info += "@" + str(i)

                            codeList.append(data_byte) # 添加待编码的码字


                    # 未解码中没有全是对方需要的包的情况
                    if not added:
                        a = random.sample(list(L_undecoded), 1)  # 从中随机选出一个编码包
                        if len(a[0][0]) <= degreeMax:
                            degreeMax = degreeMax - len(a[0][0])
                            codeList.append(a[0][1])
                            for i in a[0][0]:
                                if (m_info == ""):
                                    m_info += str(i)
                                else:
                                    m_info += "@" + str(i)
                        else:
                            degreeMax -= 1
                
        if len(codeList) > 0:
            m_code = bytesList_Xor_to_Bytes(codeList)
            # 已经编码后的字节码数据
            data = (m_info + "##").encode() + m_code
            return  data
            print("交换的数据内容: ", data)
        else:
            return None


def get_forward_encoded_data_1(time_queue,L_decoded,L_undecoded,n_index):
    if len(L_undecoded)>0:
        m_info = ""
        a = L_undecoded[0]  # 随机一个字典中的key，第二个参数为限制个数
        for i in list(a[0]):
            if (m_info == ""):
                m_info += str(i)
            else:
                m_info += "@" + str(i)
        data = (m_info + "##").encode() + a[1]
        # print("data: ", data)
        return data
    elif len(L_decoded)>0:
        key1 = L_decoded.keys()[0]
        value1 = L_decoded[key1]
        data =(key1 + "##").encode() + value1
        # print("data: ", data)
        return data


# 转发层编码使用的方法,一直到我最大的最下于度的时候
# time_queue  时间序列  L_decoded 已解码序列  L_undecoded未解码序列   n_index时间转换序列的轮次
def get_forward_encoded_data_oldGC(time_queue,L_decoded,L_undecoded,n_index):
    if len(L_decoded) == 0 and len(L_undecoded) == 0:
        return  "null"
    if time_queue[n_index] == 1:
        if len(L_decoded) == 0:
            return "null"
        a = random.sample(L_decoded.keys(), 1)  # 随机一个字典中的key，第二个参数为限制个数
        b = a[0]
        data = (b + "##").encode() + L_decoded[b]
        return  data
    else:
        degreeMax = time_queue[n_index]
        m_info = ""
        codeList = []
        maxIter = 50
        iter = 0
        while degreeMax > 0 and iter < maxIter:
            iter+=1
            # 随机数为1的话就选择从已解码中选取
            if random.randint(1,2) == 1:
                a = random.sample(L_decoded.keys(), 1)  # 随机一个字典中的key，第二个参数为限制个数
                b = a[0]
                degreeMax-=1
                # 添加码字信息
                codeList.append(L_decoded[b])
                if (m_info == ""):
                    m_info += str(b)
                else:
                    m_info += "@" + str(b)


            else:
                if len(L_undecoded) != 0:
                    a = random.sample(L_undecoded, 1)
                    if degreeMax-len(a[0][0]) >=0:
                        degreeMax = degreeMax - len(a[0][0])
                        codeList.append(a[0][1])
                        for i in a[0][0]:
                            if (m_info == ""):
                                m_info += str(i)
                            else:
                                m_info += "@" + str(i)
                    else:
                        continue
                else:
                    continue
        if len(codeList) == 0:
            return  "null"
        m_code = bytesList_Xor_to_Bytes(codeList)
        # 已经编码后的字节码数据
        data = (m_info + "##").encode() + m_code
        return  data

# 获取编码后的数据 这是  度时间转换序列  nsource是代表有几个转发层节点
def get_encoded_data_sort(k, p,n,nsource):
    # 获取一代的字节码列表k 是分成的总包数
    bytes_list = get_bytesList_of_a_generation(k)
    # 获取随机的编码度
    # encode_degree = get_Degree(k, p)

    time_queue = getDegreeSquque(nsource)

    m_info = ""
    codeList = []
    for _id in random.sample(range(1,len(bytes_list)+1), time_queue[n]):
        # 添加码字信息
        if(m_info == ""):
            m_info += str(_id)
        else:
            m_info += "@" + str(_id)
        # 码子编码
        codeList.append(bytes_list[_id-1])
    m_code = bytesList_Xor_to_Bytes(codeList)
    # 已经编码后的字节码数据
    data = (m_info + "##").encode() + m_code
    print("发送数据的编码信息: " + m_info + "\n---------------------------\n")
    print("编码度: ",time_queue[n])
    return data