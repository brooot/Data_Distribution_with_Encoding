import os,sys
BASE_DIR = os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) )
sys.path.append(BASE_DIR)
from mainProcess import Process
import datetime
# from .modules.GA.Standard import Standard
import pandas as pd
import numpy as np

def main():

    # 收益
    resultincome = []

    # 8个权重
    parameter0 = []
    parameter1 = []
    parameter2 = []
    parameter3 = []
    parameter4 = []
    parameter5 = []
    parameter6 = []
    parameter7 = []

    # 时间间隔
    timespace = []

    # 迭代次数
    generations=[]

    start_time=datetime.datetime.now()
    for num in range(0,1):
        start_time2=datetime.datetime.now()
        final_average_income,best_chrome,res_generation=Process.main()

        generations.append(res_generation)

        print(num)
        print(final_average_income)

        resultincome.append(final_average_income)

        # 因为best_chrome是一个二维数组，不能直接存入excel，所以这里先转化为1维数组
        # best_chrome=best_chrome[0]
        #
        # for index,item in enumerate(best_chrome):
        #     if(index in Standard.intgerIndex):
        #         best_chrome[index]=np.ceil(item)

        for index in range(0, len(best_chrome)):
            print(best_chrome[index])

            if(index==0):
                parameter0.append(best_chrome[index])
            if (index == 1):
                parameter1.append(best_chrome[index])
            if (index == 2):
                parameter2.append(best_chrome[index])
            if (index == 3):
                parameter3.append(best_chrome[index])
            if (index == 4):
                parameter4.append(best_chrome[index])
            if (index == 5):
                parameter5.append(best_chrome[index])
            if (index == 6):
                parameter6.append(best_chrome[index])
            if (index == 7):
                parameter7.append(best_chrome[index])
            if(index==8):
                timespace.append(best_chrome[index])

        end_time2 = datetime.datetime.now()
        print("本次遗传算法执行完毕,共计耗时:", end_time2 - start_time2)

    data={'resultincome':resultincome,'parameter0':parameter0,'parameter1':parameter1,
          'parameter2':parameter2,'parameter3':parameter3,'parameter4':parameter4,'generations':generations
          }

    # df为表格对象
    df = pd.DataFrame(data)
    print(df)

    # 把df存入excel,注意不要事先在桌面上新建testdata.xlsx
    df.to_excel('./all.xls')
    end_time=datetime.datetime.now()
    # print("共计耗时:",end_time-start_time)

if __name__ == "__main__":
    main()
