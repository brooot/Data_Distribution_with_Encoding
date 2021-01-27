from scipy.optimize import fsolve
import numpy as np
from config import *
cfg = Config()


class Standard:
    # 参数上下界
    # decisionVariables = [[68, 69], [1,2], [0, 0.01], [-1, 1], [-1, 1]]
    # print("====================================", record_num*68//len(Dest_ADDR))
    decisionVariables = [[10000, min(cfg.record_num*68, 70000)], [1, 3], [0.1, 1], [0.1, 0.5], [0.001, 0.01]]

    # 精度
    delta = 0.0001

    # 最大进化代数(一个极大值)
    maxgeneration = 100000

    # 初始种群数量
    initialPopuSize = 10

    # 初始交叉率
    prob = 0.8

    # 初始变异率
    mutationprob = 0.02

    # 每次生成的子代染色体个数
    maxPopuSize = 10

    # 是否要加精英
    ifRetainElitist = False

    # 要保留的精英个数
    retainEliteNumbers = 0

    # 最大精英个数
    maxEliteNumbers = 15

    # 最低变异率
    minMutation = 0.001

    # 每代方差列表
    stdarr = []

    # 求染色体长度
    @staticmethod
    def getEncodeLength(decisionVariables, delta):

        # 将每个变量的编码长度放入数组
        lengths = []
        idx = 0
        for decisionvar in decisionVariables:
            uper = decisionvar[1]
            low = decisionvar[0]
            # res()返回一个数组
            if idx == 1 or idx == 0:
                res = fsolve(lambda x: ((uper - low) - 2 ** x + 1), 30)
                # ceil()向上取整
                length = int(np.ceil(res[0]))
                lengths.append(length)
            else:
                res = fsolve(lambda x: ((uper - low) / delta - 2 ** x + 1), 30)
                # ceil()向上取整
                length = int(np.ceil(res[0]))
                lengths.append(length)
            idx += 1
        return lengths

    # 随机生成初始化种群
    @staticmethod
    def getinitialPopulation(length, initialPopuSize):

        chromsomes = np.zeros((initialPopuSize, length), dtype=np.int)

        for popusize in range(initialPopuSize):

            len0 = Standard.EncodeLength[0]
            len1 = Standard.EncodeLength[1]
            len2 = Standard.EncodeLength[2]
            len3 = Standard.EncodeLength[3]
            len4 = Standard.EncodeLength[4]

            # np.random.randit()产生[0,2)之间的随机整数，第三个参数表示随机数的数量
            print("len0: ", len0)
            chromsomes[popusize, :len0] = np.random.randint(0, 2, len0)

            chromsomes[popusize, len0:len0 + len1] = np.random.randint(0, 2, len1)

            binArr_a = np.random.randint(0, 2, len2)

            binArr_b = np.random.randint(0, 2, len3)

            binArr_c = np.random.randint(0, 2, len4)

            chromsomes[popusize, len0 + len1:len0 + len1 + len2] = binArr_a

            chromsomes[popusize, len0 + len1 + len2:len0 + len1 + len2 + len3] = binArr_b

            chromsomes[popusize, len0 + len1 + len2 + len3:len0 + len1 + len2 + len3 + len4] = binArr_c

        return chromsomes

    # 由二进制得到十进制
    @staticmethod
    def getDecimal(binArr, index):

        decimal = 0
        length = len(binArr)
        power = length - 1

        for k in range(0, length):
            # 二进制转为十进制
            decimal += binArr[k] * (2 ** power)
            power = power - 1

        lower = Standard.decisionVariables[index][0]
        uper = Standard.decisionVariables[index][1]

        return lower + decimal * (uper - lower) / (2 ** length - 1)


    @staticmethod
    def init_data():

        # 要求为整数的参数索引集合
        Standard.intgerIndex = [0, 1]

        # 获得染色体长度(是一个数组)
        Standard.EncodeLength = Standard.getEncodeLength(Standard.decisionVariables, Standard.delta)

        # 获得初始化种群
        Standard.initialPopulation = Standard.getinitialPopulation(sum(Standard.EncodeLength), Standard.initialPopuSize)

        # 精度
        Standard.delta = 0.0001

        # 最大进化代数(一个极大值)
        Standard.maxgeneration = 100000

        # 初始种群数量
        Standard.initialPopuSize = 5

        # 初始交叉率
        Standard.prob = 0.9

        # 初始变异率
        Standard.mutationprob = 0.08

        # 每次生成的子代染色体个数
        Standard.maxPopuSize = 5

        # 要保留的精英个数
        Standard.retainEliteNumbers = 0

        # 最大精英个数
        Standard.maxEliteNumbers = 5

        # 最低变异率
        Standard.minMutation = 0.003

        # 每代方差列表
        Standard.stdarr = []

        Standard.retainEliteNumbers = 0
