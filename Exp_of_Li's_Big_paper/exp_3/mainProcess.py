from datetime import datetime
import numpy as np
import random
from scipy.optimize import fsolve
# import matplotlib.pyplot as plt
import heapq
from Standard import Standard
from Generation import Generation


class Process(object):

    def main():

        average_incomes = []

        populations = []

        # 用于判断全局收敛的方差最小值,小于该值时认为种群达到全局收敛
        std_limition = 0.1

        currentAdjustGeneration = 41

        Standard.init_data()
        population = Standard.initialPopulation

        generation = 0

        time3 = datetime.now()

        # 十万代以内，不停迭代，直到某一代出现完全收敛
        while generation < Standard.maxgeneration:

            populations.append(population)

            print("第")
            print(generation)
            print("代")

            if (generation == 40):
                Standard.retainEliteNumbers = 1

            print("本代精英个数:", Standard.retainEliteNumbers)
            print("本代变异率:", Standard.mutationprob)

            # 每相隔30代 加一次精英
            if (generation - currentAdjustGeneration > 30 and Standard.retainEliteNumbers < 5):
                print("下面加精英")
                Standard.retainEliteNumbers += 1
                currentAdjustGeneration = generation

            # 对种群解码得到表现形
            decode = Generation.getDecode(population, Standard)

            # 得到适应度值和累计概率值
            fitnessValue, cum_proba, incomes, retain_population, elite_population, elite_incomes, generation_best_chrome = Generation.getFitnessValue(
                population, decode, Standard)

            # 选择新的种群,并计算平均收益
            newpopulations, average_income = Generation.selectNewPopulation(retain_population, population, cum_proba,
                                                                            fitnessValue,
                                                                            incomes, elite_population, elite_incomes,
                                                                            Standard)

            print("本代平均收益:", average_income)
            average_incomes.append(average_income)

            # 如果本代方差小于一定值，则认为达到了全局收敛，迭代终止
            if (Standard.stdarr[generation] < std_limition):
                break

            # 新种群交叉
            crossPopulations = Generation.crossNewPopulation(newpopulations, Standard.prob)

            # 变异操作
            mutationpopulation = Generation.mutation(crossPopulations, Standard.mutationprob)


            # 将父母和子女合并为新的种群
            population = np.vstack((newpopulations, mutationpopulation))

            generation += 1

            print("本代演化结束,当前平均收益数组:", average_incomes)

            time4 = datetime.now()
            print("本代耗时:", time4 - time3)

            time3 = time4

        # 获取最后要输出的平均收益和各项参数
        final_average_income = average_income
        best_chrome = generation_best_chrome
        """
        print(average_incomes)
        x = [i for i in range(generation)]
        y = [average_incomes[i] for i in range(generation)]
        plt.plot(x, y)
        plt.show()
        """
        # 返回最终平均收益,以及最后一代的最优染色体

        best_chrome_dealed = best_chrome[0]

        for index, item in enumerate(best_chrome_dealed):
            if (index in Standard.intgerIndex):
                best_chrome_dealed[index] = np.ceil(item)

        return final_average_income, best_chrome_dealed, generation
