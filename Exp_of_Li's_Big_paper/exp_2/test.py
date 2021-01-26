import json
# with open("data.txt", "rb") as f:
#     # all_bytes = b""
#     for i in range(10):  # 一代 k 片数据, 每一片表示一条68字符的完整的记录
#         line = f.readline()
#         print(line)
#         print(len(line))

# with open('data_69.txt', 'r') as infile, open('data.txt', 'w', newline='\n') as outfile:
#     outfile.writelines(infile.readlines())
# from multiprocessing import *
# L = Manager().dict()


Map = {'1': 'a', '2': 'b'}
li = {'aList':[1,2,3,4], 'aMap': Map}

kk = json.dumps(li)

s = bytes(kk, encoding='utf-8')

p = s.decode()

msg_data = json.loads(p)

print(type(msg_data))
print(msg_data['aList'])
