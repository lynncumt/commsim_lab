"""扩展: 新型频带调制 — QPSK, 16QAM, MSK + 星座图"""
import numpy as np
from scipy.signal import butter, filtfilt, hilbert
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QComboBox
from src.ui.base_module import BaseModuleWidget, COLORS


def _lpf(sig, cutoff, fs, order=5):
    nyq = fs / 2
    b, a = butter(order, min(cutoff / nyq, 0.99), btype='low')
    return filtfilt(b, a, sig)


def _awgn(sig, snr_db):
    sp = np.mean(np.abs(sig) ** 2) + 1e-12
    np_val = sp / (10 ** (snr_db / 10))
    noise = (np.random.randn(*sig.shape) + 1j * np.random.randn(*sig.shape)) * np.sqrt(np_val / 2)
    return sig + noise


# ── QPSK ──────────────────────────────────────────────────────────────────────
def qpsk_mod(bits, fc, fs, rb):
    sps = max(1, int(fs / rb))
    n_syms = len(bits) // 2
    syms_i = bits[:n_syms * 2:2] * 2 - 1   # ±1
    syms_q = bits[1:n_syms * 2:2] * 2 - 1
    t = np.arange(n_syms * sps) / fs
    I = np.repeat(syms_i.astype(float), sps)
    Q = np.repeat(syms_q.astype(float), sps)
    s = I * np.cos(2 * np.pi * fc * t) - Q * np.sin(2 * np.pi * fc * t)
    return s, syms_i, syms_q, t


def qpsk_demod(s_rx, fc, fs, rb, n_syms):
    sps = max(1, int(fs / rb))
    t = np.arange(len(s_rx)) / fs
    I_raw = _lpf(s_rx * np.cos(2 * np.pi * fc * t), rb * 1.5, fs)
    Q_raw = _lpf(-s_rx * np.sin(2 * np.pi * fc * t), rb * 1.5, fs)
    # Sample at symbol centers
    centers = np.array([int((i + 0.5) * sps) for i in range(n_syms)])
    centers = centers[centers < len(I_raw)]
    return I_raw[centers], Q_raw[centers]


# ── 16-QAM ────────────────────────────────────────────────────────────────────
QAM16_GRAY = {  # 4-bit gray code → (I, Q) normalized
    0b0000: (-3, -3), 0b0001: (-3, -1), 0b0011: (-3,  3), 0b0010: (-3,  1),
    0b0100: (-1, -3), 0b0101: (-1, -1), 0b0111: (-1,  3), 0b0110: (-1,  1),
    0b1100: ( 3, -3), 0b1101: ( 3, -1), 0b1111: ( 3,  3), 0b1110: ( 3,  1),
    0b1000: ( 1, -3), 0b1001: ( 1, -1), 0b1011: ( 1,  3), 0b1010: ( 1,  1),
}
_QAM16_POINTS = np.array(list(QAM16_GRAY.values()), dtype=float) / 3.0  # normalize to unit avg power


def qam16_mod(bits, fc, fs, rb):
    sps = max(1, int(fs / rb))
    n_syms = len(bits) // 4
    t = np.arange(n_syms * sps) / fs
    syms_iq = []
    for i in range(n_syms):
        nibble = (bits[4*i] << 3) | (bits[4*i+1] << 2) | (bits[4*i+2] << 1) | bits[4*i+3]
        iq = QAM16_GRAY.get(nibble, (0, 0))
        syms_iq.append(iq)
    syms_iq = np.array(syms_iq, dtype=float) / 3.0
    I = np.repeat(syms_iq[:, 0], sps)
    Q = np.repeat(syms_iq[:, 1], sps)
    s = I * np.cos(2 * np.pi * fc * t) - Q * np.sin(2 * np.pi * fc * t)
    return s, syms_iq[:, 0], syms_iq[:, 1], t


# ── MSK ───────────────────────────────────────────────────────────────────────
def msk_mod(bits, fc, fs, rb):
    sps = max(1, int(fs / rb))
    h = 0.5  # modulation index for MSK
    t_full = np.arange(len(bits) * sps) / fs
    phase = np.zeros(len(bits) * sps)
    phase_acc = 0.0
    for i, b in enumerate(bits):
        fi = fc + (b * 2 - 1) * rb * h  # f = fc ± Rb/4
        seg_t = np.arange(sps) / fs
        seg_phase = 2 * np.pi * fi * seg_t + phase_acc
        phase[i * sps:(i + 1) * sps] = seg_phase
        phase_acc = seg_phase[-1] + 2 * np.pi * fi / fs
    s = np.cos(phase)
    return s, t_full


class AdvancedModulationWidget(BaseModuleWidget):
    def __init__(self, user, parent=None):
        super().__init__(user, rows=3, cols=2, figsize=(11, 8), parent=parent)
        self._build_controls()
        self._run()

    def _build_controls(self):
        self.add_section_title('🌐  高阶调制参数')

        self._mod = QComboBox()
        self._mod.addItems(['QPSK', '16QAM', 'MSK', 'BER曲线对比'])
        self.add_param_row('调制方式', self._mod)

        self._n_bits = QSpinBox()
        self._n_bits.setRange(32, 2048)
        self._n_bits.setValue(512)
        self.add_param_row('比特数', self._n_bits)

        self._rb = QDoubleSpinBox()
        self._rb.setRange(1, 200)
        self._rb.setValue(10.0)
        self._rb.setSuffix(' bps')
        self.add_param_row('码元速率', self._rb)

        self._fc = QDoubleSpinBox()
        self._fc.setRange(20, 2000)
        self._fc.setValue(200.0)
        self._fc.setSuffix(' Hz')
        self.add_param_row('载波频率', self._fc)

        self._snr = QDoubleSpinBox()
        self._snr.setRange(-5, 30)
        self._snr.setValue(15.0)
        self._snr.setSuffix(' dB')
        self.add_param_row('信道 Eb/N0', self._snr)

        self.add_spacer()
        self.add_run_button(callback=self._run)
        self.add_stretch()

    def _run(self):
        mod_idx = self._mod.currentIndex()
        if mod_idx == 3:
            self._plot_ber()
            return

        n_bits = self._n_bits.value()
        rb = self._rb.value()
        fc = self._fc.value()
        snr_db = self._snr.value()
        fs = max(fc * 20, rb * 40)

        bits = np.random.randint(0, 2, n_bits)

        self.canvas.clear_axes()
        axes = self.canvas.axes

        if mod_idx == 0:  # QPSK
            self._plot_qpsk(axes, bits, fc, fs, rb, snr_db)
        elif mod_idx == 1:  # 16QAM
            self._plot_16qam(axes, bits, fc, fs, rb, snr_db)
        else:  # MSK
            self._plot_msk(axes, bits, fc, fs, rb, snr_db)

        self.canvas.fig.tight_layout(pad=1.5)
        self.canvas.draw()

    def _plot_qpsk(self, axes, bits, fc, fs, rb, snr_db):
        n_bits = len(bits) & ~1  # even
        s_tx, si, sq, t = qpsk_mod(bits[:n_bits], fc, fs, rb)
        n_syms = len(si)

        # AWGN on complex baseband
        sig_power = np.mean(s_tx ** 2) + 1e-12
        noise_power = sig_power / (10 ** (snr_db / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), len(s_tx))
        s_rx = s_tx + noise

        I_rx, Q_rx = qpsk_demod(s_rx, fc, fs, rb, n_syms)

        sps = max(1, int(fs / rb))
        show = min(len(s_tx), 8 * sps)

        # Waveform
        axes[0].plot(t[:show], s_tx[:show], color=COLORS[1], lw=1.0)
        axes[0].set_title('QPSK 调制波形')
        axes[0].set_xlabel('时间 (s)'); axes[0].set_ylabel('幅度')
        axes[0].grid(True, alpha=0.3)

        # Ideal constellation
        ax1 = axes[1]
        for b0, b1, (ic, qc) in [
            (0, 0, (1, 1)), (0, 1, (1, -1)), (1, 0, (-1, 1)), (1, 1, (-1, -1))
        ]:
            ax1.scatter([ic], [qc], s=200, color=COLORS[0], zorder=3)
            ax1.annotate(f'{b0}{b1}', (ic, qc), textcoords='offset points',
                         xytext=(5, 5), fontsize=10, color='#cfd8dc')
        ax1.axhline(0, color='#2a3a5a', lw=0.8)
        ax1.axvline(0, color='#2a3a5a', lw=0.8)
        ax1.set_title('QPSK 理想星座图'); ax1.set_xlabel('I'); ax1.set_ylabel('Q')
        ax1.set_xlim(-2, 2); ax1.set_ylim(-2, 2)
        ax1.set_aspect('equal'); ax1.grid(True, alpha=0.3)

        # Received constellation
        axes[2].scatter(I_rx, Q_rx, s=10, color=COLORS[1], alpha=0.6)
        axes[2].axhline(0, color='#2a3a5a', lw=0.8)
        axes[2].axvline(0, color='#2a3a5a', lw=0.8)
        axes[2].set_title(f'QPSK 接收星座图 (SNR={snr_db}dB)')
        axes[2].set_xlabel('I'); axes[2].set_ylabel('Q')
        axes[2].set_aspect('equal'); axes[2].grid(True, alpha=0.3)

        # Decision regions
        axes[3].scatter(I_rx, Q_rx, s=10, alpha=0.5,
                        c=['red' if (i < 0) else 'blue' for i in I_rx])
        axes[3].axhline(0, color='white', lw=1.5, ls='--')
        axes[3].axvline(0, color='white', lw=1.5, ls='--')
        axes[3].set_title('QPSK 判决区域')
        axes[3].set_xlabel('I'); axes[3].set_ylabel('Q')
        axes[3].set_aspect('equal'); axes[3].grid(True, alpha=0.3)

        # BER
        rx_I = np.sign(I_rx) > 0
        rx_Q = np.sign(Q_rx) > 0
        tx_I = (si > 0)
        tx_Q = (sq > 0)
        n = min(len(tx_I), len(rx_I))
        ber = (np.sum(tx_I[:n] != rx_I[:n]) + np.sum(tx_Q[:n] != rx_Q[:n])) / (2 * n)

        from scipy.special import erfc
        snr_lin = 10 ** (snr_db / 10)
        ber_theory = 0.5 * erfc(np.sqrt(snr_lin))

        axes[4].axis('off')
        axes[4].text(0.1, 0.5,
            f'QPSK 仿真结果\n\n'
            f'比特数: {len(bits)}\n'
            f'符号数: {n_syms}\n'
            f'SNR = {snr_db} dB\n\n'
            f'仿真 BER = {ber:.4f}\n'
            f'理论 BER = {ber_theory:.4f}\n\n'
            f'QPSK 频谱效率: 2 bit/s/Hz\n'
            f'比 BPSK 高 2倍',
            transform=axes[4].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        axes[5].axis('off')
        axes[5].text(0.1, 0.5,
            'QPSK 调制原理\n\n'
            'I/Q 正交双路 BPSK\n\n'
            '映射关系 (Gray码):\n'
            '  00 → ( 1, 1) = 45°\n'
            '  01 → ( 1,-1) = -45°\n'
            '  10 → (-1, 1) = 135°\n'
            '  11 → (-1,-1) = -135°\n\n'
            '相位集合: {±45°, ±135°}',
            transform=axes[5].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))

    def _plot_16qam(self, axes, bits, fc, fs, rb, snr_db):
        n_bits = (len(bits) // 4) * 4
        s_tx, si, sq, t = qam16_mod(bits[:n_bits], fc, fs, rb)
        n_syms = len(si)
        sps = max(1, int(fs / rb))

        sig_power = np.mean(s_tx ** 2) + 1e-12
        noise_power = sig_power / (10 ** (snr_db / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), len(s_tx))
        s_rx = s_tx + noise

        # Demod via coherent detection
        t_full = np.arange(len(s_rx)) / fs
        I_raw = _lpf(s_rx * np.cos(2 * np.pi * fc * t_full), rb * 1.5, fs)
        Q_raw = _lpf(-s_rx * np.sin(2 * np.pi * fc * t_full), rb * 1.5, fs)
        centers = [int((i + 0.5) * sps) for i in range(n_syms) if int((i + 0.5) * sps) < len(I_raw)]
        I_rx = I_raw[centers]
        Q_rx = Q_raw[centers]

        show = min(len(t), 8 * sps)
        axes[0].plot(t[:show], s_tx[:show], color=COLORS[1], lw=0.8)
        axes[0].set_title('16QAM 调制波形')
        axes[0].set_xlabel('时间 (s)'); axes[0].set_ylabel('幅度')
        axes[0].grid(True, alpha=0.3)

        # Ideal constellation
        pts = np.array(list(QAM16_GRAY.values()), dtype=float) / 3.0
        axes[1].scatter(pts[:, 0], pts[:, 1], s=120, color=COLORS[0], zorder=3)
        for k, (iv, qv) in QAM16_GRAY.items():
            axes[1].annotate(f'{k:04b}', (iv / 3, qv / 3),
                             textcoords='offset points', xytext=(3, 3), fontsize=7, color='#90a4ae')
        axes[1].axhline(0, color='#2a3a5a', lw=0.8)
        axes[1].axvline(0, color='#2a3a5a', lw=0.8)
        axes[1].set_title('16QAM 理想星座图'); axes[1].set_xlabel('I'); axes[1].set_ylabel('Q')
        axes[1].set_aspect('equal'); axes[1].grid(True, alpha=0.3)

        axes[2].scatter(I_rx, Q_rx, s=8, color=COLORS[1], alpha=0.5)
        axes[2].axhline(0, color='#2a3a5a', lw=0.8)
        axes[2].axvline(0, color='#2a3a5a', lw=0.8)
        axes[2].set_title(f'16QAM 接收星座图 (SNR={snr_db}dB)')
        axes[2].set_xlabel('I'); axes[2].set_ylabel('Q')
        axes[2].set_aspect('equal'); axes[2].grid(True, alpha=0.3)

        # Decision grid
        for thresh in [-2/3, 0, 2/3]:
            axes[3].axhline(thresh, color='white', lw=0.8, ls='--', alpha=0.6)
            axes[3].axvline(thresh, color='white', lw=0.8, ls='--', alpha=0.6)
        axes[3].scatter(I_rx, Q_rx, s=8, color=COLORS[3], alpha=0.5)
        axes[3].set_title('16QAM 判决格栅')
        axes[3].set_xlabel('I'); axes[3].set_ylabel('Q')
        axes[3].set_aspect('equal'); axes[3].grid(True, alpha=0.3)

        # Nearest-neighbor decision BER estimate
        def nearest_decision(i_val, q_val):
            dists = np.sqrt((pts[:, 0] - i_val) ** 2 + (pts[:, 1] - q_val) ** 2)
            return np.argmin(dists)

        orig_indices = [nearest_decision(si[k], sq[k]) for k in range(len(si))]
        recv_indices = [nearest_decision(I_rx[k] / 2, Q_rx[k] / 2) for k in range(len(I_rx))]  # scale back
        n = min(len(orig_indices), len(recv_indices))
        sym_err = sum(1 for a, b in zip(orig_indices[:n], recv_indices[:n]) if a != b)
        ser = sym_err / n if n > 0 else 0

        axes[4].axis('off')
        axes[4].text(0.1, 0.5,
            f'16QAM 仿真结果\n\n'
            f'符号数: {n_syms}\n'
            f'比特/符号: 4 bit/sym\n'
            f'SNR = {snr_db} dB\n\n'
            f'仿真符号错误率: {ser:.4f}\n\n'
            f'16QAM 频谱效率: 4 bit/s/Hz\n'
            f'是 QPSK 的 2 倍\n'
            f'但需要更高 SNR',
            transform=axes[4].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        axes[5].axis('off')
        axes[5].text(0.1, 0.5,
            '调制阶数对比\n\n'
            '  BPSK:  1 bit/sym  最鲁棒\n'
            '  QPSK:  2 bit/sym\n'
            '  16QAM: 4 bit/sym\n'
            '  64QAM: 6 bit/sym\n'
            ' 256QAM: 8 bit/sym  最高效\n\n'
            '应用: 5G NR, LTE, Wi-Fi\n'
            '(自适应调制编码 AMC)',
            transform=axes[5].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))

    def _plot_msk(self, axes, bits, fc, fs, rb, snr_db):
        n_bits = min(len(bits), 64)
        s_tx, t = msk_mod(bits[:n_bits], fc, fs, rb)

        sig_power = np.mean(s_tx ** 2) + 1e-12
        noise_power = sig_power / (10 ** (snr_db / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), len(s_tx))
        s_rx = s_tx + noise

        sps = max(1, int(fs / rb))
        show = min(len(t), 12 * sps)

        axes[0].plot(t[:show], s_tx[:show], color=COLORS[0], lw=1.0)
        axes[0].set_title('MSK 调制波形（连续相位）')
        axes[0].set_xlabel('时间 (s)'); axes[0].set_ylabel('幅度')
        axes[0].grid(True, alpha=0.3)

        axes[1].plot(t[:show], s_rx[:show], color=COLORS[3], lw=0.8)
        axes[1].set_title(f'MSK 信道输出 (SNR={snr_db}dB)')
        axes[1].set_xlabel('时间 (s)'); axes[1].set_ylabel('幅度')
        axes[1].grid(True, alpha=0.3)

        # Instantaneous frequency
        analytic = hilbert(s_tx)
        inst_phase = np.unwrap(np.angle(analytic))
        inst_freq = np.diff(inst_phase) / (2 * np.pi) * fs
        axes[2].plot(t[1:show], inst_freq[:show - 1], color=COLORS[2], lw=1.2)
        f0 = fc
        f1 = fc + rb / 2
        axes[2].axhline(f0, color=COLORS[4], ls='--', lw=0.8, label=f'f0={f0:.0f}Hz')
        axes[2].axhline(f1, color=COLORS[1], ls='--', lw=0.8, label=f'f1={f1:.0f}Hz')
        axes[2].set_title('MSK 瞬时频率（体现连续相位）')
        axes[2].set_xlabel('时间 (s)'); axes[2].set_ylabel('频率 (Hz)')
        axes[2].legend(fontsize=8); axes[2].grid(True, alpha=0.3)

        # Phase trajectory
        phase_mod = inst_phase[:show] % (2 * np.pi)
        axes[3].plot(t[:show], inst_phase[:show] / np.pi, color=COLORS[0], lw=1.2)
        axes[3].set_title('MSK 相位轨迹（线性增加）')
        axes[3].set_xlabel('时间 (s)'); axes[3].set_ylabel('相位 (×π rad)')
        axes[3].grid(True, alpha=0.3)

        # Spectrum comparison: MSK vs BPSK
        from scipy.signal import welch
        f_msk, p_msk = welch(s_tx, fs=fs, nperseg=min(1024, len(s_tx)))
        axes[4].semilogy(f_msk - fc, p_msk + 1e-15, color=COLORS[0], lw=1.5, label='MSK')
        axes[4].set_title('MSK 功率谱（相对于载波）')
        axes[4].set_xlabel('(f-fc)/Rb'); axes[4].set_ylabel('PSD')
        axes[4].set_xlim(-3 * rb, 3 * rb)
        axes[4].legend(); axes[4].grid(True, alpha=0.3, which='both')

        axes[5].axis('off')
        axes[5].text(0.1, 0.5,
            'MSK 最小频移键控\n\n'
            'h = 0.5 (最小频移)\n\n'
            '特点:\n'
            '  ✓ 连续相位 (CPFSK)\n'
            '  ✓ 恒定包络\n'
            '  ✓ 带外衰减快\n'
            '  ✓ 频谱效率较高\n\n'
            f'  f0 = {fc:.0f} Hz (发"0")\n'
            f'  f1 = {fc+rb/2:.0f} Hz (发"1")\n'
            f'  Δf = Rb/2 = {rb/2:.1f} Hz',
            transform=axes[5].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))

    def _plot_ber(self):
        from scipy.special import erfc
        snr = np.linspace(0, 20, 100)
        snr_lin = 10 ** (snr / 10)

        ber_bpsk = 0.5 * erfc(np.sqrt(snr_lin))
        ber_qpsk = 0.5 * erfc(np.sqrt(snr_lin))  # Same as BPSK per bit
        ber_16qam = (3/4) * erfc(np.sqrt(snr_lin * 2 / 5))
        ber_msk = 0.5 * erfc(np.sqrt(snr_lin / 2))  # approx

        self.canvas.clear_axes()
        axes = self.canvas.axes

        ax = axes[0]
        ax.semilogy(snr, ber_bpsk, color=COLORS[0], lw=2, label='BPSK/QPSK')
        ax.semilogy(snr, ber_16qam, color=COLORS[1], lw=2, label='16QAM')
        ax.semilogy(snr, ber_msk, color=COLORS[2], lw=2, label='MSK')
        ax.set_title('高阶调制 BER vs Eb/N0')
        ax.set_xlabel('Eb/N0 (dB)'); ax.set_ylabel('BER')
        ax.set_xlim(0, 20); ax.set_ylim(1e-6, 1)
        ax.legend(); ax.grid(True, alpha=0.3, which='both')

        # Spectral efficiency
        mods = ['BPSK', 'QPSK', '8PSK', '16QAM', '64QAM', '256QAM']
        eff = [1, 2, 3, 4, 6, 8]
        req_snr = [9.6, 9.6, 14.0, 17.0, 23.5, 29.0]  # dBfor BER=1e-3
        ax2 = axes[1]
        bars = ax2.bar(mods, eff, color=COLORS[:6], alpha=0.8)
        ax2.set_title('频谱效率 (bit/s/Hz)')
        ax2.set_xlabel('调制方式'); ax2.set_ylabel('频谱效率 (bit/s/Hz)')
        ax2.grid(True, alpha=0.3, axis='y')
        for bar, e in zip(bars, eff):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                     str(e), ha='center', va='bottom', fontsize=9, color='#cfd8dc')

        ax3 = axes[2]
        ax3.plot(eff, req_snr, 'o-', color=COLORS[0], lw=2, ms=8)
        for i, (e, s, m) in enumerate(zip(eff, req_snr, mods)):
            ax3.annotate(m, (e, s), textcoords='offset points', xytext=(5, 3), fontsize=8, color='#90a4ae')
        ax3.set_title('频谱效率 vs 所需SNR (BER=10⁻³)')
        ax3.set_xlabel('频谱效率 (bit/s/Hz)'); ax3.set_ylabel('Eb/N0 (dB)')
        ax3.grid(True, alpha=0.3)

        for i in range(3, 6):
            axes[i].axis('off')
        axes[3].text(0.1, 0.5,
            '调制阶数与系统性能权衡\n\n'
            '调制阶数越高:\n'
            '  ✓ 频谱效率越高\n'
            '  ✗ 需要更高 SNR\n'
            '  ✗ 对相位噪声更敏感\n\n'
            '5G NR 最高支持 256QAM\n'
            '需要极好的信道质量\n'
            '(MCS 28/29)',
            transform=axes[3].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        self.canvas.fig.tight_layout(pad=1.5)
        self.canvas.draw()
