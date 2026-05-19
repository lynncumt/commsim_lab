"""现代通信系统 — OFDM, MIMO, 跳频, DVB-T"""
import numpy as np
from scipy.signal import butter, filtfilt, welch
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox
from src.ui.base_module import BaseModuleWidget, COLORS


# ── OFDM ──────────────────────────────────────────────────────────────────────
def ofdm_modulate(bits, n_subcarriers=64, cp_len=16, mod='QPSK'):
    """OFDM modulation. Returns: (tx_signal, symbols)"""
    bits_per_sym = 2 if mod == 'QPSK' else 4  # 16QAM
    n_data_sc = n_subcarriers - 2  # exclude DC and guard
    bits_per_ofdm = n_data_sc * bits_per_sym

    n_ofdm = len(bits) // bits_per_ofdm
    if n_ofdm == 0:
        n_ofdm = 1
        bits = np.pad(bits, (0, bits_per_ofdm - len(bits) % bits_per_ofdm))

    tx_signal = []
    all_symbols = []

    for frame in range(n_ofdm):
        b = bits[frame * bits_per_ofdm:(frame + 1) * bits_per_ofdm]
        if len(b) < bits_per_ofdm:
            b = np.pad(b, (0, bits_per_ofdm - len(b)))

        # Map bits to symbols
        if mod == 'QPSK':
            i_bits = b[0::2]
            q_bits = b[1::2]
            syms = (i_bits * 2 - 1 + 1j * (q_bits * 2 - 1)) / np.sqrt(2)
        else:  # 16QAM
            chunks = b[:n_data_sc * 4].reshape(-1, 4)
            levels = {(0,0):-3, (0,1):-1, (1,1):1, (1,0):3}
            syms = np.array([(levels.get(tuple(c[:2]), 0) + 1j * levels.get(tuple(c[2:]), 0)) / (3 * np.sqrt(2))
                              for c in chunks])

        all_symbols.extend(syms)

        # Map to subcarriers (skip DC at index 0)
        freq_domain = np.zeros(n_subcarriers, dtype=complex)
        freq_domain[1:n_data_sc + 1] = syms[:n_data_sc]

        # IFFT
        time_domain = np.fft.ifft(freq_domain) * np.sqrt(n_subcarriers)

        # Add cyclic prefix
        cp = time_domain[-cp_len:]
        ofdm_sym = np.concatenate([cp, time_domain])
        tx_signal.extend(ofdm_sym)

    return np.array(tx_signal), np.array(all_symbols)


def ofdm_demodulate(rx_signal, n_subcarriers=64, cp_len=16, n_frames=1):
    """OFDM demodulation."""
    sym_len = n_subcarriers + cp_len
    rx_symbols = []
    for i in range(n_frames):
        start = i * sym_len
        ofdm_sym = rx_signal[start:start + sym_len]
        if len(ofdm_sym) < sym_len:
            break
        # Remove CP
        time_domain = ofdm_sym[cp_len:]
        # FFT
        freq_domain = np.fft.fft(time_domain) / np.sqrt(n_subcarriers)
        rx_symbols.extend(freq_domain[1:n_subcarriers - 1])
    return np.array(rx_symbols)


# ── MIMO ──────────────────────────────────────────────────────────────────────
def mimo_simulate(n_tx, n_rx, n_bits, snr_db):
    """Simple MIMO with Alamouti STBC (2Tx, nRx) or spatial multiplexing."""
    bits = np.random.randint(0, 2, n_bits)
    # BPSK modulation
    syms = bits * 2.0 - 1.0
    # Channel matrix H (n_rx × n_tx Rayleigh)
    H = (np.random.randn(n_rx, n_tx) + 1j * np.random.randn(n_rx, n_tx)) / np.sqrt(2)
    # Noise
    snr_lin = 10 ** (snr_db / 10)
    sigma = np.sqrt(1 / (2 * snr_lin))

    if n_tx == 2 and n_rx >= 1:
        # Alamouti STBC: transmit pairs
        n_pairs = len(syms) // 2
        decoded = np.zeros(2 * n_pairs)
        for i in range(n_pairs):
            s1, s2 = syms[2*i], syms[2*i+1]
            # Time slot 1: [s1, s2] from ant1, ant2
            r1 = H[0, 0] * s1 + H[0, 1] * s2 + \
                 (np.random.randn() + 1j * np.random.randn()) * sigma
            # Time slot 2: [-s2*, s1*] from ant1, ant2
            r2 = H[0, 0] * (-s2) + H[0, 1] * s1.conjugate() + \
                 (np.random.randn() + 1j * np.random.randn()) * sigma
            # Alamouti combiner
            h1, h2 = H[0, 0], H[0, 1]
            s1_hat = np.real(h1.conj() * r1 + h2 * r2.conj())
            s2_hat = np.real(h2.conj() * r1 - h1 * r2.conj())
            decoded[2*i] = 1 if s1_hat > 0 else 0
            decoded[2*i+1] = 1 if s2_hat > 0 else 0
        ber = np.mean(bits[:2*n_pairs] != decoded)
    else:
        # MRC receive diversity
        rx_combined = np.zeros(len(syms))
        for nr in range(n_rx):
            noise = np.random.randn(len(syms)) * sigma
            h = np.abs(H[nr, 0])
            rx_combined += h * syms + noise
        decoded = (rx_combined > 0).astype(int)
        ber = np.mean(bits != decoded)

    return bits, decoded, ber, H


class ModernSystemsWidget(BaseModuleWidget):
    def __init__(self, user, parent=None):
        super().__init__(user, rows=3, cols=2, figsize=(11, 8), parent=parent)
        self._build_controls()
        self._run()

    def _build_controls(self):
        self.add_section_title('🌐  现代通信系统')

        self._mode = QComboBox()
        self._mode.addItems(['OFDM 系统', 'MIMO 系统', '跳频通信 FHSS', 'OFDM信道估计', 'DVB-T 链路'])
        self.add_param_row('仿真系统', self._mode)

        self._n_sc = QComboBox()
        self._n_sc.addItems(['16', '32', '64', '128', '256'])
        self._n_sc.setCurrentIndex(2)
        self.add_param_row('OFDM子载波数', self._n_sc)

        self._cp_ratio = QComboBox()
        self._cp_ratio.addItems(['1/4 (常用)', '1/8', '1/16', '1/32'])
        self.add_param_row('循环前缀比例', self._cp_ratio)

        self._mimo_tx = QSpinBox()
        self._mimo_tx.setRange(1, 4)
        self._mimo_tx.setValue(2)
        self.add_param_row('MIMO 发射天线', self._mimo_tx)

        self._mimo_rx = QSpinBox()
        self._mimo_rx.setRange(1, 4)
        self._mimo_rx.setValue(2)
        self.add_param_row('MIMO 接收天线', self._mimo_rx)

        self._n_bits = QSpinBox()
        self._n_bits.setRange(64, 4096)
        self._n_bits.setValue(1024)
        self.add_param_row('比特数', self._n_bits)

        self._snr = QDoubleSpinBox()
        self._snr.setRange(-5, 30)
        self._snr.setValue(15.0)
        self._snr.setSuffix(' dB')
        self.add_param_row('信道 SNR', self._snr)

        self._multipath = QCheckBox('多径信道')
        self._multipath.setChecked(True)
        self._multipath.setStyleSheet('color:#90a4ae;')
        self.ctrl_layout.addWidget(self._multipath)

        self.add_spacer()
        self.add_run_button(callback=self._run)
        self.add_stretch()

    def _run(self):
        mode = self._mode.currentIndex()
        n_sc = int(self._n_sc.currentText())
        cp_ratios = [0.25, 0.125, 0.0625, 0.03125]
        cp_len = max(1, int(n_sc * cp_ratios[self._cp_ratio.currentIndex()]))
        n_bits = self._n_bits.value()
        snr_db = self._snr.value()
        n_tx = self._mimo_tx.value()
        n_rx = self._mimo_rx.value()

        self.canvas.clear_axes()
        axes = self.canvas.axes

        if mode == 0:
            self._plot_ofdm(axes, n_bits, n_sc, cp_len, snr_db)
        elif mode == 1:
            self._plot_mimo(axes, n_tx, n_rx, n_bits, snr_db)
        elif mode == 2:
            self._plot_fhss(axes, n_bits, snr_db)
        elif mode == 3:
            self._plot_ofdm_channel_estimation(axes, n_bits, n_sc, cp_len, snr_db)
        else:
            self._plot_dvbt(axes, snr_db)

        self.canvas.fig.tight_layout(pad=1.5)
        self.canvas.draw()

    def _plot_ofdm(self, axes, n_bits, n_sc, cp_len, snr_db):
        bits = np.random.randint(0, 2, n_bits)
        tx_signal, tx_syms = ofdm_modulate(bits, n_sc, cp_len)

        # AWGN channel
        snr_lin = 10 ** (snr_db / 10)
        sig_power = np.mean(np.abs(tx_signal) ** 2) + 1e-12
        noise = (np.random.randn(len(tx_signal)) + 1j * np.random.randn(len(tx_signal))) * \
                np.sqrt(sig_power / (2 * snr_lin))

        if self._multipath.isChecked():
            # Simple 3-tap multipath channel
            h_ch = np.array([1.0, 0.3 * np.exp(1j * 0.5), 0.15 * np.exp(-1j * 0.8)])
            rx_signal = np.convolve(tx_signal, h_ch)[:len(tx_signal)]
        else:
            rx_signal = tx_signal.copy()

        rx_signal += noise

        # Demodulate
        n_frames = len(tx_signal) // (n_sc + cp_len)
        rx_syms = ofdm_demodulate(rx_signal, n_sc, cp_len, n_frames)

        # Time domain waveform
        show = min(len(tx_signal), 4 * (n_sc + cp_len))
        t = np.arange(show)
        axes[0].plot(t, np.real(tx_signal[:show]), color=COLORS[0], lw=1.0)
        axes[0].set_title(f'OFDM 时域信号 (Nsc={n_sc}, CP={cp_len})')
        axes[0].set_xlabel('样本序号'); axes[0].set_ylabel('实部')
        axes[0].grid(True, alpha=0.3)

        # Highlight CP regions
        sym_len = n_sc + cp_len
        for i in range(show // sym_len):
            axes[0].axvspan(i * sym_len, i * sym_len + cp_len, alpha=0.2, color=COLORS[3], label='CP' if i == 0 else '')
        axes[0].legend(fontsize=8)

        # Spectrum
        f, p = welch(np.real(tx_signal), nperseg=min(n_sc * 4, len(tx_signal)))
        axes[1].plot(f, 10 * np.log10(p + 1e-15), color=COLORS[2], lw=1.5)
        axes[1].set_title('OFDM 功率谱（多子载波叠加）')
        axes[1].set_xlabel('归一化频率'); axes[1].set_ylabel('PSD (dB)')
        axes[1].grid(True, alpha=0.3)

        # Received constellation
        n_show = min(len(rx_syms), 500)
        axes[2].scatter(np.real(rx_syms[:n_show]), np.imag(rx_syms[:n_show]),
                        s=5, color=COLORS[1], alpha=0.5)
        axes[2].axhline(0, color='#2a3a5a', lw=0.8)
        axes[2].axvline(0, color='#2a3a5a', lw=0.8)
        axes[2].set_title(f'接收星座图 (SNR={snr_db}dB, {"多径" if self._multipath.isChecked() else "AWGN"})')
        axes[2].set_xlabel('I'); axes[2].set_ylabel('Q')
        axes[2].set_aspect('equal'); axes[2].grid(True, alpha=0.3)

        # PAPR analysis
        papr_db = 10 * np.log10(np.max(np.abs(tx_signal) ** 2) / sig_power)
        # CCDF
        powers = np.abs(tx_signal) ** 2
        power_avg = np.mean(powers)
        papr_vals = powers / power_avg
        papr_db_vals = 10 * np.log10(papr_vals + 1e-15)
        ccdf_x = np.linspace(0, 15, 100)
        ccdf_y = [np.mean(papr_db_vals > x) for x in ccdf_x]
        axes[3].semilogy(ccdf_x, [max(y, 1e-5) for y in ccdf_y], color=COLORS[0], lw=2)
        axes[3].set_title('OFDM PAPR 的 CCDF')
        axes[3].set_xlabel('PAPR (dB)'); axes[3].set_ylabel('Pr(PAPR > x)')
        axes[3].grid(True, alpha=0.3, which='both')

        axes[4].axis('off')
        axes[4].text(0.1, 0.5,
            f'OFDM 系统参数\n\n'
            f'子载波数: Nsc = {n_sc}\n'
            f'有效子载波: {n_sc - 2}\n'
            f'循环前缀: CP = {cp_len}\n'
            f'OFDM符号长: {n_sc + cp_len}\n'
            f'CP比例: {cp_len/n_sc:.3f}\n\n'
            f'信道: {"多径+AWGN" if self._multipath.isChecked() else "AWGN"}\n'
            f'SNR = {snr_db} dB\n\n'
            f'PAPR = {papr_db:.1f} dB\n'
            f'(PAPR是OFDM主要缺点)',
            transform=axes[4].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        axes[5].axis('off')
        axes[5].text(0.1, 0.5,
            'OFDM 关键技术\n\n'
            '✓ 子载波正交性(IDFT/DFT)\n'
            '✓ 循环前缀消除ISI\n'
            '✓ 频域均衡只需单抽头\n\n'
            '应用: LTE/5G, Wi-Fi,\n'
            '      DVB-T, ADSL\n\n'
            'CP条件: TCP ≥ 最大时延扩展\n'
            f'  当前: CP={cp_len} 样本',
            transform=axes[5].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))

    def _plot_mimo(self, axes, n_tx, n_rx, n_bits, snr_db):
        bits, decoded, ber_stbc, H = mimo_simulate(n_tx, n_rx, n_bits, snr_db)
        n = min(len(bits), len(decoded))

        # Channel matrix visualization
        H_mag = np.abs(H)
        im = axes[0].imshow(H_mag, cmap='hot', aspect='auto')
        self.canvas.fig.colorbar(im, ax=axes[0])
        axes[0].set_title(f'MIMO 信道矩阵 |H| ({n_rx}×{n_tx})')
        axes[0].set_xlabel('发射天线'); axes[0].set_ylabel('接收天线')
        axes[0].set_xticks(range(n_tx))
        axes[0].set_yticks(range(n_rx))

        # Bit comparison
        show = min(64, n)
        axes[1].step(range(show), bits[:show], where='post', color=COLORS[0], lw=1.5, label='发送')
        axes[1].step(range(show), decoded[:show] + 1.5, where='post', color=COLORS[2], lw=1.5, label='接收')
        axes[1].set_title(f'MIMO 收发比特 (BER={ber_stbc:.4f})')
        axes[1].set_xlabel('比特序号'); axes[1].set_ylabel('电平')
        axes[1].legend(); axes[1].grid(True, alpha=0.3)

        # BER vs SNR for different MIMO configs
        snr_range = np.arange(0, 20, 2)
        configs = [(1, 1, 'SISO'), (1, 2, 'SIMO 1×2'), (2, 1, 'MISO 2×1'), (2, 2, 'MIMO 2×2')]
        for cfg_tx, cfg_rx, name in configs:
            bers = []
            for s in snr_range:
                _, _, ber_cfg, _ = mimo_simulate(cfg_tx, cfg_rx, 500, s)
                bers.append(max(ber_cfg, 1e-6))
            axes[2].semilogy(snr_range, bers, 'o-', lw=1.5,
                             label=name, color=COLORS[configs.index((cfg_tx, cfg_rx, name))])

        axes[2].set_title('不同MIMO配置 BER vs SNR')
        axes[2].set_xlabel('SNR (dB)'); axes[2].set_ylabel('BER')
        axes[2].legend(fontsize=8); axes[2].grid(True, alpha=0.3, which='both')

        # Capacity analysis
        snr_lin_range = 10 ** (snr_range / 10.0)
        # SISO capacity
        c_siso = np.log2(1 + snr_lin_range)
        # MIMO capacity (ergodic approximation for nT=nR=n)
        nt_vals = [1, 2, 4]
        for nt in nt_vals:
            # Approximate MIMO capacity: C ≈ nT × log2(1 + SNR/nT)
            c_mimo = nt * np.log2(1 + snr_lin_range / nt)
            axes[3].plot(snr_range, c_mimo, lw=2, label=f'{nt}×{nt} MIMO')
        axes[3].set_title('MIMO 信道容量 (bps/Hz)')
        axes[3].set_xlabel('SNR (dB)'); axes[3].set_ylabel('容量 (bps/Hz)')
        axes[3].legend(); axes[3].grid(True, alpha=0.3)

        # Diversity order vs multiplexing gain tradeoff
        axes[4].axis('off')
        axes[4].text(0.1, 0.5,
            f'MIMO 系统参数\n\n'
            f'发射天线: nT = {n_tx}\n'
            f'接收天线: nR = {n_rx}\n'
            f'总天线数: {n_tx + n_rx}\n\n'
            f'Alamouti STBC (nT=2时)\n'
            f'  ✓ 分集增益 = {min(n_tx, n_rx) * max(n_tx, n_rx)}\n'
            f'  复用增益 = 1 (单流)\n\n'
            f'仿真 BER = {ber_stbc:.4f}\n'
            f'信噪比 = {snr_db} dB',
            transform=axes[4].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        axes[5].axis('off')
        axes[5].text(0.1, 0.5,
            'MIMO 关键概念\n\n'
            '分集技术 (Diversity):\n'
            '  利用多路径独立衰落\n'
            '  提高抗衰落能力\n\n'
            '空分复用 (Spatial MUX):\n'
            '  并行发送不同数据流\n'
            '  成倍提高容量\n\n'
            'D-M折中 (Zheng-Tse):\n'
            '  d(r) = (nT-r)(nR-r)\n'
            '  r=0: 最大分集\n'
            '  r=min(nT,nR): 最大复用',
            transform=axes[5].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))

    def _plot_fhss(self, axes, n_bits, snr_db):
        """Frequency Hopping Spread Spectrum simulation."""
        n_hops = min(32, n_bits)
        hop_freqs = np.random.choice(np.arange(10, 200, 5), n_hops, replace=False)
        hop_freqs.sort()

        fs = 2000
        T_hop = 0.02  # 20ms per hop
        sps = int(fs * T_hop)
        t_hop = np.arange(sps) / fs

        # Generate FH signal
        fh_signal = np.zeros(n_hops * sps)
        for i, fh in enumerate(hop_freqs):
            fh_signal[i * sps:(i + 1) * sps] = np.cos(2 * np.pi * fh * t_hop)

        t_full = np.arange(len(fh_signal)) / fs

        # AWGN
        sig_power = np.mean(fh_signal ** 2)
        noise = np.random.normal(0, np.sqrt(sig_power / (10 ** (snr_db / 10))), len(fh_signal))
        rx_signal = fh_signal + noise

        axes[0].plot(t_full[:8 * sps], fh_signal[:8 * sps], color=COLORS[0], lw=1.0)
        axes[0].set_title('跳频信号时域波形（前8跳）')
        axes[0].set_xlabel('时间 (s)'); axes[0].set_ylabel('幅度')
        axes[0].grid(True, alpha=0.3)

        # Frequency hopping pattern (time-frequency grid)
        show_hops = min(n_hops, 20)
        axes[1].scatter(range(show_hops), hop_freqs[:show_hops],
                        c=COLORS[:show_hops % len(COLORS)] * (show_hops // len(COLORS) + 1),
                        s=100, marker='s')
        axes[1].step(range(show_hops), hop_freqs[:show_hops], where='mid',
                     color=COLORS[0], lw=1.0, alpha=0.5)
        axes[1].set_title('跳频序列（时频图）')
        axes[1].set_xlabel('跳数'); axes[1].set_ylabel('频率 (Hz)')
        axes[1].grid(True, alpha=0.3)

        # Spectrum of FH signal vs single carrier
        f_fh, p_fh = welch(fh_signal, fs=fs, nperseg=min(512, len(fh_signal)))
        fc_single = np.mean(hop_freqs)
        single_carrier = np.cos(2 * np.pi * fc_single * t_full[:sps])
        f_sc, p_sc = welch(single_carrier, fs=fs, nperseg=min(512, len(single_carrier)))

        axes[2].plot(f_fh, 10 * np.log10(p_fh + 1e-15), color=COLORS[0], lw=1.5, label='跳频信号')
        axes[2].plot(f_sc, 10 * np.log10(p_sc + 1e-15), color=COLORS[1], lw=1.5, ls='--', label='单载波')
        axes[2].set_title('跳频 vs 单载波 功率谱')
        axes[2].set_xlabel('频率 (Hz)'); axes[2].set_ylabel('PSD (dB)')
        axes[2].legend(); axes[2].grid(True, alpha=0.3)

        # Processing gain
        bw_fh = hop_freqs.max() - hop_freqs.min()
        bw_sc = 2 * 1 / T_hop  # approx single carrier BW
        pg = 10 * np.log10(bw_fh / (bw_sc + 1e-9))

        axes[3].axis('off')
        axes[3].text(0.1, 0.5,
            f'跳频通信 FHSS 参数\n\n'
            f'跳数: {n_hops}\n'
            f'跳频集合: {len(np.unique(hop_freqs))} 个频点\n'
            f'跳速: {1/T_hop:.0f} 跳/秒\n'
            f'跳频带宽: {bw_fh:.0f} Hz\n\n'
            f'处理增益: PG ≈ {pg:.1f} dB\n\n'
            f'抗干扰能力:\n'
            f'  ✓ 抗单频干扰\n'
            f'  ✓ 抗多径衰落\n'
            f'  ✓ 低截获概率(LPI)',
            transform=axes[3].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        axes[4].axis('off')
        axes[4].text(0.1, 0.5,
            '跳频通信应用\n\n'
            '军事通信:\n'
            '  反侦察、抗干扰\n\n'
            '民用通信:\n'
            '  蓝牙 (1600跳/秒)\n'
            '  IEEE 802.11 FH\n'
            '  军事卫星通信\n\n'
            'FHSS vs DSSS:\n'
            '  FHSS: 跳频扩频\n'
            '  DSSS: 直扩 (CDMA)',
            transform=axes[4].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))

        axes[5].axis('off')

    def _plot_ofdm_channel_estimation(self, axes, n_bits, n_sc, cp_len, snr_db):
        """OFDM with pilot-based channel estimation."""
        bits = np.random.randint(0, 2, n_bits)
        tx_signal, tx_syms = ofdm_modulate(bits, n_sc, cp_len)

        # Multipath channel
        h_true = np.array([1.0, 0.5 * np.exp(1j * 1.0), 0.3 * np.exp(-1j * 0.5)])
        rx_signal = np.convolve(tx_signal, h_true)[:len(tx_signal)]

        snr_lin = 10 ** (snr_db / 10)
        sig_power = np.mean(np.abs(rx_signal) ** 2) + 1e-12
        noise = (np.random.randn(len(rx_signal)) + 1j * np.random.randn(len(rx_signal))) * \
                np.sqrt(sig_power / (2 * snr_lin))
        rx_signal += noise

        # Channel frequency response (true)
        H_freq = np.fft.fft(h_true, n_sc)

        # LS channel estimation using pilots
        n_pilots = n_sc // 4
        pilot_indices = np.arange(0, n_sc, 4)
        pilot_syms = np.ones(n_pilots)  # known pilots

        # Demodulate first OFDM symbol
        sym_len = n_sc + cp_len
        rx_sym = rx_signal[:sym_len]
        time_domain = rx_sym[cp_len:]
        freq_domain = np.fft.fft(time_domain) / np.sqrt(n_sc)

        # LS estimation at pilot positions
        H_est_pilots = freq_domain[pilot_indices] / pilot_syms
        # Interpolate to all subcarriers
        from scipy.interpolate import interp1d
        f_interp = interp1d(pilot_indices, H_est_pilots.real, kind='linear',
                            fill_value='extrapolate')
        H_est_real = f_interp(np.arange(n_sc))
        f_interp_imag = interp1d(pilot_indices, H_est_pilots.imag, kind='linear',
                                 fill_value='extrapolate')
        H_est_imag = f_interp_imag(np.arange(n_sc))
        H_est = H_est_real + 1j * H_est_imag

        # Plot true vs estimated channel
        freqs = np.arange(n_sc)
        axes[0].plot(freqs, np.abs(H_freq), color=COLORS[0], lw=2, label='真实信道 |H(f)|')
        axes[0].plot(freqs, np.abs(H_est), color=COLORS[1], lw=1.5, ls='--', label='LS估计 |Ĥ(f)|')
        axes[0].scatter(pilot_indices, np.abs(H_est_pilots), s=50, color=COLORS[2], zorder=5, label='导频点')
        axes[0].set_title('多径信道频域响应与LS信道估计')
        axes[0].set_xlabel('子载波序号'); axes[0].set_ylabel('幅度')
        axes[0].legend(fontsize=8); axes[0].grid(True, alpha=0.3)

        axes[1].plot(freqs, np.angle(H_freq), color=COLORS[0], lw=2, label='真实相位')
        axes[1].plot(freqs, np.angle(H_est), color=COLORS[1], lw=1.5, ls='--', label='估计相位')
        axes[1].set_title('信道相位响应')
        axes[1].set_xlabel('子载波序号'); axes[1].set_ylabel('相位 (rad)')
        axes[1].legend(fontsize=8); axes[1].grid(True, alpha=0.3)

        # Received vs equalized constellation
        n_demod = min(len(rx_signal) // sym_len, 5)
        all_rx = ofdm_demodulate(rx_signal, n_sc, cp_len, n_demod)
        n_show = min(len(all_rx), 200)
        axes[2].scatter(np.real(all_rx[:n_show]), np.imag(all_rx[:n_show]),
                        s=8, color=COLORS[3], alpha=0.6, label='均衡前')
        axes[2].set_title('OFDM 接收星座（均衡前）')
        axes[2].set_xlabel('I'); axes[2].set_ylabel('Q')
        axes[2].set_aspect('equal'); axes[2].grid(True, alpha=0.3)
        axes[2].axhline(0, color='#2a3a5a', lw=0.8)
        axes[2].axvline(0, color='#2a3a5a', lw=0.8)

        # Apply channel equalization
        eq_syms = all_rx / (H_est[1:len(all_rx)+1] + 1e-9)
        axes[3].scatter(np.real(eq_syms[:n_show]), np.imag(eq_syms[:n_show]),
                        s=8, color=COLORS[0], alpha=0.6, label='均衡后')
        axes[3].set_title('OFDM 均衡后星座（频域均衡）')
        axes[3].set_xlabel('I'); axes[3].set_ylabel('Q')
        axes[3].set_aspect('equal'); axes[3].grid(True, alpha=0.3)
        axes[3].axhline(0, color='#2a3a5a', lw=0.8)
        axes[3].axvline(0, color='#2a3a5a', lw=0.8)

        est_err = np.mean(np.abs(H_freq[:len(H_est)] - H_est) ** 2)
        axes[4].axis('off')
        axes[4].text(0.1, 0.5,
            f'OFDM 信道估计\n\n'
            f'估计方法: LS (最小二乘)\n'
            f'导频间隔: 每4个子载波\n'
            f'导频数量: {n_pilots}\n'
            f'子载波总数: {n_sc}\n\n'
            f'信道估计MSE: {est_err:.4f}\n'
            f'信道: 3径多径\n'
            f'  h = [1.0, 0.5e^j, 0.3e^-j]\n\n'
            f'均衡方式: 频域单抽头\n'
            f'  Ŷ = Y / Ĥ',
            transform=axes[4].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        axes[5].axis('off')
        axes[5].text(0.1, 0.5,
            'OFDM 信道估计方法\n\n'
            '1. LS (最小二乘):\n'
            '   Ĥ = Y_pilot/X_pilot\n'
            '   简单快速，噪声敏感\n\n'
            '2. MMSE (最小均方误差):\n'
            '   性能更好，需先验信息\n\n'
            '3. 决策反馈:\n'
            '   利用数据辅助估计\n\n'
            '4. 深度学习:\n'
            '   5G中的新方向',
            transform=axes[5].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))

    def _plot_dvbt(self, axes, snr_db):
        """DVB-T system overview simulation."""
        # DVB-T key parameters (simplified 2K mode)
        n_sc = 2048  # 2K mode
        n_useful = 1705  # useful subcarriers
        cp_len = n_sc // 4  # 1/4 guard interval
        mod_order = 4  # 16QAM

        n_bits = n_useful * mod_order
        bits = np.random.randint(0, 2, n_bits)
        tx_signal, tx_syms = ofdm_modulate(bits[:n_useful * 2], 64, 16)  # simplified

        # DVB-T BER curves for different modulations
        snr_range = np.linspace(0, 30, 100)
        from scipy.special import erfc
        snr_lin = 10 ** (snr_range / 10)

        ber_qpsk = 0.5 * erfc(np.sqrt(snr_lin))
        ber_16qam = (3/4) * erfc(np.sqrt(snr_lin * 2 / 5))
        ber_64qam = (7/12) * erfc(np.sqrt(snr_lin * 2 / 21))

        axes[0].semilogy(snr_range, ber_qpsk, color=COLORS[0], lw=2, label='QPSK (2 bit/sym)')
        axes[0].semilogy(snr_range, ber_16qam, color=COLORS[1], lw=2, label='16QAM (4 bit/sym)')
        axes[0].semilogy(snr_range, ber_64qam, color=COLORS[2], lw=2, label='64QAM (6 bit/sym)')
        axes[0].axvline(10, color=COLORS[3], ls='--', lw=1, label='典型接收SNR=10dB')
        axes[0].set_title('DVB-T 不同调制方式 BER 曲线')
        axes[0].set_xlabel('Eb/N0 (dB)'); axes[0].set_ylabel('BER')
        axes[0].set_xlim(0, 30); axes[0].set_ylim(1e-7, 1)
        axes[0].legend(fontsize=8); axes[0].grid(True, alpha=0.3, which='both')

        # DVB-T spectrum
        t = np.linspace(0, 0.001, 8192)
        sig = np.zeros(len(t))
        for k in range(1, n_useful, 10):
            sig += np.cos(2 * np.pi * (k * 4464 + 506000) * t) / np.sqrt(n_useful)
        f_dvbt, p_dvbt = welch(sig, fs=1 / (t[1] - t[0]), nperseg=min(1024, len(sig)))
        axes[1].plot((f_dvbt - 506000) / 1e3, 10 * np.log10(p_dvbt + 1e-15), color=COLORS[0], lw=1.0)
        axes[1].set_title('DVB-T 信号频谱 (8MHz 信道)')
        axes[1].set_xlabel('相对频率 (kHz)'); axes[1].set_ylabel('PSD (dB)')
        axes[1].set_xlim(-4000, 4000)
        axes[1].grid(True, alpha=0.3)

        axes[2].axis('off')
        axes[2].text(0.05, 0.95,
            'DVB-T 系统参数 (2K模式)\n\n'
            '  OFDM模式:  2K (2048子载波)\n'
            '  有效子载波: 1705\n'
            '  信道带宽:   8 MHz\n'
            '  保护间隔:   1/4\n\n'
            '  调制方式:   QPSK/16/64QAM\n'
            '  信道编码:   卷积码+RS码\n'
            '  交织:       频率/时间交织\n\n'
            '  应用: 地面数字电视广播\n'
            '  标准: ETSI EN 300 744',
            transform=axes[2].transAxes, fontsize=9, color='#cfd8dc',
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        axes[3].axis('off')
        axes[3].text(0.05, 0.95,
            'DVB-T 系统框图\n\n'
            '发射链路:\n'
            '  MPEG-2 TS\n'
            '  → RS(204,188) 外码\n'
            '  → 卷积交织\n'
            '  → 卷积码 (R=1/2~7/8)\n'
            '  → 内交织\n'
            '  → QPSK/QAM 映射\n'
            '  → OFDM (2K/8K)\n'
            '  → 保护间隔插入\n'
            '  → 射频发射',
            transform=axes[3].transAxes, fontsize=9, color='#cfd8dc',
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        for i in range(4, 6):
            axes[i].axis('off')
        axes[4].text(0.1, 0.5,
            'DVB 标准族\n\n'
            '  DVB-T:  地面传输\n'
            '  DVB-T2: 第二代(2009)\n'
            '  DVB-S:  卫星传输\n'
            '  DVB-S2: 第二代\n'
            '  DVB-C:  有线传输\n'
            '  DVB-C2: 第二代\n'
            '  DVB-H:  手持终端\n\n'
            '中国标准: DTMB\n'
            '  (地面数字多媒体广播)',
            transform=axes[4].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))
