import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize
from os import listdir


# 四次曲线方程
def f_4(x, A, B, C, D, E):
    return A * x * x * x * x + B * x * x * x + C * x * x + D * x + E


def getFitFunc(x0, y0, max_x, need_plot):
    # 四次曲线拟合与绘制
    A4, B4, C4, D4, E4 = optimize.curve_fit(f_4, x0, y0)[0]
    if need_plot:
        # 打印拟合图像
        # print("参数是: ", A4, B4, C4, D4, E4)
        x4 = np.arange(0, max_x, 0.01)
        y4 = A4 * x4 * x4 * x4 * x4 + B4 * x4 * x4 * x4 + C4 * x4 * x4 + D4 * x4 + E4
        plt.figure()
        plt.scatter(x0[:], y0[:], 25, "red")
        plt.plot(x4, y4, "green")
        plt.title("mean decoding curve")
        plt.xlabel("source send number")
        plt.ylabel('mean decoded num')
        plt.show()

    def f(x):
        return A4 * x * x * x * x + B4 * x * x * x + C4 * x * x + D4 * x + E4
    return f


# 读取csv文件中的数据, 返回 x 和 y 的点数组对
def read_csv(filename):
    x = [0]
    y = [0]
    with open(filename, 'r', encoding='utf-8') as datacsv:
        csvreader = csv.reader(datacsv)
        next(csvreader)
        for line in csvreader:
            x.append(int(line[0]))
            y.append(int(line[1]))
    return [x, y, x[-1]]


def main():
    mean_value =[0]
    min_Max = -1
    node_Num = 0
    csv_dir = "./csv_files"
    for filename in listdir(csv_dir):
        node_Num += 1
        X, Y, max_X = read_csv(csv_dir + '/' + filename)
        fit_func = getFitFunc(X, Y, max_X, False)  # 得到拟合函数
        if min_Max == -1:
            min_Max = max_X
            for i in range(1, min_Max + 1):
                mean_value.append(fit_func(i))
        else:
            min_Max = min(min_Max, max_X)
            for i in range(1, min_Max + 1):
                mean_value[i] += fit_func(i)

    for i in range(1, min_Max +1):
        mean_value[i] /= node_Num
    mean_value = mean_value[:min_Max+1]
    final_fit_func = getFitFunc(range(min_Max+1), mean_value, min_Max, True)  # 得到拟合函数



if __name__ == "__main__":
    main()
