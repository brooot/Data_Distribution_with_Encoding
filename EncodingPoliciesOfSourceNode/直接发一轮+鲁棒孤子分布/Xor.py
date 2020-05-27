#!/usr/bin/env python3
#encoding=utf-8
# 相同长度的字节码异或编码,返回异或编码后的字节码
def bytes_Xor_to_bytes(b1, b2):
    if(len(b1) != len(b2)):
        raise 
    L = []
    for i, j in zip(b1, b2):
        L.append(i ^ j)
    return bytes(L)


# 参数是一个字节码列表[bytes, bytes]
def bytesList_Xor_to_Bytes(Ls):
    ans = Ls[0]
    for i in range(1, len(Ls)):
        t = Ls[i]
        ans = bytes_Xor_to_bytes(ans, t)
    return ans