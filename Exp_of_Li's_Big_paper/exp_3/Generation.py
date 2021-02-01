import numpy as np
import random
import heapq
import Experiment
from jsonFile import *
from config import *
from Standard import Standard
from datetime import datetime

cfg = Config()


class Generation:

    # 染色体解码得到表现形的解
    # encodelength染色体长度
    def getDecode(population, Standard):

        # 得到population中有几个元素
        populationsize = population.shape[0]
        length = len(Standard.EncodeLength)
        decodeVariables = np.zeros((populationsize, length), dtype=np.float)
        # 将染色体拆分添加到解码数组decodeVariables中
        for i, populationchild in enumerate(population):
            # 设置起始点
            start = 0
            # j代表了一个基因
            for j, lengthchild in enumerate(Standard.EncodeLength):

                power = lengthchild - 1
                decimal = 0
                for k in range(start, start + lengthchild):
                    # 二进制转为十进制
                    decimal += populationchild[k] * (2 ** power)
                    power = power - 1
                # 从下一个染色体开始
                start += lengthchild
                lower = Standard.decisionVariables[j][0]
                uper = Standard.decisionVariables[j][1]
                # 转换为表现形
                decodevalue = lower + decimal / (2 ** lengthchild - 1) * (uper - lower)
                # 将解添加到数组中
                decodeVariables[i][j] = decodevalue

        return decodeVariables

    # 得到每个个体的适应度值及累计概率
    # func适应度函数
    # decode解码后得到的表现型
    def getFitnessValue(population, decode, Standard):

        # 得到种群的规模和决策变量的个数
        # popusize,decisionvar分别为decode二维数组的行和列
        popusize, decisionvar = decode.shape

        incomes = []

        # 初始化适应度值空间
        fitnessValue = np.zeros((popusize, 1))
        for popunum in range(popusize):
            parameter_list = [decode[popunum][0], decode[popunum][1],
                              decode[popunum][2], decode[popunum][3],
                              decode[popunum][4]]

            # fitnessValue[popunum][0] = M1.historical_backtest(Standard.train_start_date, Standard.train_end_date, parameter_list)

            # 将指定参数处理成整数
            for index, item in enumerate(parameter_list):
                if index in Standard.intgerIndex:
                    parameter_list[index] = np.ceil(item)

            # 参数列表
            print("参数列表:", parameter_list)


            # 给定一组参数
            min_unit, T_slot, a, b, c = parameter_list

            # 调整所有的5个参数
            # send_num = Experiment.run(int(min_unit), int(T_slot), a, b, c) # 2021.01.27修改前
            send_num = Experiment.run(68, int(T_slot), a, b, c, cfg.record_num, 1, -1)

            # 只调整 后四个参数
            # send_num = Experiment.run(68, int(T_slot), a, b, c)
            print("该次实验源端发送次数：", send_num)

            fitnessValue[popunum][0] = send_num
            incomes.append(fitnessValue[popunum][0])

        # 映射成非负值
        min_income = np.min(fitnessValue)
        for popunum in range(popusize):
            if min_income < 0:
                fitnessValue[popunum][0] -= min_income
            else:
                break

        fitnessValue_convert = []

        # 将二维数组fitnessValue转化为一维数组
        for popunum in range(popusize):
            fitnessValue_convert.append(fitnessValue[popunum][0])

        print("10个染色体对应收益:", incomes)

        # 求fitnessValue列表里前retainEliteNumbers个最大的索引，返回值为列表
        max_fitness_index, min_fitness_index = Generation.getListMaxNumIndex(fitnessValue_convert,
                                                                             Standard.retainEliteNumbers)

        print("最优个体:", max_fitness_index)

        # 保留精英们对应的染色体基因
        elite_population = [population[i] for i in range(len(population)) if (i in max_fitness_index)]

        # 删除population中下标为max_fitness_index的元素
        retain_population = [population[i] for i in range(len(population)) if (i not in max_fitness_index)]

        # 删除fitnessValue中下标为max_fitness_index的元素
        fitnessValue = [fitnessValue[i] for i in range(len(fitnessValue)) if (i not in max_fitness_index)]

        # 保留精英们对应的收益
        elite_incomes = [incomes[i] for i in range(len(incomes)) if (i in max_fitness_index)]

        # 删除incomes中下标为max_fitness_index的元素
        incomes = [incomes[i] for i in range(len(incomes)) if (i not in max_fitness_index)]

        # 如果总适应值为0，则说明所有个体适应值都为0
        if np.sum(fitnessValue) == 0:
            p = 1 / popusize

            # 使probability的和为1
            probability = np.ones((popusize, 1)) * p
        else:
            probability = fitnessValue / np.sum(fitnessValue)
            print(probability)

        for index, item in enumerate(probability):
            probability[index][0] = (1 - item) / 9

        print('------------------------')
        print(probability)

        cum_probability = np.cumsum(probability)

        best_chrome_index, el = Generation.getListMaxNumIndex(fitnessValue_convert, 1)

        return fitnessValue, cum_probability, incomes, retain_population, elite_population, elite_incomes, decode[
            best_chrome_index]

    # 选择新的种群
    def selectNewPopulation(retain_population, population, cum_probability, fitnessValue, incomes, elite_population,
                            elite_incomes, Standard):

        # 获取种群的规模和基因的个数,m=5/10,n=161
        m, n = population.shape

        print("累计概率:", cum_probability)

        cum_len = len(cum_probability)

        # 父代适应度列表
        incomearr = []

        selected_incomes = []

        # print("incomes:",incomes)
        # print("cum_probability:",cum_probability)

        # 初始化新种群
        newPopulation = np.zeros((Standard.maxPopuSize, n))

        new_count = 0
        Hash = np.zeros(10)


        while new_count < Standard.maxPopuSize:
            # 产生一个0到1之间的随机数
            randomnum = np.random.random()

            for j in range(m):
                if Hash[j] >= 2 or j >= cum_len:
                    continue
                # print("选择:",j)
                # print("new_count:",new_count)

                if randomnum >= cum_probability[j]:
                    continue

                newPopulation[new_count] = retain_population[j]  # 染色体基因复制
                incomearr.append(fitnessValue[j])  # 注意evaluation是收益映射成非负值的结果
                selected_incomes.append((incomes[j]))

                new_count += 1
                Hash[j] += 1

                break

        print("赌轮选出的5个染色体对应收益为:", selected_incomes)
        print("赌轮选出的5个染色体对应方差为:", np.std(selected_incomes))
        a, min_index = Generation.getListMaxNumIndex(incomearr, Standard.retainEliteNumbers)

        print("最差个体为:", min_index)

        # 删除newPopulation中最差的若干个个体
        newPopulation = [newPopulation[i] for i in range(len(newPopulation)) if (i not in min_index)]

        # 删除selected_incomes中最差的若干个收益
        selected_incomes = [selected_incomes[i] for i in range(len(selected_incomes)) if (i not in min_index)]

        print("删除最差收益后的selected_incomes:", selected_incomes)

        # 向newPopulation中加入elite_population
        temp = np.zeros((Standard.maxPopuSize, n))

        count = 0
        while (count < Standard.maxPopuSize - Standard.retainEliteNumbers):
            temp[count] = newPopulation[count]
            count += 1

        count2 = 0
        while (count2 < Standard.retainEliteNumbers):
            temp[count] = elite_population[count2]
            count2 += 1
            count += 1

        newPopulation = temp

        # 向selected_incomes中加入elite_incomes
        temp2 = np.zeros(Standard.maxPopuSize)

        count = 0
        while (count < Standard.maxPopuSize - Standard.retainEliteNumbers):
            temp2[count] = selected_incomes[count]
            count += 1

        count2 = 0
        while (count2 < Standard.retainEliteNumbers):
            temp2[count] = elite_incomes[count2]
            count2 += 1
            count += 1

        selected_incomes = temp2
        print("加入精英收益后的selected_incomes:", selected_incomes)

        print("经过精英保留后本代5个父代染色体的方差为:", np.std(selected_incomes))
        Standard.stdarr.append(np.std(selected_incomes))

        return newPopulation, np.average(selected_incomes)

    # 交叉
    def crossNewPopulation(newpopu, prob):

        m, n = newpopu.shape
        # uint8将数值转换为无符号整型
        numbers = np.uint8(m * prob)
        print("交叉染色体个数:", numbers)
        # 如果选择的交叉数量为奇数，则数量加1
        if numbers % 2 != 0:
            numbers = numbers + 1
        # 初始化新的交叉种群
        updatepopulation = np.zeros((m, n), dtype=np.uint8)

        # 随机生成需要交叉的染色体的索引号
        index = random.sample(range(m), numbers)

        # 不需要交叉的染色体直接复制到新的种群中
        for i in range(m):
            if not index.__contains__(i):
                updatepopulation[i] = newpopu[i]
        # 交叉操作
        j = 0
        while j < numbers:
            # 随机生成一个交叉点，np.random.randint()返回的是一个列表
            crosspoint = np.random.randint(0, n, 1)
            crossPoint = crosspoint[0]
            # a = index[j]
            # b = index[j+1]
            updatepopulation[index[j]][0:crossPoint] = newpopu[index[j]][0:crossPoint]
            updatepopulation[index[j]][crossPoint:] = newpopu[index[j + 1]][crossPoint:]
            updatepopulation[index[j + 1]][0:crossPoint] = newpopu[j + 1][0:crossPoint]
            updatepopulation[index[j + 1]][crossPoint:] = newpopu[index[j]][crossPoint:]
            j = j + 2

        return updatepopulation

    # 变异
    def mutation(crosspopulation, mutaprob):

        # 初始化变异种群
        mutationpopu = np.copy(crosspopulation)

        m, n = crosspopulation.shape
        # 计算需要变异的基因数量
        mutationnums = np.uint8(m * n * mutaprob)

        print("变异基因个数:", mutationnums / 5)

        # 随机生成变异基因的位置
        mutationindex = random.sample(range(m * n), mutationnums)

        # 变异操作
        for geneindex in mutationindex:
            # np.floor()向下取整返回的是float型
            row = np.uint8(np.floor(geneindex / n))

            colume = geneindex % n
            if mutationpopu[row][colume] == 0:
                mutationpopu[row][colume] = 1
            else:
                mutationpopu[row][colume] = 0
        return mutationpopu

    def getListMaxMinIndex(num_list, topk):
        '''
        获取列表中最大的前n个数值的位置索引
        '''
        max_num_index = map(num_list.index, heapq.nlargest(topk, num_list))
        min_num_index = map(num_list.index, heapq.nsmallest(topk, num_list))

        return list(max_num_index), list(min_num_index)

    def getListMaxNumIndex(num_list, topk):

        min_num = -999999999999999999999
        max_num = 999999999999999999999

        max_index = []
        min_index = []
        num_list_copy = num_list.copy()
        for i in range(topk):
            max_one_index, min_one_index = Generation.getListMaxMinIndex(num_list_copy, 1)
            num_list_copy[max_one_index[0]] = min_num
            max_index.append(max_one_index[0])

        num_list_copy = num_list.copy()

        for i in range(topk):
            max_one_index, min_one_index = Generation.getListMaxMinIndex(num_list_copy, 1)
            num_list_copy[min_one_index[0]] = max_num
            min_index.append(min_one_index[0])

        # 求最大值
        # return max_index, min_index

        # 求最小值
        return min_index, max_index
