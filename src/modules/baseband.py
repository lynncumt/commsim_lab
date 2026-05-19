"""实验7/8: 基带传输与码型变换 — NRZ/RZ/AMI/HDB3, 眼图, 奈奎斯特准则"""
import numpy as np
from scipy.signal import butter, filtfilt, lfilter
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox
from src.ui.base_module import BaseModuleWidget, COLORS


def _gen_bits(n):
    return np.random.randint(0, 2, n)


def _nrz_l(bits, sps):
    """NRZ-L: 1→+A, 0→-A"""
    return np.repeat(bits * 2 - 1, sps).astype(float)


def _nrz_rz(bits, sps):
    """RZ: 1→half-period pulse, 0→zero"""
    sig = np.zeros(len(bits) * sps)
    half = sps // 2
    for i, b in enumerate(bits):
        if b == 1:
            sig[i * sps:i * sps + half] = 1.0
    return sig


def _ami(bits, sps):
    """AMI: 0→0, 1→alternating ±1"""
    sig = np.zeros(len(bits) * sps)
    last = 1
    for i, b in enumerate(bits):
        if b == 1:
            sig[i * sps:(i + 1) * sps] = float(last)
            last = -last
    return sig


def _hdb3(bits, sps):
    """HDB3: AMI with substitution of 000+B4V pattern for runs of 4 zeros."""
    n = len(bits)
    codes = np.zeros(n)  # -1, 0, +1
    last_nonzero = 1
    zero_count = 0
    b_polarity = -1  # last B polarity

    i = 0
    while i < n:
        if bits[i] == 1:
            codes[i] = last_nonzero
            last_nonzero = -last_nonzero
            zero_count = 0
            i += 1
        else:
            # count consecutive zeros
            j = i
            while j < n and bits[j] == 0:
                j += 1
            run = j - i
            k = 0
            while k < run:
                remaining = run - k
                if remaining >= 4:
                    # substitute: B00V pattern
                    b_polarity = last_nonzero
                    # if violation condition: same polarity as last V
                    v_polarity = last_nonzero
                    codes[i + k] = b_polarity
                    last_nonzero = -last_nonzero
                    codes[i + k + 1] = 0
                    codes[i + k + 2] = 0
                    codes[i + k + 3] = v_polarity
                    last_nonzero = -last_nonzero
                    k += 4
                else:
                    codes[i + k] = 0
                    k += 1
            i = j

    sig = np.repeat(codes, sps).astype(float)
    return sig


def _raised_cosine(beta, sps, n_taps):
    """Raised cosine filter impulse response."""
    t = np.arange(-n_taps // 2, n_taps // 2 + 1) / sps
    h = np.zeros(len(t))
    for idx, ti in enumerate(t):
        if ti == 0:
            h[idx] = 1.0
        elif abs(ti) == 1 / (2 * beta) and beta != 0:
            h[idx] = (np.pi / 4) * np.sinc(1 / (2 * beta))
        else:
            num = np.sinc(ti) * np.cos(np.pi * beta * ti)
            den = 1 - (2 * beta * ti) ** 2
            h[idx] = num / (den + 1e-15)
    h /= np.sum(np.abs(h))
    return h


def _eye_diagram(signal, sps, n_traces=50):
    """Extract eye diagram traces (2*sps wide window)."""
    window = 2 * sps
    traces = []
    max_start = len(signal) - window
    step = sps
    starts = range(sps, max_start, step)
    for s in starts:
        if len(traces) >= n_traces:
            break
        traces.append(signal[s:s + window])
    return np.array(traces)


class BasebandWidget(BaseModuleWidget):
    def __init__(self, user, parent=None):
        super().__init__(user, rows=3, cols=2, figsize=(11, 8), parent=parent)
        self._build_controls()
        self._run()

    def _build_controls(self):
        self.add_section_title('📊  基带码型参数')

        self._code_type = QComboBox()
        self._code_type.addItems(['NRZ-L', 'RZ (归零码)', 'AMI (交替极性码)', 'HDB3', '对比所有码型'])
        self.add_param_row('码型选择', self._code_type)

        self._n_bits = QSpinBox()
        self._n_bits.setRange(8, 256)
        self._n_bits.setValue(32)
        self.add_param_row('比特数', self._n_bits)

        self._sps = QSpinBox()
        self._sps.setRange(4, 64)
        self._sps.setValue(16)
        self.add_param_row('每符号采样数', self._sps)

        self._snr = QDoubleSpinBox()
        self._snr.setRange(-5, 30)
        self._snr.setValue(15.0)
        self._snr.setSuffix(' dB')
        self.add_param_row('信道SNR', self._snr)

        self.add_section_title('👁  眼图参数')

        self._rc_beta = QDoubleSpinBox()
        self._rc_beta.setRange(0.0, 1.0)
        self._rc_beta.setValue(0.5)
        self._rc_beta.setSingleStep(0.1)
        self.add_param_row('升余弦滚降系数β', self._rc_beta)

        self._eye_traces = QSpinBox()
        self._eye_traces.setRange(10, 200)
        self._eye_traces.setValue(80)
        self.add_param_row('眼图叠加条数', self._eye_traces)

        self.add_spacer()
        self.add_run_button(callback=self._run)
        self.add_stretch()

    def _run(self):
        n_bits = self._n_bits.value()
        sps = self._sps.value()
        snr_db = self._snr.value()
        beta = self._rc_beta.value()
        code_idx = self._code_type.currentIndex()

        bits = _gen_bits(n_bits)

        self.canvas.clear_axes()
        axes = self.canvas.axes

        if code_idx == 4:
            self._plot_all_codes(axes, bits, sps, snr_db, beta)
        else:
            code_fns = [_nrz_l, _nrz_rz, _ami, _hdb3]
            code_name = ['NRZ-L', 'RZ', 'AMI', 'HDB3'][code_idx]
            sig = code_fns[code_idx](bits, sps)
            self._plot_single_code(axes, bits, sig, sps, snr_db, beta, code_name)

        self.canvas.fig.tight_layout(pad=1.5)
        self.canvas.draw()

    def _plot_single_code(self, axes, bits, sig, sps, snr_db, beta, name):
        t = np.arange(len(sig))
        show = min(len(sig), 32 * sps)

        axes[0].step(t[:show], sig[:show], where='post', color=COLORS[0], lw=1.5)
        axes[0].set_title(f'{name} 码型波形')
        axes[0].set_xlabel('样本序号'); axes[0].set_ylabel('幅度')
        axes[0].set_ylim(-1.6, 1.6)
        axes[0].grid(True, alpha=0.3)

        # RC filtered signal
        h_rc = _raised_cosine(beta, sps, 8 * sps + 1)
        sig_filt = np.convolve(sig, h_rc, mode='same')

        # Add AWGN
        sig_power = np.mean(sig_filt ** 2) + 1e-9
        noise_power = sig_power / (10 ** (snr_db / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), len(sig_filt))
        sig_noisy = sig_filt + noise

        axes[1].plot(t[:show], sig_filt[:show], color=COLORS[2], lw=1.5, label='RC滤波后')
        axes[1].plot(t[:show], sig_noisy[:show], color=COLORS[3], lw=0.8, alpha=0.7, label=f'加噪 (SNR={snr_db}dB)')
        axes[1].set_title(f'升余弦滤波后信号 (β={beta})')
        axes[1].set_xlabel('样本序号'); axes[1].set_ylabel('幅度')
        axes[1].legend(fontsize=8); axes[1].grid(True, alpha=0.3)

        # Power spectrum
        from scipy.signal import welch
        fs_norm = 1.0
        freqs, psd = welch(sig, fs=fs_norm, nperseg=min(512, len(sig)))
        axes[2].semilogy(freqs * sps, psd + 1e-15, color=COLORS[0], label=name)
        freqs2, psd2 = welch(sig_filt, fs=fs_norm, nperseg=min(512, len(sig_filt)))
        axes[2].semilogy(freqs2 * sps, psd2 + 1e-15, color=COLORS[2], ls='--', label='RC滤波后')
        axes[2].set_title('基带信号功率谱')
        axes[2].set_xlabel('归一化频率 (f/Rb)'); axes[2].set_ylabel('PSD')
        axes[2].set_xlim(0, 2)
        axes[2].axvline(0.5, color=COLORS[4], ls=':', lw=0.8, label='奈奎斯特频率')
        axes[2].legend(fontsize=8); axes[2].grid(True, alpha=0.3)

        # Eye diagram — before filtering
        eye_raw = _eye_diagram(sig, sps, self._eye_traces.value())
        tw = np.linspace(-1, 1, 2 * sps)
        for trace in eye_raw:
            axes[3].plot(tw, trace, color=COLORS[0], lw=0.5, alpha=0.3)
        axes[3].set_title(f'眼图 ({name}, 滤波前)')
        axes[3].set_xlabel('T (符号周期归一化)'); axes[3].set_ylabel('幅度')
        axes[3].axvline(0, color=COLORS[4], ls='--', lw=0.8, alpha=0.6)
        axes[3].axhline(0, color='#546e7a', ls=':', lw=0.5)
        axes[3].grid(True, alpha=0.3)

        # Eye diagram — after filtering + noise
        eye_filt = _eye_diagram(sig_noisy, sps, self._eye_traces.value())
        for trace in eye_filt:
            axes[4].plot(tw, trace, color=COLORS[2], lw=0.5, alpha=0.3)
        axes[4].set_title(f'眼图 ({name}, RC+AWGN, β={beta}, SNR={snr_db}dB)')
        axes[4].set_xlabel('T (符号周期归一化)'); axes[4].set_ylabel('幅度')
        axes[4].axvline(0, color=COLORS[4], ls='--', lw=0.8, alpha=0.6)
        axes[4].axhline(0, color='#546e7a', ls=':', lw=0.5)
        axes[4].grid(True, alpha=0.3)

        axes[5].axis('off')
        axes[5].text(0.1, 0.5,
            f'奈奎斯特第一准则\n\n'
            f'无码间干扰(ISI)条件:\n'
            f'  带宽 B = Rb/2 (理想)\n'
            f'  实际: B = Rb(1+β)/2\n\n'
            f'当前参数:\n'
            f'  码型: {name}\n'
            f'  滚降系数 β = {beta}\n'
            f'  SNR = {snr_db} dB\n\n'
            f'眼图开合越大 → ISI越小\n'
            f'眼图开合越小 → ISI越大',
            transform=axes[5].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

    def _plot_all_codes(self, axes, bits, sps, snr_db, beta):
        show_bits = min(len(bits), 16)
        t = np.arange(show_bits * sps)

        codes = [
            ('NRZ-L', _nrz_l(bits[:show_bits], sps), COLORS[0]),
            ('RZ',    _nrz_rz(bits[:show_bits], sps), COLORS[1]),
            ('AMI',   _ami(bits[:show_bits], sps), COLORS[2]),
            ('HDB3',  _hdb3(bits[:show_bits], sps), COLORS[3]),
        ]

        for i, (name, sig, color) in enumerate(codes):
            ax = axes[i]
            ax.step(t, sig, where='post', color=color, lw=1.5)
            ax.set_title(f'{name}')
            ax.set_ylabel('幅度'); ax.set_xlabel('样本')
            ax.set_ylim(-1.6, 1.6)
            ax.grid(True, alpha=0.3)
            # Mark bit boundaries
            for j in range(show_bits + 1):
                ax.axvline(j * sps, color='#1e3a5f', lw=0.6, ls=':')

        # Bit labels on top of NRZ-L
        for j, b in enumerate(bits[:show_bits]):
            axes[0].text(j * sps + sps / 2, 1.3, str(b),
                         ha='center', va='bottom', fontsize=8, color='#90a4ae')

        # Spectrum comparison
        from scipy.signal import welch
        for name, sig, color in codes:
            f, p = welch(sig, nperseg=min(256, len(sig)))
            axes[4].semilogy(f * sps, p + 1e-15, color=color, lw=1.5, label=name)
        axes[4].set_title('四种基带码型功率谱对比')
        axes[4].set_xlabel('归一化频率 (f/Rb)'); axes[4].set_ylabel('PSD')
        axes[4].set_xlim(0, 2)
        axes[4].legend(fontsize=9); axes[4].grid(True, alpha=0.3)

        axes[5].axis('off')
        axes[5].text(0.05, 0.95,
            '基带码型特性对比\n\n'
            '  NRZ-L:  单极性不归零, 含直流\n'
            '  RZ:     归零码, 时钟信息丰富\n'
            '  AMI:    无直流, 含±1极性\n'
            '  HDB3:   高密度双极性3型\n'
            '           限制连零串最多3个\n\n'
            'HDB3 是 PCM 系统标准码型\n'
            '(E1/T1 电话网使用)',
            transform=axes[5].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))
