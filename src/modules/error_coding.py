"""差错控制编码 — 汉明码, 卷积码, LDPC(近似), 极化码(近似) + BER曲线"""
import numpy as np
from scipy.special import erfc
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox
from src.ui.base_module import BaseModuleWidget, COLORS


# ── Hamming(7,4) ──────────────────────────────────────────────────────────────
H74_G = np.array([
    [1, 0, 0, 0, 1, 1, 0],
    [0, 1, 0, 0, 1, 0, 1],
    [0, 0, 1, 0, 0, 1, 1],
    [0, 0, 0, 1, 1, 1, 1],
], dtype=int)

H74_H = np.array([
    [1, 1, 0, 1, 1, 0, 0],
    [1, 0, 1, 1, 0, 1, 0],
    [0, 1, 1, 1, 0, 0, 1],
], dtype=int)


def hamming_encode(bits):
    """Encode bit blocks of 4 into Hamming(7,4) codewords."""
    n = (len(bits) // 4) * 4
    bits = bits[:n]
    codewords = []
    for i in range(0, n, 4):
        blk = bits[i:i+4]
        cw = (blk @ H74_G) % 2
        codewords.extend(cw)
    return np.array(codewords, dtype=int)


def hamming_decode(rx_bits):
    """Decode Hamming(7,4) with single-error correction."""
    n = (len(rx_bits) // 7) * 7
    rx_bits = rx_bits[:n]
    decoded = []
    n_errors = 0
    for i in range(0, n, 7):
        cw = rx_bits[i:i+7]
        syndrome = (H74_H @ cw) % 2
        s = syndrome[0] * 4 + syndrome[1] * 2 + syndrome[2]
        if s != 0:
            cw[s - 1] ^= 1
            n_errors += 1
        decoded.extend(cw[:4])
    return np.array(decoded, dtype=int), n_errors


# ── Simple Rate-1/2 Convolutional Code k=1, n=2, K=3 ─────────────────────────
def conv_encode(bits, g1=0b111, g2=0b101):
    """Rate-1/2 convolutional encoder, constraint length 3."""
    K = 3
    shift_reg = np.zeros(K, dtype=int)
    out = []
    padded = np.concatenate([bits, np.zeros(K - 1, dtype=int)])
    for b in padded:
        shift_reg = np.roll(shift_reg, 1)
        shift_reg[0] = b
        b1 = int(np.sum(shift_reg * np.array([g1 >> (K - 1 - j) & 1 for j in range(K)])) % 2)
        b2 = int(np.sum(shift_reg * np.array([g2 >> (K - 1 - j) & 1 for j in range(K)])) % 2)
        out.extend([b1, b2])
    return np.array(out, dtype=int)


def viterbi_decode(rx, n_bits, g1=0b111, g2=0b101):
    """Viterbi hard-decision decoder for rate-1/2, K=3 code."""
    K = 3
    n_states = 2 ** (K - 1)

    def branch_metric(state, new_bit, rx_pair):
        # Compute encoder output for this transition
        sr = [(state >> (K - 2 - i)) & 1 for i in range(K - 1)]
        sr_new = [new_bit] + sr
        b1 = int(sum(sr_new[j] * ((g1 >> (K - 1 - j)) & 1) for j in range(K)) % 2)
        b2 = int(sum(sr_new[j] * ((g2 >> (K - 1 - j)) & 1) for j in range(K)) % 2)
        return (b1 != rx_pair[0]) + (b2 != rx_pair[1])  # Hamming distance

    INF = 1e9
    pm = np.full(n_states, INF)
    pm[0] = 0
    survivors = [[] for _ in range(n_states)]

    n_total = n_bits + K - 1
    for t in range(n_total):
        if 2 * t + 1 >= len(rx):
            break
        rx_pair = rx[2 * t:2 * t + 2]
        pm_new = np.full(n_states, INF)
        surv_new = [None] * n_states
        for s in range(n_states):
            if pm[s] == INF:
                continue
            for bit in (0, 1):
                next_s = ((s << 1) | bit) & (n_states - 1)
                metric = pm[s] + branch_metric(s, bit, rx_pair)
                if metric < pm_new[next_s]:
                    pm_new[next_s] = metric
                    surv_new[next_s] = survivors[s] + [bit]
        pm = pm_new
        survivors = [s if s is not None else [] for s in surv_new]

    best = int(np.argmin(pm))
    path = survivors[best]
    return np.array(path[:n_bits], dtype=int) if len(path) >= n_bits else np.zeros(n_bits, dtype=int)


# ── LDPC (simplified BER curve approximation) ─────────────────────────────────
def ldpc_ber_approx(snr_db_arr, rate=0.5):
    """Approximate LDPC BER curve via density evolution approximation."""
    snr = 10 ** (np.array(snr_db_arr) / 10)
    # Threshold SNR for rate-1/2 LDPC is approx 0.187 dB above Shannon limit
    # Shannon capacity: C = log2(1+SNR)
    # For rate-1/2: SNR_min ≈ 0 dB, LDPC works near ~0.5 dB above Shannon
    shannon_snr = (2 ** (2 * rate) - 1)
    sigma2 = 1.0 / snr
    # Use turbo-like approximation
    ber = np.clip(0.5 * erfc(np.sqrt(snr * rate)), 1e-10, 0.5)
    # LDPC gets closer to Shannon limit — apply ~3dB gain over uncoded
    snr_eff = snr * 3.0
    ber_ldpc = np.clip(0.5 * erfc(np.sqrt(snr_eff * rate)), 1e-10, 0.5)
    return ber_ldpc


# ── Polar Code (simplified BER) ──────────────────────────────────────────────
def polar_ber_approx(snr_db_arr, rate=0.5):
    """Approximate polar code BER (rate-1/2)."""
    snr = 10 ** (np.array(snr_db_arr) / 10)
    # Polar code approaches capacity, ~1dB from Shannon for practical lengths
    snr_eff = snr * 4.0
    ber = np.clip(0.5 * erfc(np.sqrt(snr_eff * rate)), 1e-10, 0.5)
    return ber


class ErrorCodingWidget(BaseModuleWidget):
    def __init__(self, user, parent=None):
        super().__init__(user, rows=3, cols=2, figsize=(11, 8), parent=parent)
        self._build_controls()
        self._run()

    def _build_controls(self):
        self.add_section_title('🛡️  差错控制编码')

        self._code = QComboBox()
        self._code.addItems(['汉明码 Hamming(7,4)', '卷积码 (Rate=1/2, K=3)', 'BER曲线全对比'])
        self.add_param_row('编码方案', self._code)

        self._n_bits = QSpinBox()
        self._n_bits.setRange(16, 2048)
        self._n_bits.setValue(256)
        self.add_param_row('信息比特数', self._n_bits)

        self._snr = QDoubleSpinBox()
        self._snr.setRange(-5, 20)
        self._snr.setValue(5.0)
        self._snr.setSuffix(' dB')
        self.add_param_row('信道 Eb/N0', self._snr)

        self._ber_simpts = QSpinBox()
        self._ber_simpts.setRange(3, 12)
        self._ber_simpts.setValue(6)
        self.add_param_row('BER曲线点数', self._ber_simpts)

        self.add_spacer()
        self.add_run_button(callback=self._run)
        self.add_stretch()

    def _run(self):
        code_idx = self._code.currentIndex()
        n_bits = self._n_bits.value()
        snr_db = self._snr.value()

        self.canvas.clear_axes()
        axes = self.canvas.axes

        if code_idx == 0:
            self._plot_hamming(axes, n_bits, snr_db)
        elif code_idx == 1:
            self._plot_conv(axes, n_bits, snr_db)
        else:
            self._plot_ber_all(axes)

        self.canvas.fig.tight_layout(pad=1.5)
        self.canvas.draw()

    def _bpsk_channel(self, coded, snr_db):
        """BPSK modulation + AWGN + hard-decision demodulation."""
        bpsk = coded * 2.0 - 1.0
        noise_std = np.sqrt(1.0 / (2 * 10 ** (snr_db / 10)))
        rx = bpsk + np.random.normal(0, noise_std, len(bpsk))
        return (rx < 0).astype(int)

    def _plot_hamming(self, axes, n_bits, snr_db):
        bits = np.random.randint(0, 2, n_bits)
        coded = hamming_encode(bits)
        rx = self._bpsk_channel(coded, snr_db)
        decoded, n_corrected = hamming_decode(rx.copy())
        n = min(len(bits), len(decoded))
        ber_uncoded = np.mean(self._bpsk_channel(bits, snr_db)[:n] != bits[:n])
        ber_coded = np.mean(decoded[:n] != bits[:n])

        # Visualize first 64 bits
        show = min(64, n_bits)
        axes[0].imshow(bits[:show].reshape(1, -1), cmap='RdYlGn', aspect='auto',
                       vmin=0, vmax=1, interpolation='none')
        axes[0].set_title(f'原始信息比特 (前{show}位)')
        axes[0].set_xlabel('比特序号'); axes[0].set_yticks([])
        axes[0].grid(False)

        show_coded = min(112, len(coded))
        axes[1].imshow(coded[:show_coded].reshape(1, -1), cmap='RdYlGn', aspect='auto',
                       vmin=0, vmax=1, interpolation='none')
        axes[1].set_title(f'Hamming(7,4) 编码后 (前{show_coded}位)')
        axes[1].set_xlabel('比特序号'); axes[1].set_yticks([])
        axes[1].grid(False)

        show_rx = min(112, len(rx))
        err_mask = (rx[:show_rx] != coded[:show_rx]).astype(float)
        axes[2].imshow(rx[:show_rx].reshape(1, -1), cmap='RdYlGn', aspect='auto',
                       vmin=0, vmax=1, interpolation='none')
        axes[2].set_title(f'接收序列 (SNR={snr_db}dB, 红=错误)')
        axes[2].set_xlabel('比特序号'); axes[2].set_yticks([])
        axes[2].grid(False)

        axes[3].imshow(decoded[:show].reshape(1, -1), cmap='RdYlGn', aspect='auto',
                       vmin=0, vmax=1, interpolation='none')
        axes[3].set_title(f'译码后 ({n_corrected}个码字被纠错)')
        axes[3].set_xlabel('比特序号'); axes[3].set_yticks([])
        axes[3].grid(False)

        # BER vs SNR
        snr_range = np.arange(-2, 12, 1.5)
        ber_u, ber_c = [], []
        for s in snr_range:
            rx_u = self._bpsk_channel(bits, s)
            ber_u.append(np.mean(rx_u[:n] != bits[:n]))
            c2 = hamming_encode(bits)
            rx_c = self._bpsk_channel(c2, s)
            dec, _ = hamming_decode(rx_c)
            ber_c.append(np.mean(dec[:n] != bits[:n]))

        axes[4].semilogy(snr_range, [max(b, 1e-6) for b in ber_u], 'o-',
                         color=COLORS[0], lw=2, label='未编码 BPSK')
        axes[4].semilogy(snr_range, [max(b, 1e-6) for b in ber_c], 's-',
                         color=COLORS[1], lw=2, label='Hamming(7,4)')
        axes[4].set_title('汉明码 BER vs Eb/N0')
        axes[4].set_xlabel('Eb/N0 (dB)'); axes[4].set_ylabel('BER')
        axes[4].legend(); axes[4].grid(True, alpha=0.3, which='both')

        axes[5].axis('off')
        rate = 4 / 7
        axes[5].text(0.1, 0.5,
            f'Hamming(7,4) 参数\n\n'
            f'编码率: k/n = 4/7 ≈ {rate:.3f}\n'
            f'最小汉明距: dmin = 3\n'
            f'纠错能力: t = 1 (单比特)\n'
            f'检错能力: e = 2\n\n'
            f'当前 SNR = {snr_db} dB\n'
            f'信息比特: {n_bits}\n'
            f'编码比特: {len(coded)}\n'
            f'纠正码字数: {n_corrected}\n\n'
            f'未编码 BER ≈ {ber_uncoded:.4f}\n'
            f'编码后 BER ≈ {ber_coded:.4f}',
            transform=axes[5].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

    def _plot_conv(self, axes, n_bits, snr_db):
        bits = np.random.randint(0, 2, n_bits)
        coded = conv_encode(bits)
        rx_coded = self._bpsk_channel(coded, snr_db)

        # Viterbi decode
        decoded = viterbi_decode(rx_coded, n_bits)
        n = min(len(bits), len(decoded))
        ber_uncoded = np.mean(self._bpsk_channel(bits, snr_db)[:n] != bits[:n])
        ber_coded = np.mean(decoded[:n] != bits[:n])

        show = min(64, n_bits)
        axes[0].step(range(show), bits[:show], where='post', color=COLORS[0], lw=1.5)
        axes[0].set_title('原始信息比特')
        axes[0].set_xlabel('比特序号'); axes[0].set_ylabel('电平')
        axes[0].set_ylim(-0.2, 1.3); axes[0].grid(True, alpha=0.3)

        show_coded = min(128, len(coded))
        axes[1].step(range(show_coded), coded[:show_coded], where='post', color=COLORS[1], lw=1.2)
        axes[1].set_title('卷积编码输出 (Rate=1/2, g1=111, g2=101)')
        axes[1].set_xlabel('比特序号'); axes[1].set_ylabel('电平')
        axes[1].set_ylim(-0.2, 1.3); axes[1].grid(True, alpha=0.3)

        axes[2].step(range(show_coded), rx_coded[:show_coded], where='post', color=COLORS[3], lw=1.2)
        axes[2].set_title(f'接收比特 (SNR={snr_db}dB)')
        axes[2].set_xlabel('比特序号'); axes[2].set_ylabel('电平')
        axes[2].set_ylim(-0.2, 1.3); axes[2].grid(True, alpha=0.3)

        axes[3].step(range(show), decoded[:show], where='post', color=COLORS[2], lw=1.5, label='Viterbi译码')
        axes[3].step(range(show), bits[:show] + 1.5, where='post', color=COLORS[0], lw=1.5, label='原始比特', alpha=0.7)
        errors = bits[:n] != decoded[:n]
        err_pos = np.where(errors)[0]
        err_pos = err_pos[err_pos < show]
        if len(err_pos):
            axes[3].scatter(err_pos, np.ones(len(err_pos)) * 2.8, marker='x', color='red', s=60, zorder=5)
        axes[3].set_title(f'Viterbi 译码结果 (BER={ber_coded:.4f})')
        axes[3].set_xlabel('比特序号'); axes[3].set_ylabel('电平')
        axes[3].legend(fontsize=8); axes[3].grid(True, alpha=0.3)

        # BER vs SNR
        snr_range = np.arange(-2, 12, 1.5)
        ber_u, ber_c = [], []
        for s in snr_range:
            rx_u = self._bpsk_channel(bits, s)
            ber_u.append(np.mean(rx_u[:n] != bits[:n]))
            c2 = conv_encode(bits)
            rx_c = self._bpsk_channel(c2, s)
            dec2 = viterbi_decode(rx_c, n_bits)
            ber_c.append(np.mean(dec2[:n] != bits[:n]))

        axes[4].semilogy(snr_range, [max(b, 1e-6) for b in ber_u], 'o-',
                         color=COLORS[0], lw=2, label='未编码 BPSK')
        axes[4].semilogy(snr_range, [max(b, 1e-6) for b in ber_c], 's-',
                         color=COLORS[1], lw=2, label='卷积码+Viterbi')
        axes[4].set_title('卷积码 BER vs Eb/N0')
        axes[4].set_xlabel('Eb/N0 (dB)'); axes[4].set_ylabel('BER')
        axes[4].legend(); axes[4].grid(True, alpha=0.3, which='both')

        axes[5].axis('off')
        axes[5].text(0.1, 0.5,
            '卷积码 + Viterbi 译码\n\n'
            f'编码参数:\n'
            f'  码率: R = 1/2\n'
            f'  约束长度: K = 3\n'
            f'  生成多项式:\n'
            f'    g1 = 111 (oct: 7)\n'
            f'    g2 = 101 (oct: 5)\n\n'
            f'Viterbi 最大似然译码\n'
            f'时间复杂度: O(L × 2^(K-1))\n\n'
            f'当前结果:\n'
            f'  未编码 BER ≈ {ber_uncoded:.4f}\n'
            f'  编码后 BER ≈ {ber_coded:.4f}',
            transform=axes[5].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

    def _plot_ber_all(self, axes):
        snr = np.linspace(-2, 12, 100)
        snr_lin = 10 ** (snr / 10)

        # Uncoded BPSK
        ber_bpsk = 0.5 * erfc(np.sqrt(snr_lin))
        # Hamming(7,4) approximation
        p = 0.5 * erfc(np.sqrt(snr_lin * 4 / 7))
        ber_hamming = 1 - (1 - p) ** 7 - 7 * p * (1 - p) ** 6
        # Convolutional code (free distance 5) approximation
        ber_conv = 0.5 * erfc(np.sqrt(snr_lin * 2.5))
        # LDPC
        ber_ldpc = ldpc_ber_approx(snr)
        # Polar
        ber_polar = polar_ber_approx(snr)
        # Shannon limit line at BER=1e-5
        shannon_snr = 10 * np.log10(2 ** (2 * 0.5) - 1)  # -0.19 dB for rate-1/2

        ax = axes[0]
        ax.semilogy(snr, ber_bpsk, color=COLORS[0], lw=2, label='未编码 BPSK')
        ax.semilogy(snr, np.clip(ber_hamming, 1e-8, 1), color=COLORS[1], lw=2, label='Hamming(7,4)')
        ax.semilogy(snr, np.clip(ber_conv, 1e-8, 1), color=COLORS[2], lw=2, label='卷积码 R=1/2, K=3')
        ax.semilogy(snr, np.clip(ber_ldpc, 1e-8, 1), color=COLORS[3], lw=2, label='LDPC R=1/2')
        ax.semilogy(snr, np.clip(ber_polar, 1e-8, 1), color=COLORS[4], lw=2, label='极化码 R=1/2')
        ax.axvline(shannon_snr, color='white', lw=1.5, ls=':', alpha=0.7, label=f'Shannon极限 ({shannon_snr:.1f}dB)')
        ax.set_title('各编码方案 BER vs Eb/N0 (Rate=1/2)')
        ax.set_xlabel('Eb/N0 (dB)'); ax.set_ylabel('BER')
        ax.set_xlim(-2, 12); ax.set_ylim(1e-7, 1)
        ax.legend(fontsize=8); ax.grid(True, alpha=0.3, which='both')

        # Coding gain at BER=1e-3
        axes[1].axis('off')
        gains_text = ('编码增益对比 (BER=10⁻³)\n\n'
                      '  方案          所需 Eb/N0   编码增益\n'
                      '  ─────────────────────────────\n'
                      '  未编码 BPSK    6.8 dB      0 dB\n'
                      '  Hamming(7,4)  5.2 dB     1.6 dB\n'
                      '  卷积码 R=1/2  3.5 dB     3.3 dB\n'
                      '  LDPC R=1/2   1.5 dB     5.3 dB\n'
                      '  极化码 R=1/2  1.0 dB     5.8 dB\n'
                      '  Shannon极限  -0.2 dB    7.0 dB\n\n'
                      '  极化码/LDPC 已接近 Shannon 极限')
        axes[1].text(0.05, 0.5, gains_text, transform=axes[1].transAxes,
                     fontsize=10, color='#cfd8dc', verticalalignment='center',
                     fontfamily='monospace',
                     bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        # Code history timeline
        axes[2].axis('off')
        timeline = [
            (1948, '(1948) Shannon信道容量定理'),
            (1950, '(1950) Hamming 汉明码'),
            (1955, '(1955) 卷积码'),
            (1993, '(1993) Turbo 码 (~0.5dB from Shannon)'),
            (1996, '(1996) LDPC 码重新发现'),
            (2008, '(2008) 极化码 (Arikan)'),
            (2018, '(2018) 5G NR 采用极化码'),
        ]
        for i, (year, desc) in enumerate(timeline):
            color = COLORS[i % len(COLORS)]
            axes[2].text(0.05, 0.9 - i * 0.12, desc,
                         transform=axes[2].transAxes, fontsize=9,
                         color=color, fontfamily='monospace')

        axes[2].set_title('信道编码发展历程')

        # Complexity comparison
        methods = ['Hamming', '卷积码\n+Viterbi', 'Turbo', 'LDPC', '极化码']
        complexity = [1, 3, 8, 6, 5]
        performance = [1.6, 3.3, 5.5, 5.3, 5.8]
        axes[3].scatter(complexity, performance, s=[200, 200, 200, 200, 200],
                        c=COLORS[:5], zorder=3)
        for i, m in enumerate(methods):
            axes[3].annotate(m, (complexity[i], performance[i]),
                             textcoords='offset points', xytext=(5, 3), fontsize=8, color='#90a4ae')
        axes[3].set_title('编码增益 vs 复杂度权衡')
        axes[3].set_xlabel('相对复杂度'); axes[3].set_ylabel('编码增益 (dB)')
        axes[3].grid(True, alpha=0.3)

        # 5G coding schemes
        axes[4].axis('off')
        axes[4].text(0.1, 0.5,
            '5G NR 信道编码方案\n\n'
            '  数据信道 (PDSCH/PUSCH):\n'
            '    → LDPC 码\n'
            '    → 码率 1/3 ~ 0.92\n\n'
            '  控制信道 (PDCCH):\n'
            '    → 极化码 (Polar Code)\n'
            '    → 码率 1/12 ~ 8/9\n\n'
            '  广播信道 (BCH):\n'
            '    → 极化码\n\n'
            '极化码首次进入国际标准！',
            transform=axes[4].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        axes[5].axis('off')
        axes[5].text(0.1, 0.5,
            'Shannon 信道容量定理\n\n'
            '  C = B × log₂(1 + S/N)\n\n'
            '  C: 信道容量 (bps)\n'
            '  B: 带宽 (Hz)\n'
            '  S/N: 信噪比\n\n'
            '这是通信系统的根本极限:\n'
            '任何编码方案都不能超过\n'
            'Shannon 极限！\n\n'
            '编码的目标就是逼近此极限。',
            transform=axes[5].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))
