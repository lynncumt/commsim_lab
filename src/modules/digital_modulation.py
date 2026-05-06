"""实验5: 数字频带调制 — 2ASK, 2FSK, 2PSK, 2DPSK (相干/非相干解调)"""
import numpy as np
from scipy.signal import butter, filtfilt, hilbert
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox
from src.ui.base_module import BaseModuleWidget, COLORS


def _lpf(signal, cutoff, fs, order=5):
    nyq = fs / 2
    b, a = butter(order, min(cutoff / nyq, 0.99), btype='low')
    return filtfilt(b, a, signal)


def _bpf(signal, fc, bw, fs, order=4):
    nyq = fs / 2
    lo = max(0.001, (fc - bw / 2) / nyq)
    hi = min(0.999, (fc + bw / 2) / nyq)
    b, a = butter(order, [lo, hi], btype='band')
    return filtfilt(b, a, signal)


def _ber_2ask_theory(snr_db):
    snr = 10 ** (snr_db / 10)
    from scipy.special import erfc
    return 0.5 * erfc(np.sqrt(snr / 4))


def _ber_2psk_theory(snr_db):
    snr = 10 ** (snr_db / 10)
    from scipy.special import erfc
    return 0.5 * erfc(np.sqrt(snr))


def _ber_2fsk_theory(snr_db, coherent=True):
    snr = 10 ** (snr_db / 10)
    from scipy.special import erfc
    if coherent:
        return 0.5 * erfc(np.sqrt(snr / 2))
    else:
        return 0.5 * np.exp(-snr / 2)


class DigitalModulationWidget(BaseModuleWidget):
    def __init__(self, user, parent=None):
        super().__init__(user, rows=3, cols=2, figsize=(11, 8), parent=parent)
        self._build_controls()
        self._run()

    def _build_controls(self):
        self.add_section_title('📶  数字调制参数')

        self._mod = QComboBox()
        self._mod.addItems(['2ASK', '2FSK', '2PSK', '2DPSK', 'BER曲线对比'])
        self.add_param_row('调制方式', self._mod)

        self._rb = QDoubleSpinBox()
        self._rb.setRange(1.0, 500.0)
        self._rb.setValue(10.0)
        self._rb.setSuffix(' bps')
        self.add_param_row('码元速率 Rb', self._rb)

        self._fc = QDoubleSpinBox()
        self._fc.setRange(10.0, 2000.0)
        self._fc.setValue(100.0)
        self._fc.setSuffix(' Hz')
        self.add_param_row('载波频率 fc', self._fc)

        self._f1 = QDoubleSpinBox()
        self._f1.setRange(10.0, 2000.0)
        self._f1.setValue(120.0)
        self._f1.setSuffix(' Hz')
        self.add_param_row('2FSK f1 (发"1")', self._f1)

        self._n_bits = QSpinBox()
        self._n_bits.setRange(16, 512)
        self._n_bits.setValue(64)
        self.add_param_row('比特数', self._n_bits)

        self._snr = QDoubleSpinBox()
        self._snr.setRange(-5, 30)
        self._snr.setValue(12.0)
        self._snr.setSuffix(' dB')
        self.add_param_row('信道SNR (Eb/N0)', self._snr)

        self._coherent = QCheckBox('相干解调')
        self._coherent.setChecked(True)
        self._coherent.setStyleSheet('color:#90a4ae;')
        self.ctrl_layout.addWidget(self._coherent)

        self.add_spacer()
        self.add_run_button(callback=self._run)
        self.add_stretch()

    def _run(self):
        mod_idx = self._mod.currentIndex()
        if mod_idx == 4:
            self._plot_ber_curves()
            return

        rb = self._rb.value()
        fc = self._fc.value()
        f1 = self._f1.value()
        n_bits = self._n_bits.value()
        snr_db = self._snr.value()
        coherent = self._coherent.isChecked()

        fs = max(fc * 20, rb * 40)
        sps = int(fs / rb)
        t_bit = 1.0 / rb
        bits = np.random.randint(0, 2, n_bits)
        t = np.arange(n_bits * sps) / fs

        mod_names = ['2ASK', '2FSK', '2PSK', '2DPSK']
        name = mod_names[mod_idx]

        # ── Modulation ────────────────────────────────────────────────────
        if mod_idx == 0:  # 2ASK
            env = np.repeat(bits.astype(float), sps)
            s_tx = env * np.cos(2 * np.pi * fc * t)

        elif mod_idx == 1:  # 2FSK
            f0 = fc  # frequency for '0'
            phase = 0.0
            s_tx = np.zeros(n_bits * sps)
            for i, b in enumerate(bits):
                fi = f1 if b == 1 else f0
                ti = np.arange(sps) / fs
                seg = np.cos(2 * np.pi * fi * ti + phase)
                s_tx[i * sps:(i + 1) * sps] = seg
                phase += 2 * np.pi * fi * sps / fs

        elif mod_idx == 2:  # 2PSK
            phase_bits = np.where(bits == 0, 0, np.pi)
            phase_seq = np.repeat(phase_bits, sps)
            s_tx = np.cos(2 * np.pi * fc * t + phase_seq)

        else:  # 2DPSK
            # Differential encoding
            d_bits = np.zeros(n_bits + 1, dtype=int)
            d_bits[0] = 0  # reference
            for i in range(n_bits):
                d_bits[i + 1] = d_bits[i] ^ bits[i]
            phase_bits = np.where(d_bits[1:] == 0, 0, np.pi)
            phase_seq = np.repeat(phase_bits, sps)
            s_tx = np.cos(2 * np.pi * fc * t + phase_seq)

        # ── Channel AWGN ──────────────────────────────────────────────────
        sig_power = np.mean(s_tx ** 2)
        noise_power = sig_power / (10 ** (snr_db / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), len(s_tx))
        s_rx = s_tx + noise

        # ── Demodulation ──────────────────────────────────────────────────
        if mod_idx == 0:  # 2ASK
            if coherent:
                demod = s_rx * np.cos(2 * np.pi * fc * t)
                demod = _lpf(demod, rb * 2, fs)
            else:
                demod = np.abs(hilbert(s_rx))
                demod = _lpf(demod, rb * 2, fs)
            # Decision
            rx_bits = np.array([1 if np.mean(demod[i*sps:(i+1)*sps]) > 0.25 else 0
                                 for i in range(n_bits)])

        elif mod_idx == 1:  # 2FSK
            if coherent:
                d0 = _lpf(s_rx * np.cos(2 * np.pi * fc * t), rb * 2, fs)
                d1 = _lpf(s_rx * np.cos(2 * np.pi * f1 * t), rb * 2, fs)
            else:
                d0 = np.abs(hilbert(_bpf(s_rx, fc, rb * 2, fs)))
                d1 = np.abs(hilbert(_bpf(s_rx, f1, rb * 2, fs)))
            rx_bits = np.array([1 if np.mean(d1[i*sps:(i+1)*sps]) > np.mean(d0[i*sps:(i+1)*sps]) else 0
                                 for i in range(n_bits)])
            demod = d1 - d0

        elif mod_idx == 2:  # 2PSK
            demod = _lpf(s_rx * np.cos(2 * np.pi * fc * t), rb * 2, fs)
            rx_bits = np.array([1 if np.mean(demod[i*sps:(i+1)*sps]) < 0 else 0
                                 for i in range(n_bits)])

        else:  # 2DPSK
            demod = _lpf(s_rx * np.cos(2 * np.pi * fc * t), rb * 2, fs)
            d_rx = np.array([1 if np.mean(demod[i*sps:(i+1)*sps]) < 0 else 0
                              for i in range(n_bits)])
            # Differential decoding
            rx_bits = np.zeros(n_bits, dtype=int)
            for i in range(1, n_bits):
                rx_bits[i] = d_rx[i] ^ d_rx[i - 1]

        # ── BER calculation ───────────────────────────────────────────────
        n_compare = min(len(bits), len(rx_bits))
        ber_sim = np.sum(bits[:n_compare] != rx_bits[:n_compare]) / n_compare

        # ── Plots ──────────────────────────────────────────────────────────
        self.canvas.clear_axes()
        axes = self.canvas.axes
        show = min(n_bits * sps, int(8 * sps))

        axes[0].step(np.arange(show), np.repeat(bits, sps)[:show],
                     where='post', color=COLORS[0], lw=1.5, label='发送比特')
        axes[0].set_title('发送基带信号')
        axes[0].set_xlabel('样本序号'); axes[0].set_ylabel('电平')
        axes[0].set_ylim(-0.2, 1.3); axes[0].legend(); axes[0].grid(True, alpha=0.3)

        axes[1].plot(t[:show], s_tx[:show], color=COLORS[1], lw=1.0, label=f'{name} 已调信号')
        axes[1].set_title(f'{name} 调制波形')
        axes[1].set_xlabel('时间 (s)'); axes[1].set_ylabel('幅度')
        axes[1].legend(); axes[1].grid(True, alpha=0.3)

        axes[2].plot(t[:show], s_rx[:show], color=COLORS[3], lw=0.8, label=f'信道输出 (SNR={snr_db}dB)')
        axes[2].set_title('信道输出（含AWGN）')
        axes[2].set_xlabel('时间 (s)'); axes[2].set_ylabel('幅度')
        axes[2].legend(); axes[2].grid(True, alpha=0.3)

        axes[3].plot(t[:show], demod[:show], color=COLORS[2], lw=1.2, label='解调输出')
        axes[3].step(np.arange(show), np.repeat(rx_bits, sps)[:show],
                     where='post', color=COLORS[4], lw=1.5, alpha=0.7, label='判决输出')
        axes[3].set_title(f'解调信号（{"相干" if coherent else "非相干"}）')
        axes[3].set_xlabel('样本序号'); axes[3].set_ylabel('幅度')
        axes[3].legend(); axes[3].grid(True, alpha=0.3)

        # Bit comparison
        errors = bits[:n_compare] != rx_bits[:n_compare]
        axes[4].step(range(n_compare), bits[:n_compare], where='post', color=COLORS[0], lw=1.5, label='发送')
        axes[4].step(range(n_compare), rx_bits[:n_compare] + 1.5, where='post', color=COLORS[1], lw=1.5, label='接收')
        err_pos = np.where(errors)[0]
        if len(err_pos) > 0:
            axes[4].scatter(err_pos, np.ones(len(err_pos)) * 2.8, marker='x',
                            color='red', s=50, zorder=5, label=f'错误 ({len(err_pos)})')
        axes[4].set_title('发送/接收比特流对比')
        axes[4].set_xlabel('比特序号'); axes[4].set_ylabel('电平')
        axes[4].legend(fontsize=8); axes[4].grid(True, alpha=0.3)

        # Info panel
        axes[5].axis('off')
        demod_method = '相干' if coherent else '非相干'
        axes[5].text(0.1, 0.5,
            f'{name} 仿真结果\n\n'
            f'解调方式: {demod_method}\n'
            f'码元速率 Rb = {rb} bps\n'
            f'载波频率 fc = {fc} Hz\n'
            f'信道SNR = {snr_db} dB\n'
            f'发送比特数: {n_bits}\n'
            f'误码数: {np.sum(errors)}\n'
            f'仿真误码率: {ber_sim:.4f}\n\n'
            f'理论误码率:\n'
            f'  {self._theory_ber_str(mod_idx, snr_db, coherent)}',
            transform=axes[5].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        self.canvas.fig.tight_layout(pad=1.5)
        self.canvas.draw()

    def _theory_ber_str(self, mod_idx, snr_db, coherent):
        snr_vals = np.array([snr_db])
        if mod_idx == 0:
            ber = _ber_2ask_theory(snr_db)
        elif mod_idx == 1:
            ber = _ber_2fsk_theory(snr_db, coherent)
        elif mod_idx in (2, 3):
            ber = _ber_2psk_theory(snr_db)
        else:
            ber = _ber_2psk_theory(snr_db)
        return f'Pe ≈ {ber:.4e}'

    def _plot_ber_curves(self):
        snr_range = np.linspace(0, 20, 80)

        self.canvas.clear_axes()
        axes = self.canvas.axes

        # Theoretical BER curves
        ber_ask = [_ber_2ask_theory(s) for s in snr_range]
        ber_fsk_coh = [_ber_2fsk_theory(s, True) for s in snr_range]
        ber_fsk_ncoh = [_ber_2fsk_theory(s, False) for s in snr_range]
        ber_psk = [_ber_2psk_theory(s) for s in snr_range]

        ax = axes[0]
        ax.semilogy(snr_range, ber_ask, color=COLORS[0], lw=2, label='2ASK')
        ax.semilogy(snr_range, ber_fsk_coh, color=COLORS[1], lw=2, label='2FSK (相干)')
        ax.semilogy(snr_range, ber_fsk_ncoh, color=COLORS[1], lw=2, ls='--', label='2FSK (非相干)')
        ax.semilogy(snr_range, ber_psk, color=COLORS[2], lw=2, label='2PSK/2DPSK')
        ax.set_title('各调制方式 BER vs Eb/N0 (理论曲线)')
        ax.set_xlabel('Eb/N0 (dB)'); ax.set_ylabel('误码率 BER')
        ax.set_xlim(0, 20); ax.set_ylim(1e-6, 1)
        ax.legend(); ax.grid(True, alpha=0.3, which='both')

        # Monte Carlo simulation BER
        snr_sim = np.arange(0, 20, 2)
        n_bits_sim = 500
        rb = self._rb.value()
        fc = self._fc.value()

        def sim_ber(mod, snr_db):
            fs = max(fc * 20, rb * 40)
            sps = int(fs / rb)
            bits = np.random.randint(0, 2, n_bits_sim)
            t = np.arange(n_bits_sim * sps) / fs
            if mod == '2psk':
                phase = np.where(bits == 0, 0.0, np.pi)
                s_tx = np.cos(2 * np.pi * fc * t + np.repeat(phase, sps))
            else:
                env = np.repeat(bits.astype(float), sps)
                s_tx = env * np.cos(2 * np.pi * fc * t)
            sig_power = np.mean(s_tx ** 2) + 1e-9
            noise = np.random.normal(0, np.sqrt(sig_power / (10 ** (snr_db / 10))), len(s_tx))
            s_rx = s_tx + noise
            demod = _lpf(s_rx * np.cos(2 * np.pi * fc * t), rb * 2, fs)
            if mod == '2psk':
                rx = np.array([1 if np.mean(demod[i*sps:(i+1)*sps]) < 0 else 0 for i in range(n_bits_sim)])
            else:
                rx = np.array([1 if np.mean(demod[i*sps:(i+1)*sps]) > 0.25 else 0 for i in range(n_bits_sim)])
            return np.sum(bits != rx) / n_bits_sim

        ber_ask_sim = [sim_ber('2ask', s) for s in snr_sim]
        ber_psk_sim = [sim_ber('2psk', s) for s in snr_sim]

        axes[1].semilogy(snr_range, ber_ask, color=COLORS[0], lw=1.5, label='2ASK 理论')
        axes[1].semilogy(snr_sim, [max(b, 1e-6) for b in ber_ask_sim], 'o', color=COLORS[0], ms=6, label='2ASK 仿真')
        axes[1].semilogy(snr_range, ber_psk, color=COLORS[2], lw=1.5, label='2PSK 理论')
        axes[1].semilogy(snr_sim, [max(b, 1e-6) for b in ber_psk_sim], 's', color=COLORS[2], ms=6, label='2PSK 仿真')
        axes[1].set_title('理论 vs 仿真 BER 对比')
        axes[1].set_xlabel('Eb/N0 (dB)'); axes[1].set_ylabel('BER')
        axes[1].set_xlim(0, 18); axes[1].set_ylim(1e-5, 1)
        axes[1].legend(fontsize=8); axes[1].grid(True, alpha=0.3, which='both')

        # SNR gain: PSK over ASK
        gain = np.array(snr_range) - np.array([snr_range[np.argmin(np.abs(np.array(ber_ask) - b))]
                                                 if b > 0 else 0 for b in ber_psk])

        axes[2].axis('off')
        axes[2].text(0.1, 0.5,
            '调制方式抗噪声性能比较\n\n'
            '相同BER=10⁻³所需 Eb/N0:\n\n'
            f'  2ASK:       ≈ 13.5 dB\n'
            f'  2FSK(相干): ≈ 12.5 dB\n'
            f'  2FSK(非相干):≈ 13.0 dB\n'
            f'  2PSK:       ≈  7.0 dB\n'
            f'  2DPSK:      ≈  8.0 dB\n\n'
            '结论:\n'
            '  2PSK 抗噪声性能最佳\n'
            '  比 2ASK 好约 6 dB',
            transform=axes[2].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        axes[3].axis('off')
        axes[3].text(0.1, 0.5,
            '解调方式影响\n\n'
            '相干解调 vs 非相干解调:\n\n'
            '  相干解调需要载波同步\n'
            '  性能好, 复杂度高\n\n'
            '  非相干解调无需载波同步\n'
            '  性能稍差, 实现简单\n\n'
            '2FSK非相干比相干:\n'
            '  约差 0.5~1 dB',
            transform=axes[3].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))

        for i in range(4, 6):
            axes[i].axis('off')

        self.canvas.fig.tight_layout(pad=1.5)
        self.canvas.draw()
