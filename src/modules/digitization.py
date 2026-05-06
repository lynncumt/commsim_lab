"""实验3/4/6: 信号数字化与复用 — 抽样定理、PCM编码、ΔM、TDM"""
import numpy as np
from scipy.signal import butter, filtfilt
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QComboBox, QLabel, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt
from src.ui.base_module import BaseModuleWidget, COLORS


def _lpf(signal, cutoff, fs, order=5):
    nyq = fs / 2
    b, a = butter(order, min(cutoff / nyq, 0.99), btype='low')
    return filtfilt(b, a, signal)


def _pcm_encode(samples, n_bits):
    """Uniform PCM quantizer + encoder. Returns (levels, codes, quant_error)."""
    vmax = np.max(np.abs(samples)) + 1e-9
    # Normalize to [-1, 1]
    normalized = samples / vmax
    n_levels = 2 ** n_bits
    # Map to integer levels [0, n_levels-1]
    indices = np.clip(np.round((normalized + 1) / 2 * (n_levels - 1)).astype(int), 0, n_levels - 1)
    # Reconstruct
    quant = indices / (n_levels - 1) * 2 - 1
    quant_error = normalized - quant
    return indices, quant * vmax, quant_error * vmax


def _delta_modulation(signal, delta=0.1):
    """Simple delta modulation encoder."""
    n = len(signal)
    approx = np.zeros(n)
    bits = np.zeros(n, dtype=int)
    step = 0.0
    for i in range(1, n):
        if signal[i] > step:
            step += delta
            bits[i] = 1
        else:
            step -= delta
            bits[i] = 0
        approx[i] = step
    return bits, approx


class DigitizationWidget(BaseModuleWidget):
    def __init__(self, user, parent=None):
        super().__init__(user, rows=3, cols=2, figsize=(11, 8), parent=parent)
        self._build_controls()
        self._run()

    def _build_controls(self):
        self.add_section_title('🔢  数字化参数')

        self._mode = QComboBox()
        self._mode.addItems(['抽样定理验证', 'PCM 编码/译码', '增量调制 ΔM', '时分复用 TDM'])
        self.add_param_row('仿真模式', self._mode)

        self._fm = QDoubleSpinBox()
        self._fm.setRange(0.5, 200.0)
        self._fm.setValue(5.0)
        self._fm.setSuffix(' Hz')
        self.add_param_row('消息信号频率', self._fm)

        self._fs_factor = QDoubleSpinBox()
        self._fs_factor.setRange(0.5, 10.0)
        self._fs_factor.setValue(3.0)
        self._fs_factor.setSingleStep(0.5)
        self.add_param_row('采样率 (×fm)', self._fs_factor)

        self._nbits = QSpinBox()
        self._nbits.setRange(2, 16)
        self._nbits.setValue(8)
        self.add_param_row('PCM 量化位数', self._nbits)

        self._n_channels = QSpinBox()
        self._n_channels.setRange(2, 8)
        self._n_channels.setValue(4)
        self.add_param_row('TDM 信道数', self._n_channels)

        self._delta = QDoubleSpinBox()
        self._delta.setRange(0.01, 1.0)
        self._delta.setValue(0.1)
        self._delta.setSingleStep(0.01)
        self.add_param_row('ΔM 步长', self._delta)

        self.add_spacer()
        self.add_run_button(callback=self._run)
        self.add_stretch()

    def _run(self):
        mode = self._mode.currentIndex()
        fm = self._fm.value()
        fs_factor = self._fs_factor.value()
        fs = fm * 100  # high-res continuous signal
        T = max(1.0, 4.0 / fm)
        t = np.arange(0, T, 1.0 / fs)
        msg = np.sin(2 * np.pi * fm * t)

        self.canvas.clear_axes()
        axes = self.canvas.axes

        if mode == 0:  # Sampling theorem
            self._plot_sampling(axes, t, msg, fm, fs, fs_factor)
        elif mode == 1:  # PCM
            self._plot_pcm(axes, t, msg, fm, fs, self._nbits.value())
        elif mode == 2:  # Delta modulation
            self._plot_delta_mod(axes, t, msg, fm, fs)
        else:  # TDM
            self._plot_tdm(axes, fm, fs)

        self.canvas.fig.tight_layout(pad=1.5)
        self.canvas.draw()

    def _plot_sampling(self, axes, t, msg, fm, fs, factor):
        fs_sample = fm * factor
        sample_period = int(fs / fs_sample)
        sample_indices = np.arange(0, len(t), sample_period)
        t_s = t[sample_indices]
        s_s = msg[sample_indices]

        # Reconstruct via ideal LPF interpolation
        reconstructed = np.zeros_like(t)
        for i, (ti, si) in enumerate(zip(t_s, s_s)):
            reconstructed += si * np.sinc((t - ti) * fs_sample)

        axes[0].plot(t, msg, color=COLORS[0], lw=1.5, label='原始信号')
        axes[0].stem(t_s, s_s, linefmt=COLORS[1], markerfmt='o', basefmt=' ', label=f'采样点 (fs={fs_sample:.1f}Hz)')
        axes[0].set_title(f'奈奎斯特抽样定理 (fm={fm}Hz, fs={fs_sample:.1f}Hz)')
        axes[0].set_xlabel('时间 (s)'); axes[0].set_ylabel('幅度')
        axes[0].legend(); axes[0].grid(True, alpha=0.3)

        axes[1].plot(t, msg, color=COLORS[0], lw=1.5, label='原始信号')
        axes[1].plot(t, reconstructed, color=COLORS[1], lw=1.5, ls='--', label='重建信号')
        axes[1].set_title('信号重建（sinc插值）')
        axes[1].set_xlabel('时间 (s)'); axes[1].set_ylabel('幅度')
        axes[1].legend(); axes[1].grid(True, alpha=0.3)

        # Error analysis
        err = msg - reconstructed
        axes[2].plot(t, err, color=COLORS[2], lw=1.0)
        axes[2].set_title('重建误差')
        axes[2].set_xlabel('时间 (s)'); axes[2].set_ylabel('误差')
        axes[2].grid(True, alpha=0.3)

        # Spectrum comparison
        from scipy.signal import welch
        f1, p1 = welch(msg, fs=fs, nperseg=min(512, len(msg)))
        f2, p2 = welch(reconstructed, fs=fs, nperseg=min(512, len(reconstructed)))
        axes[3].plot(f1, 10 * np.log10(p1 + 1e-15), color=COLORS[0], label='原始')
        axes[3].plot(f2, 10 * np.log10(p2 + 1e-15), color=COLORS[1], ls='--', label='重建')
        axes[3].set_title('频谱对比')
        axes[3].set_xlabel('频率 (Hz)'); axes[3].set_ylabel('PSD (dB)')
        axes[3].set_xlim(0, fm * 10)
        axes[3].legend(); axes[3].grid(True, alpha=0.3)

        snr = 10 * np.log10(np.mean(msg ** 2) / (np.mean(err ** 2) + 1e-15))
        axes[4].axis('off')
        info = (f'抽样参数汇总\n\n'
                f'消息信号频率:  fm = {fm} Hz\n'
                f'奈奎斯特频率: 2fm = {2*fm} Hz\n'
                f'实际采样率:   fs = {fs_sample:.1f} Hz\n'
                f'采样率/奈频:  {factor:.1f}×\n\n'
                f'重建SNR: {snr:.1f} dB\n'
                f'{"✓ 满足奈奎斯特准则" if factor >= 2 else "✗ 不满足奈奎斯特准则 (混叠!)"}')
        axes[4].text(0.1, 0.5, info, transform=axes[4].transAxes,
                     fontsize=11, color='#cfd8dc', verticalalignment='center',
                     fontfamily='monospace',
                     bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        axes[5].axis('off')
        alias_info = ('奈奎斯特抽样定理说明\n\n'
                      '对于最高频率为 fm 的信号，\n'
                      '采样频率必须满足:\n\n'
                      '    fs ≥ 2·fm\n\n'
                      '否则会发生频谱混叠(Aliasing)，\n'
                      '无法完美重建原始信号。\n\n'
                      f'当前状态: fs/fm = {factor:.1f}×')
        axes[5].text(0.1, 0.5, alias_info, transform=axes[5].transAxes,
                     fontsize=10, color='#90a4ae', verticalalignment='center',
                     fontfamily='monospace',
                     bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))

    def _plot_pcm(self, axes, t, msg, fm, fs, n_bits):
        indices, quant, q_err = _pcm_encode(msg, n_bits)
        n_levels = 2 ** n_bits

        axes[0].plot(t, msg, color=COLORS[0], lw=1.5, label='原始信号')
        axes[0].plot(t, quant, color=COLORS[1], lw=1.0, ls='--', alpha=0.9, label=f'量化信号 ({n_bits}bit)')
        axes[0].set_title(f'PCM 量化 ({n_bits}位, {n_levels}电平)')
        axes[0].set_xlabel('时间 (s)'); axes[0].set_ylabel('幅度')
        axes[0].legend(); axes[0].grid(True, alpha=0.3)

        axes[1].plot(t, q_err, color=COLORS[2], lw=1.0)
        axes[1].axhline(1 / (2 * n_levels), color=COLORS[3], ls='--', lw=0.8, label=f'±Δ/2 = ±{1/(2*n_levels):.4f}')
        axes[1].axhline(-1 / (2 * n_levels), color=COLORS[3], ls='--', lw=0.8)
        axes[1].set_title('量化误差 (均匀量化噪声)')
        axes[1].set_xlabel('时间 (s)'); axes[1].set_ylabel('误差')
        axes[1].legend(); axes[1].grid(True, alpha=0.3)

        # Bit stream visualization (first few bits)
        n_show = min(32, len(indices))
        bit_stream = np.unpackbits(indices[:n_show].astype(np.uint8).reshape(-1, 1), axis=1)[:, -n_bits:]
        bit_flat = bit_stream.flatten()
        t_bits = np.arange(len(bit_flat))
        axes[2].step(t_bits, bit_flat, where='post', color=COLORS[0], lw=1.5)
        axes[2].set_title(f'PCM 编码位流 (前{n_show}个样本, {n_bits}bit/样本)')
        axes[2].set_xlabel('比特序号'); axes[2].set_ylabel('电平')
        axes[2].set_ylim(-0.2, 1.2)
        axes[2].grid(True, alpha=0.3)

        # SNR vs bits
        bits_range = range(2, 17)
        snr_vals = [6.02 * b + 1.76 for b in bits_range]
        axes[3].plot(list(bits_range), snr_vals, color=COLORS[0], lw=2, marker='o', ms=4)
        axes[3].axvline(n_bits, color=COLORS[1], ls='--', lw=1.5, label=f'当前: {n_bits}位')
        axes[3].axhline(6.02 * n_bits + 1.76, color=COLORS[2], ls=':', lw=1.0)
        axes[3].set_title('PCM 量化SNR vs 量化位数')
        axes[3].set_xlabel('量化位数 (bits)'); axes[3].set_ylabel('SQNR (dB)')
        axes[3].legend(); axes[3].grid(True, alpha=0.3)
        axes[3].annotate(f'{6.02*n_bits+1.76:.1f} dB',
                         xy=(n_bits, 6.02*n_bits+1.76),
                         xytext=(n_bits+0.5, 6.02*n_bits+1.76-3),
                         color=COLORS[1], fontsize=9)

        sqnr = 6.02 * n_bits + 1.76
        axes[4].axis('off')
        axes[4].text(0.1, 0.5,
            f'PCM 编码参数\n\n'
            f'量化位数:   {n_bits} bit\n'
            f'量化电平数: {n_levels}\n'
            f'量化步长:   Δ = {2/n_levels:.4f}\n'
            f'比特率:     {n_bits} × {fs:.0f} = {n_bits*fs:.0f} bps\n\n'
            f'理论SQNR = 6.02×{n_bits} + 1.76\n'
            f'         = {sqnr:.2f} dB',
            transform=axes[4].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        # Histogram of quantization error
        axes[5].hist(q_err, bins=50, color=COLORS[2], alpha=0.8, edgecolor='none')
        axes[5].set_title('量化误差分布（均匀分布）')
        axes[5].set_xlabel('量化误差'); axes[5].set_ylabel('频次')
        axes[5].grid(True, alpha=0.3)

    def _plot_delta_mod(self, axes, t, msg, fm, fs):
        delta = self._delta.value()
        bits, approx = _delta_modulation(msg, delta)

        show = min(int(fs * 3 / fm), len(t))
        axes[0].plot(t[:show], msg[:show], color=COLORS[0], lw=1.5, label='原始信号')
        axes[0].step(t[:show], approx[:show], where='post', color=COLORS[1], lw=1.0, label='ΔM 近似')
        axes[0].set_title(f'增量调制 ΔM (步长δ={delta})')
        axes[0].set_xlabel('时间 (s)'); axes[0].set_ylabel('幅度')
        axes[0].legend(); axes[0].grid(True, alpha=0.3)

        axes[1].step(t[:show], bits[:show], where='post', color=COLORS[2], lw=1.5)
        axes[1].set_title('ΔM 编码位流')
        axes[1].set_xlabel('时间 (s)'); axes[1].set_ylabel('比特值')
        axes[1].set_ylim(-0.2, 1.2)
        axes[1].grid(True, alpha=0.3)

        err = msg - approx
        axes[2].plot(t[:show], err[:show], color=COLORS[3], lw=1.0)
        axes[2].set_title('ΔM 量化误差（颗粒噪声+斜率过载）')
        axes[2].set_xlabel('时间 (s)'); axes[2].set_ylabel('误差')
        axes[2].grid(True, alpha=0.3)

        # Different delta values comparison
        deltas = [0.05, 0.1, 0.2, 0.4]
        snrs = []
        for d in deltas:
            _, approx_d = _delta_modulation(msg, d)
            snr_d = 10 * np.log10(np.mean(msg ** 2) / (np.mean((msg - approx_d) ** 2) + 1e-15))
            snrs.append(snr_d)
        axes[3].bar([str(d) for d in deltas], snrs, color=COLORS[:4])
        axes[3].set_title('不同步长δ下的ΔM信噪比')
        axes[3].set_xlabel('步长 δ'); axes[3].set_ylabel('SNR (dB)')
        axes[3].grid(True, alpha=0.3, axis='y')

        axes[4].axis('off')
        snr = snrs[deltas.index(min(deltas, key=lambda d: abs(d - delta)))]
        axes[4].text(0.1, 0.5,
            f'增量调制 ΔM 参数\n\n'
            f'步长 δ = {delta}\n'
            f'信号频率 fm = {fm} Hz\n'
            f'仿真SNR ≈ {snr:.1f} dB\n\n'
            f'注意事项:\n'
            f'  δ 太小 → 斜率过载失真\n'
            f'  δ 太大 → 颗粒噪声增大\n'
            f'  最优 δ 需权衡两者',
            transform=axes[4].transAxes, fontsize=10, color='#cfd8dc',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        axes[5].axis('off')
        axes[5].text(0.1, 0.5,
            '增量调制与PCM比较\n\n'
            '优点:\n'
            '  ✓ 电路简单\n'
            '  ✓ 编解码只需1bit\n'
            '  ✓ 同步要求低\n\n'
            '缺点:\n'
            '  ✗ 动态范围有限\n'
            '  ✗ 存在斜率过载\n'
            '  ✗ 信噪比低于PCM',
            transform=axes[5].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))

    def _plot_tdm(self, axes, fm, fs):
        n_ch = self._n_channels.value()
        T = 1.0
        t = np.arange(0, T, 1.0 / fs)
        freqs = [fm * (i + 1) for i in range(n_ch)]
        channels = [np.sin(2 * np.pi * f * t) for f in freqs]

        # TDM frame: interleave samples
        fs_per_ch = fs / n_ch
        sample_period = int(fs / fs_per_ch)
        frame = np.zeros(len(t))
        for i, ch in enumerate(channels):
            frame[i::sample_period * n_ch] = ch[i::sample_period * n_ch]

        # Plot original channels
        show = min(int(fs * 3 / fm), len(t))
        for i in range(min(n_ch, 4)):
            axes[0].plot(t[:show], channels[i][:show] + i * 2.5,
                         color=COLORS[i], lw=1.2, label=f'CH{i+1} ({freqs[i]:.0f}Hz)')
        axes[0].set_title(f'{n_ch}路信号TDM复用 — 各路信号')
        axes[0].set_xlabel('时间 (s)'); axes[0].set_ylabel('幅度（偏移显示）')
        axes[0].legend(fontsize=8); axes[0].grid(True, alpha=0.3)

        axes[1].plot(t[:show], frame[:show], color=COLORS[4], lw=1.0)
        axes[1].set_title('TDM 复用后帧信号')
        axes[1].set_xlabel('时间 (s)'); axes[1].set_ylabel('幅度')
        axes[1].grid(True, alpha=0.3)

        # Demultiplex
        demux = []
        for i in range(n_ch):
            ch_recovered = np.zeros(len(t))
            ch_recovered[i::sample_period * n_ch] = frame[i::sample_period * n_ch]
            ch_recovered = _lpf(ch_recovered, freqs[i] * 2.5, fs)
            demux.append(ch_recovered)

        for i in range(min(n_ch, 4)):
            axes[2].plot(t[:show], demux[i][:show] + i * 2.5,
                         color=COLORS[i], lw=1.2, label=f'解复用CH{i+1}')
        axes[2].set_title('TDM 解复用后信号')
        axes[2].set_xlabel('时间 (s)'); axes[2].set_ylabel('幅度（偏移显示）')
        axes[2].legend(fontsize=8); axes[2].grid(True, alpha=0.3)

        # TDM frame structure diagram
        axes[3].axis('off')
        frame_text = 'TDM 帧结构\n\n'
        for i in range(n_ch):
            frame_text += f'时隙 {i+1}: CH{i+1} ({freqs[i]:.0f}Hz)\n'
        frame_text += f'\n帧长 = {n_ch} 时隙\n'
        frame_text += f'每路采样率 = {fs/n_ch:.0f} Sa/s\n'
        frame_text += f'帧率 = {fs/n_ch:.0f} 帧/s'
        axes[3].text(0.1, 0.5, frame_text, transform=axes[3].transAxes,
                     fontsize=10, color='#cfd8dc', verticalalignment='center',
                     fontfamily='monospace',
                     bbox=dict(boxstyle='round', facecolor='#1a2a4a', alpha=0.8))

        # SNR of recovered channels
        snrs = []
        for i in range(n_ch):
            snr = 10 * np.log10(np.mean(channels[i] ** 2) / (np.mean((channels[i] - demux[i]) ** 2) + 1e-15))
            snrs.append(snr)
        axes[4].bar([f'CH{i+1}' for i in range(n_ch)], snrs, color=COLORS[:n_ch])
        axes[4].set_title('各路信号解复用SNR')
        axes[4].set_xlabel('信道'); axes[4].set_ylabel('SNR (dB)')
        axes[4].grid(True, alpha=0.3, axis='y')

        axes[5].axis('off')
        axes[5].text(0.1, 0.5,
            '时分复用 TDM 原理\n\n'
            '将时间轴划分成等间隔时隙，\n'
            '每个时隙分配给一路信号使用。\n\n'
            '关键参数:\n'
            f'  信道数: {n_ch}\n'
            f'  总采样率: {fs:.0f} Sa/s\n'
            f'  每路速率: {fs/n_ch:.0f} Sa/s\n\n'
            '应用: PCM电话、数字广播',
            transform=axes[5].transAxes, fontsize=10, color='#90a4ae',
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1826', alpha=0.6))
