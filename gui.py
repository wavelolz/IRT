import pyqtgraph as pg
import numpy as np
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QFileDialog
import os
import sys
from scipy.stats import norm
import pandas as pd

class disform(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(disform, self).__init__(*args, **kwargs)
        uic.loadUi("dis.ui", self)

        # 準備資料 --------------------------------
        file_dir = 'D:\\Dropbox\\wave\\projects\\IRT\\discriminate\\' # 資料檔所在目錄
        file_name = 'exchange(20).xlsx'
        out_file_name = 'item_disc_index.txt'
        pd_data = pd.read_excel(file_dir+file_name, header=None)
        raw_data = np.array(pd_data)
        total_question = len(raw_data[0][1:])
        #-----------------------------------------

        self.quesid.currentIndexChanged.connect(lambda: self._calculate_discriminate(file_name, int(self.quesid.currentText()) - 1, raw_data))
        self._compo_method(total_question)



    def _compo_method(self, total_question):
        for i in range(total_question):
            self.quesid.addItem(str(i + 1))


    def _calculate_discriminate(self, file_name, ques_id, raw_data):
        
        test_answer = raw_data[0, 1:]# 本次考試正確答案（第一列）
        original_diff = raw_data[2, 1:] # 試題原始難度（第三列）
        answered_data = raw_data[3:, 1:] # 本次考試考生答案
        J, I = answered_data.shape # 本次考生人數，題目數
        # 開始計算 -----------------------------------
        Tmp = np.tile(test_answer, (J, 1))
        corrected_data = np.multiply((Tmp == answered_data), 1) #對答案（convert logic to numeric)
        correctly_answered = corrected_data.mean(axis = 1) # 答對率
        rank_index = np.argsort(correctly_answered) # low to high

        # 計算選項率（所有考生選擇答案 1,2,3,4或其他的比例）：分三組:全體、高分群、低分群
        cut = np.floor(J / 100 * 27).astype('int') # 高分群=前27%, 低分群=後27%
        low_idx = rank_index[0:cut] # 低分群=後27%
        high_idx = rank_index[-cut:] # 高分群=前27%

        choices = 5 # multiple choices: 1,2,3,4,other
        cnt_1234_all = np.zeros((I, choices)) # 全體各題選項率
        cnt_1234_high = np.zeros((I, choices)) # 高分群各題選項率
        cnt_1234_low = np.zeros((I, choices)) # 低分群各題選項率
        for i in range(choices):
            cnt_1234_all[:, i]= np.count_nonzero(answered_data == i+1, axis = 0) / J
            cnt_1234_high[:, i]= np.count_nonzero(answered_data[high_idx] == i+1, axis = 0) / cut
            cnt_1234_low[:, i]= np.count_nonzero(answered_data[low_idx] == i+1, axis = 0) / cut

        # 通過率：答對的比率
        pass_rate = np.zeros(I)
        # 難度：答對之(高分組選項率+低分組選項率)/2
        diff = np.zeros(I)
        # 鑑別度：答對之（高分組選項率-低分組選項率）
        disc = np.zeros(I)
        final_report = np.zeros((I * 4, 6))
        for i in range(I):
            idx = test_answer[i]-1
            pass_rate[i] = cnt_1234_all[i, idx]
            diff[i] = (cnt_1234_high[i, idx] + cnt_1234_low[i, idx]) / 2
            disc[i] = cnt_1234_high[i, idx] - cnt_1234_low[i, idx]
            final_report[i*4, :] =  np.r_[np.arange(1,6), original_diff[i]]
            final_report[i*4+1, :] = np.r_[cnt_1234_all[i,:], pass_rate[i]]
            final_report[i*4+2, :] = np.r_[cnt_1234_high[i,:], diff[i]]
            final_report[i*4+3, :] = np.r_[cnt_1234_low[i,:], disc[i]]

        # 輸出到 txt 檔案
        # file_handle = open(out_file_name,"w")
        Data_out ='' # collect output contents
        # with open(r'item_disc_index.txt','w') as outfile:
        Data_out = Data_out + '科目：{}, 試題之難度,鑑別度等指標.本測驗共有 {} 題, {} 受試者\n\n'.format(file_name, I, J)
        Data_out = Data_out + '註一：原始難度是指出題者或審題者研判試題之難易度, 1 代表容易, 2 代表適中, 3 代表較難\n\n'
        Data_out = Data_out + '註二：試題選項有星號者(*)為正確選項\n\n'
        Data_out = Data_out + '-----------------------------------------------------------------\n\n'
        
        i1 = '1*' if test_answer[ques_id]==1 else '1' # 加 * 代表是該題的答案
        i2 = '2*' if test_answer[ques_id]==2 else '2'
        i3 = '3*' if test_answer[ques_id]==3 else '3'
        i4 = '4*' if test_answer[ques_id]==4 else '4'
        Data_out = Data_out + '試題：{}  (題庫中之原始題號:{}) \n'.format(ques_id+1, raw_data[1, ques_id+1])
        Data_out = Data_out + '選  項      {:8s}{:8s}{:8s}{:7s}{:s}      原始難度:{:4.0f}\n'.format(i1,i2,i3,i4, '其他', original_diff[ques_id])
        Data_out = Data_out + '選項率 {:8.3f}{:8.3f}{:8.3f}{:8.3f}{:8.3f}      通過率:{:.3f}\n'.format(cnt_1234_all[ques_id,0],cnt_1234_all[ques_id,1],cnt_1234_all[ques_id,2],cnt_1234_all[ques_id,3],cnt_1234_all[ques_id,4],pass_rate[ques_id])
        Data_out = Data_out + '高分組 {:8.3f}{:8.3f}{:8.3f}{:8.3f}{:8.3f}      難  度:{:.3f}\n'.format(cnt_1234_high[ques_id,0],cnt_1234_high[ques_id,1],cnt_1234_high[ques_id,2],cnt_1234_high[ques_id,3],cnt_1234_high[ques_id,4],diff[ques_id])
        Data_out = Data_out + '低分組 {:8.3f}{:8.3f}{:8.3f}{:8.3f}{:8.3f}      鑑別度:{:.3f}\n'.format(cnt_1234_low[ques_id,0],cnt_1234_low[ques_id,1],cnt_1234_low[ques_id,2],cnt_1234_low[ques_id,3],cnt_1234_low[ques_id,4],disc[ques_id])
        Data_out = Data_out + '-----------------------------------------------------------------\n\n'

        self.result.setPlainText(Data_out)
            



class mainform(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(mainform, self).__init__(*args, **kwargs)
        uic.loadUi("demo.ui", self)

        self.disform = disform()
        self._compo_method()
        self._show_title()

        self.graph.setXRange(0, 105, padding = 0)
        self.graph.setYRange(0, 115, padding = 0)
        self.graph.setMouseEnabled(x = False)
        self.graph.setMouseEnabled(y = False)
        self.graph.setBackground("#2B3B84")
    

        # signal
        self.test.currentIndexChanged.connect(self._show_title)
        self.correct.valueChanged.connect(self._show_correct)
        self.exit.clicked.connect(self._exit)
        self.common.clicked.connect(self._open_common)
        self.original.clicked.connect(self._open_original)
        self.answer.clicked.connect(self._open_answer)
        self.correct.valueChanged.connect(self._update_plot)
        self.dis.clicked.connect(self._show_dis)

    def _compo_method(self):
        self.test.addItem("金融基測")
        self.test.addItem("外匯交易")
        self.test.addItem("AFP / CFP")
        
    def _show_title(self):
        tle = f"<p style = 'font-size: 20px; color: white'>目前正在執行 {self.test.currentText()} 的等化模擬 </p>"
        self.title.setText(tle)

    def _show_correct(self):
        value = self.correct.value()
        lbl = f"<p style = 'font-size: 15pt; color: #FFCA6C'>答對題數: {value}</p>"
        self.cor_label.setText(lbl)

    def _update_plot(self):
        self.graph.clear()
        n = 110
        x = np.linspace(0, 100, 1000)
        y1 = norm.cdf(x, loc = 50, scale = 15) * n
        y2 = norm.cdf(x, loc = 45, scale = 13) * n
        former = int(self.correct.value())
        ability = norm.ppf(former/n, loc = 50, scale = 15)
        corr = norm.cdf(ability , loc = 45, scale = 13) * n
        vx = [ability] * 2
        vy = [0, corr]
        h1x = h2x = [0, ability]
        h1y = [corr] * 2
        h2y = [former] * 2

        penori = pg.mkPen(color = "#3DFCFF", width = 4.5)
        pennow = pg.mkPen(color = "#FFC327", width = 4.5)
        self.graph.addLegend()

        
        self.graph.plot(x, y1, pen = penori, name = "<p style = 'font-size: 14pt; color: #B5FFA3; font-weight: bold'>前屆</p>")
        self.graph.plot(x, y2, pen = pennow, name = "<p style = 'font-size: 14pt; color: #B5FFA3; font-weight: bold'>本屆</p>")
        self.graph.plot(vx, vy)
        self.graph.plot(h1x, h1y)
        self.graph.plot(h2x, h2y)

        font = QtGui.QFont()
        font.setPixelSize(20)
        font.setWeight(100)

        xtick_num = [0, 20, 40, 60, 80, 100, round(ability, 2)]
        xtick_label = [str(i) for i in xtick_num]
        xaxis = self.graph.getAxis("bottom")
        xaxis.setTicks([list(zip(xtick_num, xtick_label))])
        xaxis.setTickFont(font)
        xaxis.setTextPen("w")

        ytick_num = [0, 20, 40, 60, 80, 100, round(corr, 1), former]
        ytick_label = [str(i) for i in ytick_num]
        yaxis = self.graph.getAxis("left")
        yaxis.setTicks([list(zip(ytick_num, ytick_label))])
        yaxis.setTickFont(font)
        yaxis.setTextPen("w")

        # change text

        self.now.setText(f"<p style = 'font-size: 15pt; color: #FFCA6C'>前屆答對題數: {former} 題, 對應到本屆答對題數為: {round(corr, 1)} 題</p>")

    def _open_original(self):
        file_name = QFileDialog.getOpenFileName(self, "選取作答檔", "D:\Dropbox\wave\projects\IRT", "All Files (*)")
        print(file_name)

    def _open_answer(self):
        file_name = QFileDialog.getOpenFileName(self, "選取答案檔", "D:\Dropbox\wave\projects\IRT", "All Files (*)")
        print(file_name)

    def _open_common(self):
        file_name = QFileDialog.getOpenFileName(self, "選取共同題", "D:\Dropbox\wave\projects\IRT", "All Files (*)")
        print(file_name)

    def _show_dis(self):
        self.disform.show()

    def _exit(self):
        self.close()



if __name__ == "__main__":
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QtWidgets.QApplication(sys.argv)
    ui = mainform()
    ui.show()
    sys.exit(app.exec())
