# @package SoundEffectorModel.py
# @brief SoundEffectorのModel
# @author Nakashima
# @date 2018/9/9
# @version 0.0.1
# @

# @cond
# -*- coding:utf-8 -*-
# @endcond
import sys
import numpy as np
from scipy import signal
import pyaudio
import wave
from time import sleep

## Model
# @brief 信号処理用クラス
class SoundEffectorModel:
    ## コンストラクタ
    # @brief メンバ変数宣言、音声入出力用インスタンス生成を行います
    def __init__(self):
        """ 信号処理用定数 """
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.CHUNK = 1024
        self.MONORALRIGHT = True
        self.BUFFERSIZE = 2*self.CHUNK
        self.ANALYZEDSIZE = 8*self.CHUNK
        self.MAXLEVEL = 32768.0
        self.HANNINGWINDOW = np.hanning(self.ANALYZEDSIZE)
        self.HAMMINGWINDOW = np.hamming(self.ANALYZEDSIZE)

        """ 信号用配列 """
        self.bufferdata = np.zeros(self.BUFFERSIZE)
        self.analyzeddata = np.empty(self.ANALYZEDSIZE)
        self.plotdata = np.empty(self.CHUNK)
        self.spectrum = np.empty(self.ANALYZEDSIZE)
        self.power = np.empty(self.ANALYZEDSIZE)
        self.cepstrum = np.empty(self.ANALYZEDSIZE)
        self.phase = np.empty(self.BUFFERSIZE)

        """ 信号処理用変数 """
        self.amp_pre_booster = 6
        self.amp_post_booster = 4
        self.threshold_distortion = 0.2*self.MAXLEVEL
        self.shift_phaser = 0.5
        self.whole_counter = 0

        """ エフェクト有効化フラグ """
        self.pre_booster_on = 1
        self.distortion_on = 0
        self.post_booster_on = 0
        self.phaser_on = 0

        """ 音声入出力用インスタンス """
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format = self.FORMAT,
            		              channels = self.CHANNELS,
            		              rate = self.RATE,
                                  input = True,
            		              output = True)

    ## デストラクタ
    # @brief インスタンス削除関数を呼び出します
    def __del__(self):
        self.delete()

    ## インスタンス削除関数
    # @brief 音声入出力用インスタンスを削除します
    def delete(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    """ -----------------------------------------------------------------------
        Pre Process
    ----------------------------------------------------------------------- """
    """ 取得データの変換(文字列→INT16) """
    ## 取得データの変換(文字列→INT16)
    # @param data_str pyaudioの入力音信号(str型)
    # @return data_int16 pyaudioの入力音信号(int16型)
    def toInt16(self, data_str):
        data_int16 = np.frombuffer(data_str, "int16")
        return data_int16

    """ 取得データの変換(文字列→FLOAT(-1.0～1.0)) """
    ## 取得データの変換(文字列→FLOAT(-1.0～1.0))
    # @param data_str pyaudioの入力音信号(str型)
    # @return data_float pyaudioの入力音信号(-1～1に正規化されたfloat型)
    def toNormalizedFloat(self, data_str):
        data_float = np.frombuffer(data_str, "float")/self.MAXLEVEL
        return data_float

    """ ステレオ(左側)→モノラル """
    ## ステレオ(左側)→モノラル
    # @param input pyaudioの入力音信号(ステレオ)
    # @return output pyaudioの入力音信号(ステレオ入力の左側)
    def toMonoralLeft(self, input):
        output = input[::2]
        return output

    """ ステレオ(右側)→モノラル """
    ## ステレオ(右側)→モノラル
    # @param input pyaudioの入力音信号(ステレオ)
    # @return output pyaudioの入力音信号(ステレオ入力の右側)
    def toMonoralRight(self, input):
        output = input[1::2]
        return output

    """ -----------------------------------------------------------------------
        Post Process
    ----------------------------------------------------------------------- """
    """ モノラル→ステレオ """
    ## モノラル→ステレオ
    # @param input pyaudioの出力音信号(モノラル)
    # @return output pyaudioの出力音信号(ステレオ)
    def toStereo(self, input):
        output = np.concatenate(np.array([input,input]).T)
        return output

    """ 処理済データの変換(INT16→文字列) """
    ## 処理済データの変換(INT16→文字列)
    # @param data_int16 pyaudioの出力音信号(int16型)
    # @return data_str pyaudioの出力音信号(str型)
    def toStr(self, data_int16):
        data_str = np.frombuffer(np.array(data_int16), "S1")
        return data_str

    """ 処理済データの変換(float(-1.0～1.0)→文字列) """
    ## 処理済データの変換(float(-1.0～1.0)→文字列)
    # @param data_int16 pyaudioの出力音信号(float型)
    # @return data_str pyaudioの出力音信号(str型)
    def toDenormalizedStr(self, data_float):
        data_str = np.frombuffer(np.array(data_float)*32768.0, "S1")
        return data_str

    """ -----------------------------------------------------------------------
        Sound Effect
    ----------------------------------------------------------------------- """
    ## エフェクト処理
    # @brief メインの音声エフェクト処理を行います
    # @param input 入力音信号
    # @return output 出力音信号
    def effect(self, input):

        # 時間領域の変調処理
        effected = input
        if self.pre_booster_on == 1:
            effected = self.booster(effected, self.amp_pre_booster)
        if self.distortion_on == 1:
            effected = self.distortion(effected, self.threshold_distortion)
        if self.post_booster_on == 1:
            effected = self.booster(effected, self.amp_post_booster)

#        self.bufferdata = self.pushData(effected,self.bufferdata)

        # 周波数領域の変調処理
        if self.phaser_on == 1:
            effected = self.phaser(effected, self.shift_phaser, self.whole_counter)
#            self.bufferdata = self.gate(self.bufferdata)
#            buf0 = np.zeros(self.BUFFERSIZE)
#            buf1 = np.zeros(self.BUFFERSIZE)
#            buf2 = np.zeros(self.BUFFERSIZE)
#            buf0[:1024] = self.phaser(self.bufferdata[:1024], self.shift_phaser, self.whole_counter)
#            buf1[512:1536] = self.phaser(self.bufferdata[512:1536], self.shift_phaser, self.whole_counter+0.5)
#            buf2[1024:] = self.phaser(self.bufferdata[1024:], self.shift_phaser, self.whole_counter+1)
#            buf2 += buf0+buf1
#        effected = buf2[int(self.CHUNK/2):int(self.CHUNK*3/2)]

        # 時間領域に領域に変換
#        spectrum = self.restoreSpectrum(amp, phase)
#        effected = self.ifft(spectrum)
        self.whole_counter += 1

        # 出力
        output = np.array(effected, dtype="int16")
        return output

    """ エフェクト """
    ## ブースター
    # @brief 音の大きさを変動させます
    # @param input 入力音信号
    # @param amp 倍率
    # @return output 出力音信号
    def booster(self, input, amp):
        return input*amp

    ## ディスト―ション
    # @brief 音に歪みを加えます
    # @param input 入力音信号
    # @param threshold 音量の閾値
    # @return output 出力音信号
    def distortion(self, input, threshold):
        effected = []
        for i in range(len(input)):
            if input[i] > threshold:
                effected.append(threshold)
            elif input[i] < -threshold:
                effected.append(-threshold)
            else:
                effected.append(input[i])
        return np.array(effected,dtype="int16")

    ## フェーザー
    # @brief 位相を操作したエフェクトをかけます
    # @param phase 位相(input)
    # @param shift 位相のシフト量
    # @return output 位相(output)
    def phaser(self, effected, shift, counter):
        original = effected / 2
        spectrum = np.fft.fft(effected)
        amp = self.calcAmpSpectrum(spectrum)
        phase = self.calcPhaseSpectrum(spectrum)
        shifter = np.pi*shift*200*np.linspace(0,1,effected.shape[0]/2+1)
        shifter = np.delete(shifter,-1)
        shifter = np.concatenate([shifter, np.pi*shift*200*np.linspace(1,0,effected.shape[0]/2+1)])
        shifter = np.delete(shifter,-1)
        phase_shifted = phase + np.mod(shifter,np.pi)
        spectrum = self.restoreSpectrum(amp, phase_shifted)
        modulated = self.ifft(spectrum) / 2
        output = original + modulated
#        output = 2*modulated
        return output

    ## ノイズゲート
    # @brief 位相を操作したエフェクトをかけます
    # @param phase 位相(input)
    # @param shift 位相のシフト量
    # @return output 位相(output)
    def gate(self, effected):
        spectrum = np.fft.fft(effected)
        amp = self.calcAmpSpectrum(spectrum)
        phase = self.calcPhaseSpectrum(spectrum)
        spectrum = self.restoreSpectrum(amp, phase)
        output = self.ifft(spectrum)
        return output

    """ -----------------------------------------------------------------------
        Signal Processing
    ----------------------------------------------------------------------- """
    """ Processing """
    ## 信号処理
    # @param input
    def processing(self, input):
        pass

    """ FIFO Push Pop """
    ## キューのpush
    # @param input 値
    # @param buffer 入力配列(キュー)
    # @return output 出力配列(キュー)
    def pushData(self, input, buffer):
        buffer = np.delete(buffer, list(range(self.CHUNK)))
        buffer = np.append(buffer, input)
        return buffer

    """ -----------------------------------------------------------------------
        Spectrum
    ----------------------------------------------------------------------- """
    """ FFT """
    ## フーリエ変換
    # @param input 入力配列(音信号)
    # @param window 窓関数
    # @return spectrum 出力配列(スペクトラム)
    def fft(self, input, window):
        windowed = window*input
        spectrum = np.fft.fft(windowed)
        return spectrum

    """ 振幅スペクトラム """
    ## 振幅スペクトラムの作成
    # @param spectrum 入力配列(スペクトラム)
    # @return amp 出力配列(振幅スペクトラム)
    def calcAmpSpectrum(self, spectrum):
        amp = abs(spectrum)
        return amp

    """ パワースペクトラム """
    ## パワースペクトラムの作成
    # @param spectrum 入力配列(スペクトラム)
    # @return power 出力配列(パワースペクトラム)
    def calcPowerSpectrum(self, spectrum):
        power = abs(spectrum)**2
        return power

    """ 位相スペクトラム """
    ## 位相スペクトラムの作成
    # @param spectrum 入力配列(スペクトラム)
    # @return phase 出力配列(位相スペクトラム)
    def calcPhaseSpectrum(self, spectrum):
        phase = np.arctan2(np.imag(spectrum), np.real(spectrum))
        return phase

    """ フーリエスペクトラム復元 """
    ## パワースペクトラムの作成
    # @param amp 入力配列(振幅スペクトラム)
    # @param phase 入力配列(位相スペクトラム)
    # @return spectrum 出力配列(スペクトラム)
    def restoreSpectrum(self, amp, phase):
        real = amp * np.cos(phase)
        imag = amp * np.sin(phase)
        spectrum = list(map(complex, real, imag))
#        for i, no_use in enumerate(real):
#            spectrum.append(complex(real[i],imag[i]))
        return np.array(spectrum, dtype=complex)

    """ IFFT """
    ## 逆フーリエ変換
    # @param spectrum 出力配列(スペクトラム)
    # @return processed 出力配列(音信号)
    def ifft(self, spectrum):
        processed = np.real(np.fft.ifft(spectrum))
        return processed
    """ -----------------------------------------------------------------------
        Cepstrum
    ----------------------------------------------------------------------- """
    """ cepstrum """
    ## ケプストラム作成
    # @param spectrum 出力配列(スペクトラム)
    # @return cepstrum 出力配列(ケプストラム)
    def makeCepstrum(self, spectrum):
        logspectrum = 20*np.log10(spectrum)
        cepstrum = np.real(np.fft.ifft(logspectrum))
        return cepstrum

    """ pre-emphasis """
    ## プリエンファシスフィルタ
    # @param input 出力配列(音信号)
    # @return output 出力配列(フィルタ処理後信号)
    def preEmphasis(self, input):
        output = signal.lfilter([1,-0.97], 1, input)
        return output
    """ -----------------------------------------------------------------------
        Main function
    ----------------------------------------------------------------------- """
    ## メイン処理まとめ
    # @param stream 入力ストリーム
    def main(self, stream):
        """ input Data """
        input_data = stream.read(self.CHUNK)
        """ Pre-Process """
        raw_data = self.toInt16(input_data)
        if self.CHANNELS == 2 and self.MONORALRIGHT:
            raw_data = self.toMonoralRight(raw_data)
        elif self.CHANNELS == 2 and not self.MONORALRIGHT:
            raw_data = self.toMonoralLeft(raw_data)
        """ Effect """
        processed_data = self.effect(raw_data)
        """ Processing """

        """ Plot Data """
        self.analyzeddata = self.pushData(processed_data,self.analyzeddata)
        self.plotdata = processed_data/self.MAXLEVEL
        self.spectrum = self.fft(self.analyzeddata, self.HANNINGWINDOW)
        self.power = self.calcPowerSpectrum(self.spectrum)
        self.cepstrum = self.makeCepstrum(self.power)
        self.phase = self.calcPhaseSpectrum(self.spectrum)
        """ Post-Process """
        if self.CHANNELS == 2:
            processed_data = self.toStereo(processed_data)
        output_data = self.toStr(processed_data)
        """ output Data """
        stream.write(output_data)
