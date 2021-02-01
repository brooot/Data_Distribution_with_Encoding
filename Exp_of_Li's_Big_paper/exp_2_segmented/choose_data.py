# encoding=UTF-8
from Xor import *
from config import *
import operator
import random
import math
import time

# 每行的长度是:68
# 每行的长度是:68
# (136, 136)
cfg = Config()


def get_bytesList_of_a_generation(min_unit, piece_num):  # k 表示读取的数据的条数
    print("准备获取数据")
    if min_unit == 68:
        bt_list = []  # 一代数据列表 ['一条记录','一条记录',..., '一条记录'] 一代共 40 条
        with open("data.txt", "rb") as f:
            # all_bytes = b""
            for i in range(cfg.record_num):  # 一代 k 片数据, 每一片表示一条68字符的完整的记录
                bt_list.append(f.readline())
        print("----------------------  获取一波数据  68 ------------------")
        return bt_list  # 返回记录的字节码列表
    else:
        bt_list = []  # 一代数据列表 ['一条记录','一条记录',..., '一条记录'] 一代共 40 条
        full_num = 68 * cfg.record_num // min_unit
        left = 68 * cfg.record_num % min_unit
        all_bytes = ""
        with open("data.txt", "r") as f:
            data = f.readlines(cfg.record_num * 68)
            # for i in range(len(data)):
            #     print (i)
            #     data[i] = data[i].rstrip('\n')
            for line in data:
                all_bytes += line
            all_bytes = all_bytes.encode()
            for i in range(full_num):
                bt_list.append(all_bytes[:min_unit])
                all_bytes = all_bytes[min_unit:]

            if left:
                while (len(all_bytes) != min_unit):
                    all_bytes += "=".encode()
                print(len(bt_list))
                bt_list.append(all_bytes)
        print("----------------------  获取一波数据 68+---------------------")
        return bt_list  # 返回记录的字节码列表


# 理想孤子分部(仅供鲁棒孤子分布计算调用)
def get_idealSolition_degree_distribution(piece_num):
    p = {0: 0, 1: 1 / piece_num}
    for i in range(2, piece_num + 1):
        p[i] = 1 / i / (i - 1)
        pre = p[i]
    return p  # 返回度分布的概率字典


# 鲁棒孤子分布
def get_robustSolition_degree_distribution(piece_num):
    c = 0.5
    delta = 0.03
    p_ideal = get_idealSolition_degree_distribution(piece_num)
    p = {0: 0}
    R = c * math.log(piece_num) * math.sqrt(piece_num)
    tau = [0]
    if R == 0:
        raise Exception("R=0")
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
        p[i] = (p_ideal[i] + tau[i]) / beta + p[i - 1]
        # print(p[i])
    return p



# 用于实验三新度分布, 获取未累加的鲁棒孤子分布
def get_raw_robustSolition_degree_distribution(piece_num):
    c = 0.05
    delta = 0.05
    p_ideal = get_idealSolition_degree_distribution(piece_num)
    p = {0: 0}
    R = c * math.log(piece_num) * math.sqrt(piece_num)
    tau = [0]
    if R == 0:
        print("piece_num make R=0, piece_num = ", piece_num)
        raise Exception("R=0")
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
        p[i] = (p_ideal[i] + tau[i]) / beta
        # print(p[i])
    return p


def get_exponentialSolition_degree_distribution(piece_num):
    p = {0: 0, 1: 1 / 4, 2 : 1 / 2}
    for i in range(3, piece_num + 1):
        p[i] = 1/math.pow( 2, i )
    return p  # 返回度分布的概率字典

# 实验三新的度分布
def get_newSolition_degree_distribution(piece_num):
    x = 1
    y = 0.5
    p_e = get_exponentialSolition_degree_distribution(piece_num)
    p_r = get_raw_robustSolition_degree_distribution(piece_num)
    # print (p_r[1]*4)
    O = 0
    q = {0:0}
    for i in range(1, piece_num + 1):
        O = O + x * p_e[i] + y * p_r[i]
    for i in range(1, piece_num + 1):
        q[i] = (x * p_e[i] + y * p_r[i]) / O + q[i-1]
    return q



# 获取实验二编码数据
def get_Exp2_data(L_decoded, piece_num):
    divideRatio = 0.5  # 切分点
    # 获取已解码个数
    decode_num = len(L_decoded)
    if decode_num == 0:
        return None
    if decode_num == 1:
        return get_rand_package_from_decoded(L_decoded)
    
    # 获取第一个度分布
    if decode_num < divideRatio * piece_num:
        p = get_robustSolition_degree_distribution(decode_num)
    # 获取第二个度分布
    else:
        p = get_newSolition_degree_distribution(decode_num)
    encoded_Data = get_encoded_data(decode_num, list(L_decoded.values()), p)
    return encoded_Data


# 随机选择已解码中或未解码中的包
def get_rand_package_from_decoded_or_undecoded(L_decoded, L_undecoded):
    # 判断是否都为空
    if len(L_decoded) == 0 and len(L_undecoded) == 0: # 都为空返回None
        return None
    elif len(L_decoded) == 0:
        return get_rand_package_from_undecoded(L_undecoded)
    elif len(L_undecoded) == 0:
        return get_rand_package_from_decoded(L_decoded)
    else:
        return get_rand_package_from_undecoded(L_undecoded) if random.randint(0,1) == 0 else get_rand_package_from_decoded(L_decoded)


# 从已解码中随机获取一个包
def get_rand_package_from_decoded(L_decoded):
    a = random.sample(L_decoded.keys(), 1)  # 随机一个已解码的码字
    b = a[0]
    data = (b + "##").encode() + L_decoded[b]
    return data


# 从未解码中随机获取一个包
def get_rand_package_from_undecoded(L_undecoded):
    a = random.sample(list(L_undecoded), 1)  # 从中随机选出一个编码包
    m_code = a[0][1]
    m_info = ""
    for i in a[0][0]:
        if (m_info == ""):
            m_info += str(i)
        else:
            m_info += "@" + str(i)
    data = (m_info + "##").encode() + m_code
    return data


# 使用遗传算法的代码
def get_forward_GA_data(nei_Need_codes, u, L_decoded, L_undecoded, _a, _b, _c):
    # print("called", time.time())
    m_info = ""  # 记录编码的码字信息
    if nei_Need_codes:

        dist = int(_a * (u ** _b) + _c * u + 1)  # 获取距离
        max_set_len = 0
        fit_set = set()
        fit_data = b""
        for info_set, data in L_undecoded:
            if len(info_set) <= 2 * dist:
                valuable_info = []  # 未解码中对方需要的码字info
                # 计算info_set的距离
                for i in info_set:
                    if i in nei_Need_codes:
                        valuable_info.append(i)
                if max_set_len < len(valuable_info) <= dist:
                    max_set_len = len(info_set)
                    fit_set = info_set
                    fit_data = data
                if max_set_len == dist:
                    break
        # 找到恰好的距离
        if max_set_len == dist:
            # 返回该数据
            for i in list(fit_set):
                if m_info == "":
                    m_info += str(i)
                else:
                    m_info += "@" + str(i)
            # print(f"u = {u}, dist = {dist}, m_info = {m_info}")
            return (m_info + "##").encode() + fit_data
        # 没有找到正好的dist的数据, 比dist小
        else:
            # 获取已经编码的码字信息m_info
            for i in list(fit_set):
                if m_info == "":
                    m_info += str(i)
                else:
                    m_info += "@" + str(i)
            # 在已解码中找对方需要的进行编码
            L_iterDecoded = L_decoded
            for key in L_iterDecoded.keys():
                if len(m_info) > 2 * dist:
                    break
                else:
                    if key not in fit_set and key in nei_Need_codes:
                        if m_info == "":
                            m_info += str(key)
                        else:
                            m_info += "@" + str(key)
                        if len(fit_data) > 0:
                            fit_data = bytesList_Xor_to_Bytes([fit_data, L_decoded[key]])
                        else:
                            fit_data = L_decoded[key]
                        max_set_len += 1
                        if max_set_len == dist:
                            break
            if max_set_len == 0:
                if len(L_undecoded):
                    a = L_undecoded[0]  # 取未解码中的第一个包发出去
                    for i in list(a[0]):
                        if m_info == "":
                            m_info += str(i)
                        else:
                            m_info += "@" + str(i)
                    data = (m_info + "##").encode() + a[1]
                    # print(f"u = {u}, dist = {dist}, m_info = {m_info}")
                    return data
                else:
                    return None
            # print(f"u = {u}, dist = {dist}, m_info = {m_info}")
            return (m_info + "##").encode() + fit_data
    # 不知道对方需要什么
    else:
        if len(L_decoded):
            a = random.sample(L_decoded.keys(), 1)  # 随机一个已解码的码字
            b = a[0]
            data = (b + "##").encode() + L_decoded[b]
            return data
        elif len(L_undecoded):
            a = L_undecoded[0]  # 取未解码中的第一个包发出去
            for i in list(a[0]):
                if m_info == "":
                    m_info += str(i)
                else:
                    m_info += "@" + str(i)
            data = (m_info + "##").encode() + a[1]
            return data
        else:
            return None


# 获取随机的编码度
def get_Degree(piece_num, p):
    # 获取随机数, 根据它依概率所处的 0-1 的相对位置来获取此次的度
    rand_num = random.random()
    for i in range(1, piece_num + 1):
        if p[i] >= rand_num:  # 返回匹配到的度
            return i


def data_coding(piece_num, source_data, d):
    m_info = ""
    codeList = []
    for _id in random.sample(range(1, piece_num + 1), d):
        # 添加码字信息
        if m_info == "":
            m_info += str(_id)
        else:
            m_info += "@" + str(_id)
        # 码子编码
        codeList.append(source_data[_id - 1])
    m_code = bytesList_Xor_to_Bytes(codeList)
    # 已经编码后的字节码数据
    data = (m_info + "##").encode() + m_code
    # print("发送数据的编码信息: " + m_info + "\n---------------------------\n")
    return data


# 获取编码后的数据  这是度分布的实验
def get_encoded_data(piece_num, byte_LIST, p):
    # 获取随机的编码度
    encode_degree = get_Degree(piece_num, p)
    return data_coding(piece_num, byte_LIST, encode_degree)


# 工具类：得到源端的度时刻转换序列
def getDegreeSquque(nsource):
    time_queue = []
    for i in range(5000):
        if i < 129 * nsource:
            time_queue.append(1)
        elif 129 * nsource <= i < 200 * nsource:
            time_queue.append(2)
        elif 200 * nsource <= i < 300 * nsource:
            time_queue.append(3)
        elif 300 * nsource <= i < 338 * nsource:
            time_queue.append(4)
        elif 338 * nsource <= i < 353 * nsource:
            time_queue.append(5)
        elif 353 * nsource <= i < 362 * nsource:
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
        elif 70 * nsource <= i < 120 * nsource:
            time_queue.append(2)
        elif 120 * nsource <= i < 200 * nsource:
            time_queue.append(3)
        elif 200 * nsource <= i < 270 * nsource:
            time_queue.append(4)
        elif 270 * nsource <= i < 350 * nsource:
            time_queue.append(5)
        elif 350 * nsource <= i < 450 * nsource:
            time_queue.append(6)
        elif 450 * nsource <= i < 550 * nsource:
            time_queue.append(7)
        else:
            time_queue.append(8)
    return time_queue


# 转发层编码使用的方法，假如选出一个包，这个包比我的度小，就ok
# nei_Need_codes 邻居需要的码字 time_queue  时间序列  L_decoded 已解码序列  L_undecoded未解码序列   n_index时间转换序列的轮次
def get_forward_encoded_data(nei_Need_codes, time_queue, L_decoded, L_undecoded, n_index):
    m_info = ""  # 记录编码的码字信息
    if time_queue[n_index] == 1:  # 度为1
        if len(L_decoded) == 0:  # 没有已解码的
            a = L_undecoded[0]  # 取未解码中的第一个包发出去
            for i in list(a[0]):
                if m_info == "":
                    m_info += str(i)
                else:
                    m_info += "@" + str(i)
            data = (m_info + "##").encode() + a[1]
            return data
        # 如果对方有需要的包,不为空[]
        elif nei_Need_codes:
            for key in L_decoded.keys():  # 优先取出对方要且我有的(已解码)发给他
                if key in nei_Need_codes:
                    return (key + "##").encode() + L_decoded[key]
        # 无对方需要的码字信息
        else:
            a = random.sample(L_decoded.keys(), 1)  # 随机一个已解码的码字
            b = a[0]
            data = (b + "##").encode() + L_decoded[b]
            return data

    # 编码度超过 1
    else:
        m_info_list = []  # 记录在找全是对方需要的码字的码字信息过程中已经添加的码字信息, 如果已经添加了就不再添加
        degreeMax = time_queue[n_index]  # 根据度时刻序列以及序号, 得到当前最大度
        codeList = []  # 记录需要被异或编码的码字字节码, 当全部被添加后进行编码
        maxIter = 50  # 最大迭代查找次数 50 次
        _iter = 0  # 记录迭代次数
        only_undecoded = False  # 已解码中是否没有对方需要的, 是否只需要发送未解码中的
        while degreeMax > 0 and _iter < maxIter:
            _iter += 1
            # 随机数为1的话就选择从已解码中选取
            if not only_undecoded and random.randint(1, cfg.fenmu) <= cfg.fenzi:
                has_satisfying_1_degree_cw = False  # 记录是否找到对方没有的一度包

                for key in L_decoded.keys():  # 遍历我的已解码列表, 优先取出对方要且我有的发给他
                    if key in nei_Need_codes and key not in m_info_list:  # 我已解码 & 对方需要 & 不会重复添加
                        m_info_list.append(key)  # 记录我以添加该码字, 避免重复添加
                        if m_info == "":
                            m_info += str(key)
                        else:
                            m_info += "@" + str(key)
                        codeList.append(L_decoded[key])
                        degreeMax -= 1
                        has_satisfying_1_degree_cw = True

                if not has_satisfying_1_degree_cw:  # 如果没找到对方要的就标记只发未解码中的, 因为发送其他的一度包都是对方有的, 没有必要发送
                    only_undecoded = True

            else:  # 从未解码中找
                if len(L_undecoded) != 0:  # 如果有未解码的码字
                    # 先找未解码中全都是对方需要的码字
                    added = False  # 标记是否找到全为对方需要的未解码包
                    for info_set, data_byte in L_undecoded:
                        if info_set - set(nei_Need_codes) == set() and len(info_set) <= degreeMax:  # 此未解码包中尽是对方没有的
                            added = True
                            degreeMax -= len(info_set)
                            for i in info_set:  # 记录info信息
                                if m_info == "":
                                    m_info += str(i)
                                else:
                                    m_info += "@" + str(i)

                            codeList.append(data_byte)  # 添加待编码的码字

                    # 未解码中没有全是对方需要的包的情况
                    if not added:
                        a = random.sample(list(L_undecoded), 1)  # 从中随机选出一个编码包
                        if len(a[0][0]) <= degreeMax:
                            degreeMax = degreeMax - len(a[0][0])
                            codeList.append(a[0][1])
                            for i in a[0][0]:
                                if m_info == "":
                                    m_info += str(i)
                                else:
                                    m_info += "@" + str(i)
                        else:
                            degreeMax -= 1

        if len(codeList) > 0:
            m_code = bytesList_Xor_to_Bytes(codeList)
            # 已经编码后的字节码数据
            data = (m_info + "##").encode() + m_code
            return data
        else:
            return None


def get_forward_encoded_data_1(time_queue, L_decoded, L_undecoded, n_index):
    if len(L_undecoded) > 0:
        m_info = ""
        a = L_undecoded[0]  # 随机一个字典中的key，第二个参数为限制个数
        for i in list(a[0]):
            if m_info == "":
                m_info += str(i)
            else:
                m_info += "@" + str(i)
        data = (m_info + "##").encode() + a[1]
        return data
    elif len(L_decoded) > 0:
        key1 = L_decoded.keys()[0]
        value1 = L_decoded[key1]
        data = (key1 + "##").encode() + value1
        return data
