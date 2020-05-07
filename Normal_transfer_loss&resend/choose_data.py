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
