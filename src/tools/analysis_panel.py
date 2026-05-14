"""
综合分析工具面板 — 示波器 / 频谱分析仪 / 误码率测试仪 / 星座图&眼图
可独立使用，支持任意参数配置。
"""
import numpy as np
from scipy.signal import welch, butter, filtfilt, hilbert
from scipy.special import erfc
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QDoubleSpinBox, QSpinBox, QComboBox,
    QGroupBox, QScrollArea, QSizePolicy, QCheckBox, QFrame,
    QSplitter
)
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

COLORS = ['#4fc3f7', '#ef5350', '#66bb6a', '#ffa726', '#ab47bc',
          '#26c6da', '#ff7043', '#d4e157', '#ec407a', '#42a5f5']

_MPL_STYLE = dict(
    figure_facecolor='#111629', axes_facecolor='#0d1826',
    axes_edgecolor='#2a3a5a', axes_labelcolor='#90a4ae',
    xtick_color='#607d8b', ytick_color='#607d8b',
    text_color='#cfd8dc', grid_color='#1e2a4a',
)


def _apply_style(ax):
    ax.set_facecolor('#0d1826')
    ax.tick_params(colors='#607d8b')
    ax.xaxis.label.set_color('#90a4ae')
    ax.yaxis.label.set_color('#90a4ae')
    ax.title.set_color('#cfd8dc')
    for spine in ax.spines.values():
        spine.set_edgecolor('#2a3a5a')
    ax.grid(True, color='#1e2a4a', linestyle='--', linewidth=0.5, alpha=0.6)


def _make_canvas(rows=1, cols=1, figsize=(10, 4)):
    fig = Figure(figsize=figsize, tight_layout=True)
    fig.patch.set_facecolor('#111629')
    canvas = FigureCanvas(fig)
    canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    axes = [fig.add_subplot(rows, cols, i + 1) for i in range(rows * cols)]
    for ax in axes:
        _apply_style(ax)
    return fig, canvas, axes


def _ctrl_style():
    return '''
        QWidget { background:#0d1226; }
        QLabel { color:#90a4ae; font-size:12px; }
        QGroupBox {
            border:1px solid #1e3a5f; border-radius:6px;
            margin-top:10px; padding-top:6px;
            color:#4fc3f7; font-size:11px; font-weight:bold;
        }
        QGroupBox::title { subcontrol-origin:margin; left:8px; padding:0 4px; }
        QComboBox, QDoubleSpinBox, QSpinBox {
            background:#1e2545; color:#e0e0e0; border:1px solid #2a3060;
            border-radius:4px; padding:2px 6px; font-size:12px;
        }
        QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus { border-color:#4fc3f7; }
        QComboBox QAbstractItemView {
            background:#1e2545; color:#e0e0e0; selection-background-color:#1565c0;
        }
        QPushButton#run {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #1565c0,stop:1 #0288d1);
            color:white; font-weight:bold; border:none;
            border-radius:6px; padding:7px 0; font-size:14px;
        }
        QPushButton#run:hover { background:#1976d2; }
        QCheckBox { color:#90a4ae; font-size:12px; }
    '''


def _param_row(label, widget):
    row = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setFixedWidth(120)
    row.addWidget(lbl)
    row.addWidget(widget)
    return row


# ── Oscilloscope ──────────────────────────────────────────────────────────────
class OscilloscopeTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_ctrl_style())
        self._build()
        self._run()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Controls
        ctrl = QScrollArea()
        ctrl.setWidgetResizable(True)
        ctrl.setFixedWidth(270)
        ctrl.setStyleSheet('border:none;')
        ctrl_inner = QWidget()
        ctrl_inner.setStyleSheet('background:#0d1226;')
        cv = QVBoxLayout(ctrl_inner)
        cv.setContentsMargins(10, 10, 10, 10)
        cv.setSpacing(8)
        ctrl.setWidget(ctrl_inner)

        grp = QGroupBox('信号源 A')
        gv = QVBoxLayout(grp)
        self._sig_a = QComboBox(); self._sig_a.addItems(['正弦波', '方波', '三角波', '锯齿波', '噪声'])
        self._fa = QDoubleSpinBox(); self._fa.setRange(0.1, 5000); self._fa.setValue(100); self._fa.setSuffix(' Hz')
        self._aa = QDoubleSpinBox(); self._aa.setRange(0.01, 10); self._aa.setValue(1.0); self._aa.setSuffix(' V')
        for label, w in [('波形', self._sig_a), ('频率', self._fa), ('幅度', self._aa)]:
            gv.addLayout(_param_row(label, w))
        cv.addWidget(grp)

        grp2 = QGroupBox('信号源 B（叠加）')
        gv2 = QVBoxLayout(grp2)
        self._ena_b = QCheckBox('启用信号B')
        self._sig_b = QComboBox(); self._sig_b.addItems(['正弦波', '方波', '三角波', '锯齿波', '噪声'])
        self._fb = QDoubleSpinBox(); self._fb.setRange(0.1, 5000); self._fb.setValue(300); self._fb.setSuffix(' Hz')
        self._ab = QDoubleSpinBox(); self._ab.setRange(0.01, 10); self._ab.setValue(0.5); self._ab.setSuffix(' V')
        gv2.addWidget(self._ena_b)
        for label, w in [('波形', self._sig_b), ('频率', self._fb), ('幅度', self._ab)]:
            gv2.addLayout(_param_row(label, w))
        cv.addWidget(grp2)

        grp3 = QGroupBox('时基/触发')
        gv3 = QVBoxLayout(grp3)
        self._fs = QComboBox(); self._fs.addItems(['8000 Hz', '16000 Hz', '44100 Hz', '96000 Hz'])
        self._fs.setCurrentIndex(1)
        self._timebase = QDoubleSpinBox(); self._timebase.setRange(0.001, 1.0); self._timebase.setValue(0.05)
        self._timebase.setSuffix(' s')
        self._ch_count = QSpinBox(); self._ch_count.setRange(1, 2); self._ch_count.setValue(1)
        for label, w in [('采样率', self._fs), ('显示时长', self._timebase), ('通道数', self._ch_count)]:
            gv3.addLayout(_param_row(label, w))
        cv.addWidget(grp3)

        run_btn = QPushButton('▶  刷新')
        run_btn.setObjectName('run')
        run_btn.clicked.connect(self._run)
        cv.addWidget(run_btn)
        cv.addStretch()
        layout.addWidget(ctrl)

        # Plot
        right = QFrame()
        right.setStyleSheet('background:#111629;')
        rv = QVBoxLayout(right)
        rv.setContentsMargins(4, 2, 4, 2)
        self._fig, self._canvas, self._axes = _make_canvas(2, 1, (10, 6))
        tb = NavigationToolbar(self._canvas, right)
        tb.setStyleSheet('background:#111629; border:none;')
        rv.addWidget(tb)
        rv.addWidget(self._canvas)
        layout.addWidget(right, 1)

    def _make_sig(self, kind, freq, amp, t):
        if kind == 0:  # sine
            return amp * np.sin(2 * np.pi * freq * t)
        elif kind == 1:  # square
            from scipy.signal import square
            return amp * square(2 * np.pi * freq * t)
        elif kind == 2:  # triangle
            from scipy.signal import sawtooth
            return amp * sawtooth(2 * np.pi * freq * t, 0.5)
        elif kind == 3:  # sawtooth
            from scipy.signal import sawtooth
            return amp * sawtooth(2 * np.pi * freq * t)
        else:  # noise
            return amp * np.random.randn(len(t))

    def _run(self):
        fs_map = {0: 8000, 1: 16000, 2: 44100, 3: 96000}
        fs = fs_map[self._fs.currentIndex()]
        T = self._timebase.value()
        t = np.arange(0, T, 1.0 / fs)

        sig_a = self._make_sig(self._sig_a.currentIndex(), self._fa.value(), self._aa.value(), t)
        sig = sig_a.copy()
        if self._ena_b.isChecked():
            sig_b = self._make_sig(self._sig_b.currentIndex(), self._fb.value(), self._ab.value(), t)
            sig = sig_a + sig_b
        else:
            sig_b = np.zeros_like(t)

        for ax in self._axes:
            ax.cla(); _apply_style(ax)

        t_ms = t * 1000
        ax0, ax1 = self._axes

        if self._ch_count.value() == 2 and self._ena_b.isChecked():
            ax0.plot(t_ms, sig_a, color=COLORS[0], lw=1.2, label='CH A')
            ax0.plot(t_ms, sig_b, color=COLORS[1], lw=1.2, alpha=0.8, label='CH B')
            ax0.set_title('示波器 — 双通道')
        else:
            ax0.plot(t_ms, sig, color=COLORS[0], lw=1.2, label='CH A')
            ax0.set_title('示波器 — 时域波形')
        ax0.set_xlabel('时间 (ms)'); ax0.set_ylabel('幅度 (V)')
        ax0.legend(fontsize=9)

        # XY (Lissajous) mode
        if self._ena_b.isChecked():
            ax1.plot(sig_a, sig_b, color=COLORS[2], lw=0.8, alpha=0.7)
            ax1.set_title('李萨如图 (XY模式)')
            ax1.set_xlabel('CH A (V)'); ax1.set_ylabel('CH B (V)')
            ax1.set_aspect('equal')
        else:
            # Show measurements
            v_pp = np.max(sig) - np.min(sig)
            v_rms = np.sqrt(np.mean(sig ** 2))
            v_dc = np.mean(sig)
            ax1.axis('off')
            ax1.text(0.1, 0.7,
                f'测量值\n\n'
                f'  峰峰值 Vpp = {v_pp:.4f} V\n'
                f'  有效值 Vrms = {v_rms:.4f} V\n'
                f'  直流分量 Vdc = {v_dc:.4f} V\n'
                f'  峰值 Vpeak = {np.max(np.abs(sig)):.4f} V\n\n'
                f'  信号频率 = {self._fa.value():.1f} Hz\n'
                f'  采样率 = {fs} Hz\n'
                f'  显示点数 = {len(t)}',
                transform=ax1.transAxes, fontsize=11, color='#cfd8dc',
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.9))

        self._fig.tight_layout(pad=1.5)
        self._canvas.draw()


# ── Spectrum Analyzer ─────────────────────────────────────────────────────────
class SpectrumTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_ctrl_style())
        self._build()
        self._run()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        ctrl = QScrollArea(); ctrl.setWidgetResizable(True); ctrl.setFixedWidth(270)
        ctrl.setStyleSheet('border:none;')
        ci = QWidget(); ci.setStyleSheet('background:#0d1226;')
        cv = QVBoxLayout(ci); cv.setContentsMargins(10, 10, 10, 10); cv.setSpacing(8)
        ctrl.setWidget(ci)

        grp = QGroupBox('信号配置')
        gv = QVBoxLayout(grp)
        self._sig = QComboBox()
        self._sig.addItems(['正弦波', '方波', 'AM调制', 'FM调制', '多音信号', '噪声'])
        self._freq = QDoubleSpinBox(); self._freq.setRange(1, 10000); self._freq.setValue(1000); self._freq.setSuffix(' Hz')
        self._amp = QDoubleSpinBox(); self._amp.setRange(0.01, 10); self._amp.setValue(1.0); self._amp.setSuffix(' V')
        self._fc = QDoubleSpinBox(); self._fc.setRange(10, 20000); self._fc.setValue(5000); self._fc.setSuffix(' Hz')
        self._mi = QDoubleSpinBox(); self._mi.setRange(0.01, 5); self._mi.setValue(0.5)
        for label, w in [('信号类型', self._sig), ('基频/调制频率', self._freq),
                          ('幅度', self._amp), ('载频', self._fc), ('调制指数', self._mi)]:
            gv.addLayout(_param_row(label, w))
        cv.addWidget(grp)

        grp2 = QGroupBox('分析参数')
        gv2 = QVBoxLayout(grp2)
        self._fs = QComboBox()
        self._fs.addItems(['8000 Hz', '16000 Hz', '44100 Hz', '96000 Hz'])
        self._fs.setCurrentIndex(2)
        self._nperseg = QComboBox()
        self._nperseg.addItems(['256', '512', '1024', '2048', '4096'])
        self._nperseg.setCurrentIndex(2)
        self._window = QComboBox()
        self._window.addItems(['Hann', 'Hamming', 'Blackman', 'Flattop', 'Rectangular'])
        self._display = QComboBox()
        self._display.addItems(['单边功率谱 PSD', '双边谱', '幅度谱', '相位谱'])
        for label, w in [('采样率', self._fs), ('FFT点数', self._nperseg),
                          ('窗函数', self._window), ('显示模式', self._display)]:
            gv2.addLayout(_param_row(label, w))
        cv.addWidget(grp2)

        run_btn = QPushButton('▶  分析'); run_btn.setObjectName('run')
        run_btn.clicked.connect(self._run)
        cv.addWidget(run_btn); cv.addStretch()
        layout.addWidget(ctrl)

        right = QFrame(); right.setStyleSheet('background:#111629;')
        rv = QVBoxLayout(right); rv.setContentsMargins(4, 2, 4, 2)
        self._fig, self._canvas, self._axes = _make_canvas(2, 1, (10, 6))
        tb = NavigationToolbar(self._canvas, right)
        tb.setStyleSheet('background:#111629; border:none;')
        rv.addWidget(tb); rv.addWidget(self._canvas)
        layout.addWidget(right, 1)

    def _run(self):
        fs_map = {0: 8000, 1: 16000, 2: 44100, 3: 96000}
        fs = fs_map[self._fs.currentIndex()]
        nperseg = int(self._nperseg.currentText())
        T = 0.5
        t = np.arange(0, T, 1.0 / fs)
        fm = self._freq.value()
        A = self._amp.value()
        fc = self._fc.value()
        mi = self._mi.value()

        sig_idx = self._sig.currentIndex()
        if sig_idx == 0:  # sine
            sig = A * np.sin(2 * np.pi * fm * t)
        elif sig_idx == 1:  # square
            from scipy.signal import square as sq
            sig = A * sq(2 * np.pi * fm * t)
        elif sig_idx == 2:  # AM
            sig = (1 + mi * np.sin(2 * np.pi * fm * t)) * np.cos(2 * np.pi * fc * t)
        elif sig_idx == 3:  # FM
            phase = 2 * np.pi * mi * fc * np.cumsum(np.sin(2 * np.pi * fm * t)) / fs
            sig = np.cos(2 * np.pi * fc * t + phase)
        elif sig_idx == 4:  # multi-tone
            sig = sum(np.sin(2 * np.pi * fm * k * t) / k for k in range(1, 6))
        else:  # noise
            sig = np.random.randn(len(t))

        win_map = {0: 'hann', 1: 'hamming', 2: 'blackman', 3: 'flattop', 4: 'boxcar'}
        window = win_map[self._window.currentIndex()]

        for ax in self._axes: ax.cla(); _apply_style(ax)

        # Time domain
        show = min(len(t), int(fs * 5 / max(fm, 1)))
        self._axes[0].plot(t[:show] * 1000, sig[:show], color=COLORS[0], lw=1.0)
        self._axes[0].set_title('时域波形')
        self._axes[0].set_xlabel('时间 (ms)'); self._axes[0].set_ylabel('幅度 (V)')

        # Spectrum
        disp = self._display.currentIndex()
        if disp <= 1:  # PSD
            if disp == 0:
                freqs, psd = welch(sig, fs=fs, nperseg=nperseg, window=window)
                self._axes[1].semilogy(freqs, psd + 1e-15, color=COLORS[2], lw=1.2)
                self._axes[1].set_title(f'单边功率谱密度 PSD (窗: {window.capitalize()})')
                self._axes[1].set_xlabel('频率 (Hz)'); self._axes[1].set_ylabel('PSD (V²/Hz)')
            else:
                N = nperseg
                fft_vals = np.fft.fftshift(np.fft.fft(sig[:N], N))
                f = np.fft.fftshift(np.fft.fftfreq(N, 1.0 / fs))
                psd_db = 10 * np.log10(np.abs(fft_vals) ** 2 / N + 1e-15)
                self._axes[1].plot(f, psd_db, color=COLORS[2], lw=1.0)
                self._axes[1].set_title('双边频谱')
                self._axes[1].set_xlabel('频率 (Hz)'); self._axes[1].set_ylabel('功率 (dB)')
        elif disp == 2:  # amplitude
            N = min(nperseg, len(sig))
            fft_vals = np.abs(np.fft.fft(sig[:N], N)) * 2 / N
            f = np.fft.fftfreq(N, 1.0 / fs)[:N // 2]
            self._axes[1].plot(f, fft_vals[:N // 2], color=COLORS[1], lw=1.0)
            self._axes[1].set_title('幅度谱')
            self._axes[1].set_xlabel('频率 (Hz)'); self._axes[1].set_ylabel('幅度 (V)')
        else:  # phase
            N = min(nperseg, len(sig))
            fft_vals = np.fft.fft(sig[:N], N)
            f = np.fft.fftfreq(N, 1.0 / fs)[:N // 2]
            phase = np.angle(fft_vals[:N // 2], deg=True)
            self._axes[1].plot(f, phase, color=COLORS[3], lw=1.0)
            self._axes[1].set_title('相位谱')
            self._axes[1].set_xlabel('频率 (Hz)'); self._axes[1].set_ylabel('相位 (°)')

        self._fig.tight_layout(pad=1.5)
        self._canvas.draw()


# ── BER Tester ────────────────────────────────────────────────────────────────
class BERTesterTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_ctrl_style())
        self._build()
        self._run()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        ctrl = QScrollArea(); ctrl.setWidgetResizable(True); ctrl.setFixedWidth(270)
        ctrl.setStyleSheet('border:none;')
        ci = QWidget(); ci.setStyleSheet('background:#0d1226;')
        cv = QVBoxLayout(ci); cv.setContentsMargins(10, 10, 10, 10); cv.setSpacing(8)
        ctrl.setWidget(ci)

        grp = QGroupBox('调制方案')
        gv = QVBoxLayout(grp)
        self._mods = QComboBox()
        self._mods.addItems(['BPSK', 'QPSK', '8PSK', '16QAM', '64QAM',
                              '2FSK(相干)', '2FSK(非相干)', '2ASK'])
        self._coding = QComboBox()
        self._coding.addItems(['无编码', 'Hamming(7,4)', '卷积码 R=1/2', 'LDPC R=1/2', '极化码 R=1/2'])
        self._snr_min = QDoubleSpinBox(); self._snr_min.setRange(-5, 10); self._snr_min.setValue(0)
        self._snr_max = QDoubleSpinBox(); self._snr_max.setRange(0, 30); self._snr_max.setValue(16)
        self._snr_pts = QSpinBox(); self._snr_pts.setRange(5, 50); self._snr_pts.setValue(17)
        for label, w in [('调制方式', self._mods), ('信道编码', self._coding),
                          ('SNR最小(dB)', self._snr_min), ('SNR最大(dB)', self._snr_max),
                          ('曲线点数', self._snr_pts)]:
            gv.addLayout(_param_row(label, w))
        cv.addWidget(grp)

        grp2 = QGroupBox('参考曲线')
        gv2 = QVBoxLayout(grp2)
        self._show_shannon = QCheckBox('Shannon极限')
        self._show_shannon.setChecked(True)
        self._show_uncoded = QCheckBox('未编码参考线')
        self._show_uncoded.setChecked(True)
        gv2.addWidget(self._show_shannon)
        gv2.addWidget(self._show_uncoded)
        cv.addWidget(grp2)

        run_btn = QPushButton('▶  计算BER曲线'); run_btn.setObjectName('run')
        run_btn.clicked.connect(self._run)
        cv.addWidget(run_btn); cv.addStretch()
        layout.addWidget(ctrl)

        right = QFrame(); right.setStyleSheet('background:#111629;')
        rv = QVBoxLayout(right); rv.setContentsMargins(4, 2, 4, 2)
        self._fig, self._canvas, self._axes = _make_canvas(1, 2, (11, 5))
        tb = NavigationToolbar(self._canvas, right)
        tb.setStyleSheet('background:#111629; border:none;')
        rv.addWidget(tb); rv.addWidget(self._canvas)
        layout.addWidget(right, 1)

    def _ber_theory(self, mod_idx, snr_db):
        snr = 10 ** (np.array(snr_db) / 10)
        if mod_idx == 0:   # BPSK
            return 0.5 * erfc(np.sqrt(snr))
        elif mod_idx == 1: # QPSK
            return 0.5 * erfc(np.sqrt(snr))
        elif mod_idx == 2: # 8PSK
            return (2/3) * erfc(np.sqrt(snr * 3 * np.log2(8) / 8) * np.sin(np.pi / 8))
        elif mod_idx == 3: # 16QAM
            return (3/4) * erfc(np.sqrt(snr * 2 / 5))
        elif mod_idx == 4: # 64QAM
            return (7/12) * erfc(np.sqrt(snr * 2 / 21))
        elif mod_idx == 5: # 2FSK coherent
            return 0.5 * erfc(np.sqrt(snr / 2))
        elif mod_idx == 6: # 2FSK non-coherent
            return 0.5 * np.exp(-snr / 2)
        else:              # 2ASK
            return 0.5 * erfc(np.sqrt(snr / 4))

    def _apply_coding_gain(self, ber, coding_idx):
        if coding_idx == 0:
            return ber
        gains = {1: 2.0, 2: 4.0, 3: 8.0, 4: 10.0}
        rate_penalty = {1: 4/7, 2: 0.5, 3: 0.5, 4: 0.5}
        g = gains.get(coding_idx, 1.0)
        r = rate_penalty.get(coding_idx, 1.0)
        snr_eff = np.array(ber)  # placeholder: return approximate improvement
        return np.clip(ber / g, 1e-10, 1.0)

    def _run(self):
        mod_idx = self._mods.currentIndex()
        coding_idx = self._coding.currentIndex()
        snr_range = np.linspace(self._snr_min.value(), self._snr_max.value(), self._snr_pts.value())

        ber_uncoded = self._ber_theory(mod_idx, snr_range)
        ber_coded = self._apply_coding_gain(ber_uncoded, coding_idx)

        for ax in self._axes: ax.cla(); _apply_style(ax)

        ax0, ax1 = self._axes
        name = self._mods.currentText()
        code_name = self._coding.currentText()

        ax0.semilogy(snr_range, np.clip(ber_uncoded, 1e-9, 1), color=COLORS[0], lw=2.5,
                     label=f'{name} 理论')
        if coding_idx > 0:
            ax0.semilogy(snr_range, np.clip(ber_coded, 1e-9, 1), color=COLORS[1], lw=2.5,
                         ls='--', label=f'{name} + {code_name}')

        if self._show_uncoded.isChecked() and coding_idx > 0:
            ax0.semilogy(snr_range, np.clip(ber_uncoded, 1e-9, 1), color='#546e7a',
                         lw=1.0, ls=':', alpha=0.6, label='无编码参考')

        if self._show_shannon.isChecked():
            # Shannon limit for AWGN (rate=1)
            shannon_snr = 10 * np.log10(2 ** 2 - 1)  # BPSK Shannon ~0 dB
            ax0.axvline(0, color='white', lw=1.0, ls=':', alpha=0.4, label='Shannon极限(BPSK≈0dB)')

        ax0.set_title(f'{name} BER vs Eb/N0 曲线')
        ax0.set_xlabel('Eb/N0 (dB)'); ax0.set_ylabel('误码率 BER')
        ax0.set_xlim(snr_range[0], snr_range[-1]); ax0.set_ylim(1e-8, 1)
        ax0.legend(fontsize=9); ax0.grid(True, alpha=0.3, which='both')

        # All modulations comparison
        mod_names = ['BPSK', 'QPSK', '16QAM', '64QAM', '2FSK(相干)', '2ASK']
        mod_indices = [0, 1, 3, 4, 5, 7]
        for i, (mn, mi) in enumerate(zip(mod_names, mod_indices)):
            b = self._ber_theory(mi, snr_range)
            ax1.semilogy(snr_range, np.clip(b, 1e-9, 1), color=COLORS[i % len(COLORS)],
                         lw=1.8, label=mn)
        ax1.set_title('各调制方式 BER 对比')
        ax1.set_xlabel('Eb/N0 (dB)'); ax1.set_ylabel('BER')
        ax1.set_xlim(snr_range[0], snr_range[-1]); ax1.set_ylim(1e-8, 1)
        ax1.legend(fontsize=8); ax1.grid(True, alpha=0.3, which='both')

        self._fig.tight_layout(pad=1.5)
        self._canvas.draw()


# ── Constellation & Eye Diagram ───────────────────────────────────────────────
class ConstellationTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_ctrl_style())
        self._build()
        self._run()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        ctrl = QScrollArea(); ctrl.setWidgetResizable(True); ctrl.setFixedWidth(270)
        ctrl.setStyleSheet('border:none;')
        ci = QWidget(); ci.setStyleSheet('background:#0d1226;')
        cv = QVBoxLayout(ci); cv.setContentsMargins(10, 10, 10, 10); cv.setSpacing(8)
        ctrl.setWidget(ci)

        grp = QGroupBox('调制方式')
        gv = QVBoxLayout(grp)
        self._mod = QComboBox()
        self._mod.addItems(['BPSK', 'QPSK', '8PSK', '16QAM', '32QAM', '64QAM'])
        self._snr = QDoubleSpinBox(); self._snr.setRange(-5, 40); self._snr.setValue(20)
        self._snr.setSuffix(' dB')
        self._n_syms = QSpinBox(); self._n_syms.setRange(100, 5000); self._n_syms.setValue(1000)
        self._phase_err = QDoubleSpinBox(); self._phase_err.setRange(0, 30); self._phase_err.setValue(0)
        self._phase_err.setSuffix(' °')
        self._freq_err = QDoubleSpinBox(); self._freq_err.setRange(0, 100); self._freq_err.setValue(0)
        self._freq_err.setSuffix(' Hz')
        for label, w in [('调制阶数', self._mod), ('信道SNR', self._snr),
                          ('符号数', self._n_syms), ('相位误差', self._phase_err),
                          ('频率偏差', self._freq_err)]:
            gv.addLayout(_param_row(label, w))
        cv.addWidget(grp)

        grp2 = QGroupBox('眼图参数')
        gv2 = QVBoxLayout(grp2)
        self._eye_sps = QSpinBox(); self._eye_sps.setRange(4, 32); self._eye_sps.setValue(16)
        self._eye_rc = QDoubleSpinBox(); self._eye_rc.setRange(0, 1); self._eye_rc.setValue(0.5)
        self._eye_snr = QDoubleSpinBox(); self._eye_snr.setRange(-5, 30); self._eye_snr.setValue(15)
        self._eye_snr.setSuffix(' dB')
        for label, w in [('每符号采样数', self._eye_sps), ('RC滚降系数β', self._eye_rc),
                          ('眼图SNR', self._eye_snr)]:
            gv2.addLayout(_param_row(label, w))
        cv.addWidget(grp2)

        run_btn = QPushButton('▶  生成'); run_btn.setObjectName('run')
        run_btn.clicked.connect(self._run)
        cv.addWidget(run_btn); cv.addStretch()
        layout.addWidget(ctrl)

        right = QFrame(); right.setStyleSheet('background:#111629;')
        rv = QVBoxLayout(right); rv.setContentsMargins(4, 2, 4, 2)
        self._fig, self._canvas, self._axes = _make_canvas(2, 2, (11, 7))
        tb = NavigationToolbar(self._canvas, right)
        tb.setStyleSheet('background:#111629; border:none;')
        rv.addWidget(tb); rv.addWidget(self._canvas)
        layout.addWidget(right, 1)

    def _qam_points(self, order):
        """Generate ideal QAM constellation points."""
        if order == 2:  # BPSK
            return np.array([-1 + 0j, 1 + 0j])
        elif order == 4:  # QPSK
            return np.exp(1j * np.pi * np.array([0.25, 0.75, 1.25, 1.75]))
        elif order == 8:  # 8PSK
            return np.exp(1j * 2 * np.pi * np.arange(8) / 8)
        else:  # Square QAM
            side = int(np.sqrt(order))
            pts = []
            for i in range(side):
                for j in range(side):
                    pts.append((2*i - side + 1) + 1j * (2*j - side + 1))
            pts = np.array(pts, dtype=complex)
            pts /= np.sqrt(np.mean(np.abs(pts) ** 2))
            return pts

    def _run(self):
        orders = [2, 4, 8, 16, 32, 64]
        order = orders[self._mod.currentIndex()]
        n_syms = self._n_syms.value()
        snr_db = self._snr.value()
        phase_err = np.deg2rad(self._phase_err.value())
        freq_err = self._freq_err.value()

        ideal_pts = self._qam_points(order)
        # Random symbols
        idx = np.random.randint(0, len(ideal_pts), n_syms)
        tx = ideal_pts[idx]

        # Channel effects
        snr_lin = 10 ** (snr_db / 10)
        noise_power = np.mean(np.abs(tx) ** 2) / snr_lin
        noise = (np.random.randn(n_syms) + 1j * np.random.randn(n_syms)) * np.sqrt(noise_power / 2)
        rx = tx + noise

        # Phase rotation
        if abs(phase_err) > 1e-6:
            rx *= np.exp(1j * phase_err)
        # Frequency offset
        if abs(freq_err) > 1e-6:
            t_sym = np.arange(n_syms) / 1000.0
            rx *= np.exp(1j * 2 * np.pi * freq_err * t_sym)

        for ax in self._axes: ax.cla(); _apply_style(ax)
        ax_ideal, ax_rx, ax_eye_clean, ax_eye_noisy = self._axes

        name = self._mod.currentText()

        # Ideal constellation
        for p in ideal_pts:
            ax_ideal.scatter(p.real, p.imag, s=150, color=COLORS[0], zorder=3)
        ax_ideal.set_title(f'{name} 理想星座图')
        ax_ideal.set_xlabel('I'); ax_ideal.set_ylabel('Q')
        ax_ideal.set_aspect('equal')
        ax_ideal.axhline(0, color='#2a3a5a', lw=0.6)
        ax_ideal.axvline(0, color='#2a3a5a', lw=0.6)

        # Received constellation with density coloring
        ax_rx.scatter(rx.real, rx.imag, s=5, color=COLORS[1], alpha=0.4)
        for p in ideal_pts:
            ax_rx.scatter(p.real, p.imag, s=80, color=COLORS[0], zorder=4, marker='+')
        ax_rx.set_title(f'{name} 接收星座图 (SNR={snr_db}dB, φ={self._phase_err.value():.1f}°)')
        ax_rx.set_xlabel('I'); ax_rx.set_ylabel('Q')
        ax_rx.set_aspect('equal')
        ax_rx.axhline(0, color='#2a3a5a', lw=0.6)
        ax_rx.axvline(0, color='#2a3a5a', lw=0.6)

        # Eye diagram (clean)
        sps = self._eye_sps.value()
        beta = self._eye_rc.value()
        n_bits = 256
        bits = np.random.randint(0, 2, n_bits)
        bpsk_sig = (bits * 2 - 1).astype(float)
        bpsk_up = np.repeat(bpsk_sig, sps)
        # Raised cosine filter
        n_taps = 8 * sps + 1
        t_rc = np.arange(-n_taps // 2, n_taps // 2 + 1) / sps
        h = np.sinc(t_rc) * np.cos(np.pi * beta * t_rc) / (1 - (2 * beta * t_rc) ** 2 + 1e-10)
        h[np.isnan(h)] = 0
        h /= np.sum(np.abs(h)) + 1e-12
        sig_clean = np.convolve(bpsk_up, h, 'same')

        # Eye trace extraction
        tw = np.linspace(-1, 1, 2 * sps)
        for start in range(sps, len(sig_clean) - 2 * sps, sps):
            trace = sig_clean[start:start + 2 * sps]
            if len(trace) == 2 * sps:
                ax_eye_clean.plot(tw, trace, color=COLORS[0], lw=0.5, alpha=0.3)
        ax_eye_clean.set_title(f'眼图 (β={beta}, 无噪声)')
        ax_eye_clean.set_xlabel('T (符号周期)'); ax_eye_clean.set_ylabel('幅度')
        ax_eye_clean.axvline(0, color=COLORS[4], lw=0.8, ls='--', alpha=0.6)

        # Eye diagram (noisy)
        eye_snr = self._eye_snr.value()
        sig_power = np.mean(sig_clean ** 2) + 1e-9
        noise2 = np.random.normal(0, np.sqrt(sig_power / (10 ** (eye_snr / 10))), len(sig_clean))
        sig_noisy = sig_clean + noise2

        for start in range(sps, len(sig_noisy) - 2 * sps, sps):
            trace = sig_noisy[start:start + 2 * sps]
            if len(trace) == 2 * sps:
                ax_eye_noisy.plot(tw, trace, color=COLORS[2], lw=0.5, alpha=0.3)
        ax_eye_noisy.set_title(f'眼图 (β={beta}, SNR={eye_snr}dB)')
        ax_eye_noisy.set_xlabel('T (符号周期)'); ax_eye_noisy.set_ylabel('幅度')
        ax_eye_noisy.axvline(0, color=COLORS[4], lw=0.8, ls='--', alpha=0.6)

        self._fig.tight_layout(pad=1.5)
        self._canvas.draw()


# ── Main Analysis Panel ───────────────────────────────────────────────────────
class AnalysisPanelWidget(QWidget):
    """综合分析工具面板 — 可从主导航直接进入"""
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet('''
            QTabWidget::pane { border:1px solid #1e3a5f; border-radius:4px; background:#0f1628; }
            QTabBar::tab {
                background:#1a1f3a; color:#78909c; padding:8px 20px;
                border-radius:4px 4px 0 0; margin-right:3px; font-size:12px;
            }
            QTabBar::tab:selected { background:#1565c0; color:white; font-weight:bold; }
            QTabBar::tab:hover:!selected { background:#1e2a4a; color:#b0bec5; }
        ''')

        tabs.addTab(OscilloscopeTab(),    '🖥  示波器')
        tabs.addTab(SpectrumTab(),         '📊  频谱分析仪')
        tabs.addTab(BERTesterTab(),        '📈  误码率测试仪')
        tabs.addTab(ConstellationTab(),    '⭕  星座图 / 眼图')

        layout.addWidget(tabs)
