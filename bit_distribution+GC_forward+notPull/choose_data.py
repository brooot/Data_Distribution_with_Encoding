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
# def get_bytesList_of_a_generation(k):
#     global bytes_list
#     file_Lines = []  # 一代数据列表 ['一条记录','一条记录',..., '一条记录'] 一代共 40 条
#     with open("data.txt", "r") as f:
#         for i in range(k):  # 一代 k 片数据, 每一片表示一条68字符的完整的记录
#             line = f.readline().strip('\n')
#             file_Lines.append(line.encode())
#     bytes_list = file_Lines
#     return bytes_list  # 返回记录的字节码列表

def get_bytesList_of_a_generation(k): # k 表示读取的数据的条数
    global bytes_list
    if not bytes_list:
        bytes_list = []  # 一代数据列表 ['一条记录','一条记录',..., '一条记录'] 一代共 40 条
        with open("data.txt", "rb") as f:
            all_bytes = b""
            for i in range(k):  # 一代 k 片数据, 每一片表示一条68字符的完整的记录
                all_bytes += f.readline()
            for i in range(full_num):
                bytes_list.append(all_bytes[:smallest_piece])
                all_bytes = all_bytes[smallest_piece:]
            if left:
                bytes_list.append(all_bytes + "=".encode()*(smallest_piece - left))
        # print(bytes_list)
        return bytes_list  # 返回记录的字节码列表
    else:
        return bytes_list

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
    for _id in random.sample(range(1,piece_num+1), d):
        # 添加码字信息
        if(m_info == ""):
            m_info += str(_id)
        else:
            m_info += "@" + str(_id)
        # 码子编码
        print("source_data:", source_data)
        print("_id:", _id)
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
        bytes_list = get_bytesList_of_a_generation(k)
    # 获取随机的编码度
    encode_degree = get_Degree(k, p)
    print("piece_num: ", piece_num)
    print("encode_degree")
    encode_degree = get_Degree(k, p)
    while encode_degree > piece_num:
        encode_degree = get_Degree(k, p)    
        print("encode_degree", encode_degree)
        print("--")

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
# nei_Need_codes 邻居需要的码字 time_queue  时间序列  L_decoded 已解码序列  L_undecoded未解码序列   n_index时间转换序列的轮次
def get_forward_encoded_data(nei_Need_codes, time_queue, L_decoded, L_undecoded, n_index):
    m_info = "" # 记录编码的码字信息
    if time_queue[n_index] == 1: # 度为1
        if len(L_decoded) == 0: # 没有已解码的
            a = L_undecoded[0]  # 取未解码中的第一个包发出去
            for i in list(a[0]):
                if (m_info == ""):
                    m_info += str(i)
                else:
                    m_info += "@" + str(i)
            data = (m_info + "##").encode() + a[1]
            return data
        # 如果对方有需要的包,不为空[]
        elif nei_Need_codes: 
            for key in L_decoded.keys(): # 优先取出对方要且我有的(已解码)发给他
                if key in nei_Need_codes:
                    return (key + "##").encode() + L_decoded[key]
        # 无对方需要的码字信息
        else: 
            a = random.sample(L_decoded.keys(), 1)  # 随机一个已解码的码字
            b = a[0]
            data = (b + "##").encode() + L_decoded[b]
            return  data

    # 编码度超过 1
    else:
        m_info_list = [] # 记录在找全是对方需要的码字的码字信息过程中已经添加的码字信息, 如果已经添加了就不再添加
        degreeMax = time_queue[n_index] # 根据度时刻序列以及序号, 得到当前最大度
        codeList = [] # 记录需要被异或编码的码字字节码, 当全部被添加后进行编码
        maxIter = 50 # 最大迭代查找次数 50 次
        _iter = 0 # 记录迭代次数
        only_undecoded = False # 已解码中是否没有对方需要的, 是否只需要发送未解码中的
        while degreeMax > 0 and _iter < maxIter:
            _iter += 1
            # 随机数为1的话就选择从已解码中选取
            if not only_undecoded and random.randint(1,fenmu) <= fenzi:
                has_satisfying_1_degree_cw = False # 记录是否找到对方没有的一度包
                
                for key in L_decoded.keys(): # 遍历我的已解码列表, 优先取出对方要且我有的发给他
                    if key in nei_Need_codes and key not in m_info_list: # 我已解码 & 对方需要 & 不会重复添加
                        m_info_list.append(key) # 记录我以添加该码字, 避免重复添加
                        if (m_info == ""):
                            m_info += str(key)
                        else:
                            m_info += "@" + str(key)
                        codeList.append(L_decoded[key])
                        degreeMax -= 1
                        has_satisfying_1_degree_cw = True

                if not has_satisfying_1_degree_cw: # 如果没找到对方要的就标记只发未解码中的, 因为发送其他的一度包都是对方有的, 没有必要发送
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