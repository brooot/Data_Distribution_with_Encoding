#encoding=UTF-8
from Xor import *
from config import *
import operator
smallest_piece = 4 # 最小编码单元大小
# len = 67 (不带'\n')

# def get_bytesList_of_a_generation(k): # k 表示读取的数据的条数
# 	bytes_list = []  # 一代数据列表 ['一条记录','一条记录',..., '一条记录'] 一代共 40 条
# 	with open("data.txt", "rb") as f:
# 		cur_piece = b"" 
# 		read_piece = b""
# 		for i in range(k):  # 一代 k 片数据, 每一片表示一条68字符的完整的记录
# 			# 将新读取的数据拼接到缓存中
# 			read_piece += f.readline()[:-1] # 获取一行数据的字节码
# 			# print(read_piece)
# 			while len(read_piece) - smallest_piece > 0:
# 				fill_num = smallest_piece - len(cur_piece) # 获取还需要多少位才能将最小编码单元填满
# 				if fill_num <= smallest_piece: # 如果剩余的部分小于等于每一段的大小, 则只需要再添加这最后一次就可以了
# 					fill_piece = read_piece[:fill_num] # 获取能填满当前分段的内容
# 					read_piece = read_piece[fill_num:] # 获取剩余的片段
# 					bytes_list.append(cur_piece + fill_piece) # 添加到字节码列表中
# 					cur_piece = b"" # 将当前的段标记为空
# 				else: # 当前这次添加仍然不能将该段填满
# 					cur_piece += read_piece # 全部加到当前段中
# 					print("-----")
# 					# while cur_piece
# 				if i == k-1 and read_piece:
# 					read_piece += "*".encode()*(smallest_piece-len(read_piece))
# 					bytes_list.append(read_piece)
# 	print(read_piece)
# 	return bytes_list  # 返回记录的字节码列表


def get_bytesList_of_a_generation(k): # k 表示读取的数据的条数
	bytes_list = []  # 一代数据列表 ['一条记录','一条记录',..., '一条记录'] 一代共 40 条
	with open("data.txt", "rb") as f:
		all_bytes = b""
		for i in range(k):  # 一代 k 片数据, 每一片表示一条68字符的完整的记录
			all_bytes += f.readline()
		full_num = 67*k //smallest_piece
		left = 67*k % smallest_piece
		for i in range(full_num):
			bytes_list.append(all_bytes[:smallest_piece])
			all_bytes = all_bytes[smallest_piece:]
		if left:
			bytes_list.append(all_bytes + "=".encode()*left)
	return bytes_list  # 返回记录的字节码列表



byte_L = get_bytesList_of_a_generation(2)

print(byte_L)


# print(sum(map(lambda x:len(x), bytes_list)))