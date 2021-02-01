import Experiment
from config import *
cfg = Config()
def main():
    min_unit, T_slot, a, b, c = 68, 1, 0.88652179221, 0.25726495726, 0.0073070866
    
    exp_times = 1  # 实验次数
    
    pieces_each_round = cfg.record_num
    
    sendNum = Experiment.run(min_unit, T_slot, a, b, c, pieces_each_round, 1, -1)
    
    print("totalTime: ", sendNum)
    
    
if __name__ == '__main__':
    main()