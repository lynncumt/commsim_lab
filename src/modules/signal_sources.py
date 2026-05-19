"""实验1: 信号源与基础分析 — 正弦波、方波、NRZ码，波形+功率谱"""
import numpy as np
from scipy.signal import welch
from PyQt5.QtWidgets import (
    QDoubleSpinBox, QSpinBox, QComboBox, QLabel, QCheckBox, QSlider
)
from PyQt5.QtCore import Qt
from src.ui.base_module import BaseModuleWidget, COLORS


class SignalSourcesWidget(BaseModuleWidget):
    def __init__(self, user, parent=None):
        super().__init__(user, rows=2, cols=2, figsize=(10, 6), parent=parent)
        self._build_controls()
        self._run()

    def _build_controls(self):
        self.add_section_title('📶  信号源参数')

        self._sig_type = QComboBox()
        self._sig_type.addItems(['正弦波 (Sine)', '方波 (Square)', 'NRZ码', '锯齿波 (Sawtooth)', '三角波 (Triangle)'])
        self.add_param_row('信号类型', self._sig_type)

        self._freq = QDoubleSpinBox()
        self._freq.setRange(0.1, 500.0)
        self._freq.setValue(10.0)
        self._freq.setSuffix(' Hz')
        self._freq.setSingleStep(1.0)
        self.add_param_row('频率', self._freq)

        self._amp = QDoubleSpinBox()
        self._amp.setRange(0.1, 10.0)
        self._amp.setValue(1.0)
        self._amp.setSuffix(' V')
        self.add_param_row('幅度', self._amp)

        self._dc = QDoubleSpinBox()
        self._dc.setRange(-5.0, 5.0)
        self._dc.setValue(0.0)
        self._dc.setSuffix(' V')
        self.add_param_row('直流分量', self._dc)

        self._duty = QSpinBox()
        self._duty.setRange(1, 99)
        self._duty.setValue(50)
        self._duty.setSuffix(' %')
        self.add_param_row('占空比(方波)', self._duty)

        self._fs = QComboBox()
        self._fs.addItems(['1000 Hz', '2000 Hz', '4000 Hz', '8000 Hz', '16000 Hz'])
        self._fs.setCurrentIndex(2)
        self.add_param_row('采样率', self._fs)

        self._duration = QDoubleSpinBox()
        self._duration.setRange(0.1, 5.0)
        self._duration.setValue(1.0)
        self._duration.setSuffix(' s')
        self.add_param_row('时长', self._duration)

        self.add_section_title('🔊  叠加噪声')
        self._add_noise = QCheckBox('叠加AWGN噪声')
        self._add_noise.setStyleSheet('color:#90a4ae;')
        self.ctrl_layout.addWidget(self._add_noise)

        self._snr = QDoubleSpinBox()
        self._snr.setRange(-10, 40)
        self._snr.setValue(20.0)
        self._snr.setSuffix(' dB')
        self.add_param_row('信噪比(SNR)', self._snr)

        self.add_spacer()
        self.add_run_button(callback=self._run)
        self.add_stretch()

    def _run(self):
        fs_map = {0: 1000, 1: 2000, 2: 4000, 3: 8000, 4: 16000}
        fs = fs_map[self._fs.currentIndex()]
        T = self._duration.value()
        f0 = self._freq.value()
        A = self._amp.value()
        dc = self._dc.value()
        t = np.arange(0, T, 1.0 / fs)

        sig_idx = self._sig_type.currentIndex()
        if sig_idx == 0:  # sine
            s = A * np.sin(2 * np.pi * f0 * t) + dc
        elif sig_idx == 1:  # square
            duty = self._duty.value() / 100.0
            from scipy.signal import square
            s = A * square(2 * np.pi * f0 * t, duty=duty) + dc
        elif sig_idx == 2:  # NRZ
            bit_dur = 1.0 / f0
            samps_per_bit = max(1, int(fs * bit_dur))
            n_bits = max(1, int(T * f0))
            bits = np.random.randint(0, 2, n_bits)
            s = np.repeat(bits * 2 - 1, samps_per_bit)
            s = s[:len(t)]
            if len(s) < len(t):
                s = np.pad(s, (0, len(t) - len(s)), 'edge')
            s = A * s + dc
        elif sig_idx == 3:  # sawtooth
            from scipy.signal import sawtooth
            s = A * sawtooth(2 * np.pi * f0 * t) + dc
        else:  # triangle
            from scipy.signal import sawtooth
            s = A * sawtooth(2 * np.pi * f0 * t, width=0.5) + dc

        if self._add_noise.isChecked():
            snr_db = self._snr.value()
            sig_power = np.mean(s ** 2)
            noise_power = sig_power / (10 ** (snr_db / 10))
            noise = np.random.normal(0, np.sqrt(noise_power), len(s))
            s_noisy = s + noise
        else:
            s_noisy = s

        # ── Plots ──────────────────────────────────────────────────────────
        self.canvas.clear_axes()
        ax0, ax1, ax2, ax3 = self.canvas.axes

        # Time domain — clean
        ax0.plot(t[:min(len(t), 4*fs)], s[:min(len(s), 4*fs)], color=COLORS[0], lw=1.5)
        ax0.set_title('时域波形（原始信号）')
        ax0.set_xlabel('时间 (s)')
        ax0.set_ylabel('幅度 (V)')
        ax0.grid(True, alpha=0.3)

        # Time domain — noisy
        ax1.plot(t[:min(len(t), 4*fs)], s_noisy[:min(len(s_noisy), 4*fs)], color=COLORS[1], lw=1.0)
        ax1.set_title('时域波形（含噪声）')
        ax1.set_xlabel('时间 (s)')
        ax1.set_ylabel('幅度 (V)')
        ax1.grid(True, alpha=0.3)

        # Power spectrum — original
        freqs, psd = welch(s, fs=fs, nperseg=min(512, len(s)))
        ax2.semilogy(freqs, psd + 1e-15, color=COLORS[2])
        ax2.set_title('功率谱密度（原始信号）')
        ax2.set_xlabel('频率 (Hz)')
        ax2.set_ylabel('PSD (V²/Hz)')
        ax2.set_xlim(0, min(fs / 2, f0 * 15 + 50))
        ax2.grid(True, alpha=0.3)

        # Power spectrum — noisy
        freqs2, psd2 = welch(s_noisy, fs=fs, nperseg=min(512, len(s_noisy)))
        ax3.semilogy(freqs2, psd2 + 1e-15, color=COLORS[3])
        ax3.set_title('功率谱密度（含噪声）')
        ax3.set_xlabel('频率 (Hz)')
        ax3.set_ylabel('PSD (V²/Hz)')
        ax3.set_xlim(0, min(fs / 2, f0 * 15 + 50))
        ax3.grid(True, alpha=0.3)

        self.canvas.fig.tight_layout(pad=1.5)
        self.canvas.draw()
