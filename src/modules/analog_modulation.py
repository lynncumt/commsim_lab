"""实验2: 模拟调制解调 — AM, DSB, SSB, FM, PM"""
import numpy as np
from scipy.signal import hilbert, butter, filtfilt, welch
from PyQt5.QtWidgets import QDoubleSpinBox, QComboBox, QLabel, QCheckBox, QTabWidget, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from src.ui.base_module import BaseModuleWidget, COLORS


def _butter_lpf(cutoff, fs, order=5):
    nyq = fs / 2
    b, a = butter(order, cutoff / nyq, btype='low')
    return b, a


def _lpf(signal, cutoff, fs):
    b, a = _butter_lpf(cutoff, fs)
    return filtfilt(b, a, signal)


def _butter_bpf(low, high, fs, order=4):
    nyq = fs / 2
    b, a = butter(order, [low / nyq, high / nyq], btype='band')
    return b, a


def _bpf(signal, low, high, fs):
    b, a = _butter_bpf(low, high, fs)
    return filtfilt(b, a, signal)


class AnalogModulationWidget(BaseModuleWidget):
    def __init__(self, user, parent=None):
        super().__init__(user, rows=3, cols=2, figsize=(11, 8), parent=parent)
        self._build_controls()
        self._run()

    def _build_controls(self):
        self.add_section_title('📡  调制参数')

        self._mod_type = QComboBox()
        self._mod_type.addItems(['AM (常规调幅)', 'DSB (双边带)', 'SSB-USB (上边带)', 'SSB-LSB (下边带)', 'FM (调频)', 'PM (调相)'])
        self.add_param_row('调制方式', self._mod_type)

        self._fm = QDoubleSpinBox()
        self._fm.setRange(0.1, 200.0)
        self._fm.setValue(5.0)
        self._fm.setSuffix(' Hz')
        self.add_param_row('调制信号频率', self._fm)

        self._fc = QDoubleSpinBox()
        self._fc.setRange(10.0, 2000.0)
        self._fc.setValue(100.0)
        self._fc.setSuffix(' Hz')
        self.add_param_row('载波频率', self._fc)

        self._ma = QDoubleSpinBox()
        self._ma.setRange(0.0, 2.0)
        self._ma.setValue(0.5)
        self._ma.setSingleStep(0.1)
        self.add_param_row('调制指数 m', self._ma)

        self._fs = QComboBox()
        self._fs.addItems(['4000 Hz', '8000 Hz', '16000 Hz'])
        self._fs.setCurrentIndex(1)
        self.add_param_row('采样率', self._fs)

        self._snr = QDoubleSpinBox()
        self._snr.setRange(-10, 50)
        self._snr.setValue(25.0)
        self._snr.setSuffix(' dB')
        self.add_param_row('信道SNR', self._snr)

        self.add_spacer()
        self.add_run_button(callback=self._run)
        self.add_stretch()

    def _run(self):
        fs_map = {0: 4000, 1: 8000, 2: 16000}
        fs = fs_map[self._fs.currentIndex()]
        T = 1.0
        fm = self._fm.value()
        fc = self._fc.value()
        m = self._ma.value()
        t = np.arange(0, T, 1.0 / fs)

        # Baseband message
        msg = np.sin(2 * np.pi * fm * t)
        carrier = np.cos(2 * np.pi * fc * t)

        mod_idx = self._mod_type.currentIndex()
        name = self._mod_type.currentText()

        if mod_idx == 0:  # AM
            s_tx = (1 + m * msg) * carrier
            # Demod: envelope detector
            analytic = hilbert(s_tx)
            envelope = np.abs(analytic)
            s_rx = envelope - np.mean(envelope)
            s_rx = s_rx / (np.max(np.abs(s_rx)) + 1e-9)

        elif mod_idx == 1:  # DSB
            s_tx = msg * carrier
            # Demod: coherent (multiply by carrier, LPF)
            demod = s_tx * carrier
            s_rx = _lpf(demod, fm * 2, fs)
            s_rx = s_rx / (np.max(np.abs(s_rx)) + 1e-9)

        elif mod_idx == 2:  # SSB-USB
            msg_hilbert = np.imag(hilbert(msg))
            s_tx = msg * np.cos(2 * np.pi * fc * t) - msg_hilbert * np.sin(2 * np.pi * fc * t)
            # Demod: coherent
            demod = s_tx * np.cos(2 * np.pi * fc * t)
            s_rx = _lpf(demod, fm * 2, fs)
            s_rx = s_rx / (np.max(np.abs(s_rx)) + 1e-9)

        elif mod_idx == 3:  # SSB-LSB
            msg_hilbert = np.imag(hilbert(msg))
            s_tx = msg * np.cos(2 * np.pi * fc * t) + msg_hilbert * np.sin(2 * np.pi * fc * t)
            demod = s_tx * np.cos(2 * np.pi * fc * t)
            s_rx = _lpf(demod, fm * 2, fs)
            s_rx = s_rx / (np.max(np.abs(s_rx)) + 1e-9)

        elif mod_idx == 4:  # FM
            kf = m * fc  # frequency deviation
            phase = 2 * np.pi * kf * np.cumsum(msg) / fs
            s_tx = np.cos(2 * np.pi * fc * t + phase)
            # Demod: FM discriminator via instantaneous frequency
            analytic = hilbert(s_tx)
            inst_phase = np.unwrap(np.angle(analytic))
            inst_freq = np.diff(inst_phase) / (2 * np.pi) * fs
            s_rx = _lpf(np.append(inst_freq, inst_freq[-1]) - fc, fm * 3, fs)
            s_rx = s_rx / (np.max(np.abs(s_rx)) + 1e-9)

        else:  # PM
            kp = m * np.pi
            s_tx = np.cos(2 * np.pi * fc * t + kp * msg)
            analytic = hilbert(s_tx)
            inst_phase = np.unwrap(np.angle(analytic))
            s_rx = inst_phase - 2 * np.pi * fc * t
            s_rx = s_rx / (np.max(np.abs(s_rx)) + 1e-9)

        # Add AWGN
        snr_db = self._snr.value()
        sig_power = np.mean(s_tx ** 2)
        noise_power = sig_power / (10 ** (snr_db / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), len(s_tx))
        s_ch = s_tx + noise

        # ── Plots ──────────────────────────────────────────────────────────
        self.canvas.clear_axes()
        axes = self.canvas.axes  # [0..5]

        show = min(int(fs * 4 / fm), len(t))

        # Row 0: message + carrier
        axes[0].plot(t[:show], msg[:show], color=COLORS[0], lw=1.5, label='调制信号 m(t)')
        axes[0].plot(t[:show], carrier[:show], color=COLORS[4], lw=0.8, alpha=0.6, label='载波 c(t)')
        axes[0].set_title('调制信号与载波')
        axes[0].set_xlabel('时间 (s)'); axes[0].set_ylabel('幅度')
        axes[0].legend(); axes[0].grid(True, alpha=0.3)

        # Row 0 col 1: modulated signal
        axes[1].plot(t[:show], s_tx[:show], color=COLORS[1], lw=1.2, label=f'{name}')
        axes[1].set_title(f'已调信号 ({name})')
        axes[1].set_xlabel('时间 (s)'); axes[1].set_ylabel('幅度')
        axes[1].legend(); axes[1].grid(True, alpha=0.3)

        # Row 1: channel output + spectrum
        axes[2].plot(t[:show], s_ch[:show], color=COLORS[3], lw=1.0, label='信道输出')
        axes[2].set_title('信道输出（含AWGN噪声）')
        axes[2].set_xlabel('时间 (s)'); axes[2].set_ylabel('幅度')
        axes[2].legend(); axes[2].grid(True, alpha=0.3)

        freqs, psd = welch(s_tx, fs=fs, nperseg=min(1024, len(s_tx)))
        axes[3].plot(freqs, 10 * np.log10(psd + 1e-15), color=COLORS[2])
        axes[3].set_title(f'已调信号功率谱')
        axes[3].set_xlabel('频率 (Hz)'); axes[3].set_ylabel('PSD (dB/Hz)')
        axes[3].set_xlim(0, min(fs / 2, fc * 3))
        axes[3].axvline(fc, color=COLORS[4], lw=0.8, ls='--', alpha=0.7, label=f'fc={fc}Hz')
        axes[3].legend(); axes[3].grid(True, alpha=0.3)

        # Row 2: demodulated signal comparison
        axes[4].plot(t[:show], msg[:show], color=COLORS[0], lw=1.5, label='原始信号')
        axes[4].plot(t[:show], s_rx[:show], color=COLORS[1], lw=1.0, ls='--', label='解调信号')
        axes[4].set_title('解调结果对比')
        axes[4].set_xlabel('时间 (s)'); axes[4].set_ylabel('归一化幅度')
        axes[4].legend(); axes[4].grid(True, alpha=0.3)

        # Row 2 col 1: message spectrum
        freqs_m, psd_m = welch(msg, fs=fs, nperseg=min(512, len(msg)))
        axes[5].plot(freqs_m, 10 * np.log10(psd_m + 1e-15), color=COLORS[0], label='原始信号谱')
        freqs_r, psd_r = welch(s_rx, fs=fs, nperseg=min(512, len(s_rx)))
        axes[5].plot(freqs_r, 10 * np.log10(psd_r + 1e-15), color=COLORS[1], ls='--', label='解调信号谱')
        axes[5].set_title('解调前后信号频谱对比')
        axes[5].set_xlabel('频率 (Hz)'); axes[5].set_ylabel('PSD (dB/Hz)')
        axes[5].set_xlim(0, min(fs / 2, fm * 10))
        axes[5].legend(); axes[5].grid(True, alpha=0.3)

        self.canvas.fig.tight_layout(pad=1.5)
        self.canvas.draw()
