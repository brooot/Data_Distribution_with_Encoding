import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize
from os import listdir


# 二次曲线方程
def f_2(x, a, b, c):
    return a * x * x + b * x + c


# 三次曲线方程
def f_3(x, a, b, c, d):
    return a * x * x * x + b * x * x + c * x + d


# 四次曲线方程
def f_4(x, A, B, C, D, E):
    return A * x * x * x * x + B * x * x * x + C * x * x + D * x + E


def getFitFunc(x0, y0, max_x, need_plot):
    # 四次曲线拟合与绘制
    A4, B4, C4, D4, E4 = optimize.curve_fit(f_4, x0, y0)[0]
    # A4, B4, C4, D4 = optimize.curve_fit(f_3, x0, y0)[0]
    # A4, B4, C4 = optimize.curve_fit(f_2, x0, y0)[0]
    if need_plot:
        # 打印拟合图像
        # print("参数是: ", A4, B4, C4, D4, E4)
        x4 = np.arange(0, max_x, 0.01)
        y4 = A4 * x4 * x4 * x4 * x4 + B4 * x4 * x4 * x4 + C4 * x4 * x4 + D4 * x4 + E4
        plt.figure()
        # plt.scatter(x0[:], y0[:], 25, "red")
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
    with open(filename, 'r', encoding='ISO-8859-1') as datacsv:
        csvreader = csv.reader(datacsv)
        next(csvreader)
        for line in csvreader:
            x.append(int(line[0]))
            y.append(int(line[1]))
    return [x, y, x[-1], y[-1]]


def main():
    mean_value = [0]
    node_Num = 0
    piece_num = 0
    csv_dir = "./csv_files"
    for filename in listdir(csv_dir):
        node_Num += 1
        X, Y, max_X, max_Y = read_csv(csv_dir + '/' + filename)
        if node_Num == 1:
            piece_num = max_Y
        elif max_Y != piece_num:
            raise Exception("piece_num 不相同, 请检查文件实验参数是否相同! ")
        fit_func = getFitFunc(X, Y, max_X, False)  # 得到拟合函数
        if node_Num == 1:
            for i in range(1, max_X + 1):
                mean_value.append(fit_func(i))
        else:
            if max_X + 1 >= len(mean_value):
                while max_X + 1 > len(mean_value):
                    mean_value.append(piece_num * (node_Num - 1))
                for i in range(1, len(mean_value)):
                    mean_value[i] += fit_func(i)
            else:
                for i in range(1, max_X + 1):
                    mean_value[i] += fit_func(i)
                for i in range(max_X + 2, len(mean_value)):
                    mean_value[i] += piece_num

    for i in range(1, len(mean_value)):
        mean_value[i] /= node_Num
        if mean_value[i] < mean_value[i - 1]:
            mean_value[i] = mean_value[i - 1]

    with open("mean_decoding_log_of_" + str(node_Num) + ".csv", "w", encoding='utf-8') as datacsv:
        csvwriter = csv.writer(datacsv)
        csvwriter.writerow(["源的发送序号", "平均已解码个数"])
        for i in range(len(mean_value)):
            csvwriter.writerow([i, mean_value[i]])

    final_fit_func = getFitFunc(range(len(mean_value)), mean_value, len(mean_value), True)  # 得到最终的拟合函数


if __name__ == "__main__":
    main()
