/**
 * DSP Core Library — Communication Principles Simulation Platform
 * Provides: signal generation, FFT, noise, modulation math helpers
 */

const DSP = (() => {

  /* ── Signals ── */
  function sine(freq, phase, amp, t) {
    return amp * Math.sin(2 * Math.PI * freq * t + phase);
  }

  function cosine(freq, phase, amp, t) {
    return amp * Math.cos(2 * Math.PI * freq * t + phase);
  }

  /** Generate time-domain array: N samples, sampleRate Hz */
  function linspace(start, stop, N) {
    const arr = new Float64Array(N);
    const step = (stop - start) / (N - 1);
    for (let i = 0; i < N; i++) arr[i] = start + i * step;
    return arr;
  }

  function zeros(N) { return new Float64Array(N); }

  function sineWave(freq, sampleRate, N, amp = 1, phase = 0) {
    const x = new Float64Array(N);
    for (let i = 0; i < N; i++) {
      x[i] = amp * Math.sin(2 * Math.PI * freq * i / sampleRate + phase);
    }
    return x;
  }

  function squareWave(freq, sampleRate, N, amp = 1) {
    const x = new Float64Array(N);
    for (let i = 0; i < N; i++) {
      x[i] = Math.sin(2 * Math.PI * freq * i / sampleRate) >= 0 ? amp : -amp;
    }
    return x;
  }

  /** Random ±1 bit sequence */
  function randomBits(N) {
    const b = new Int8Array(N);
    for (let i = 0; i < N; i++) b[i] = Math.random() < .5 ? 1 : -1;
    return b;
  }

  /** Expand bits to samples: each bit repeated samplesPerBit times */
  function bitsToSamples(bits, samplesPerBit, highAmp = 1, lowAmp = -1) {
    const x = new Float64Array(bits.length * samplesPerBit);
    for (let i = 0; i < bits.length; i++) {
      const v = bits[i] > 0 ? highAmp : lowAmp;
      for (let j = 0; j < samplesPerBit; j++) x[i * samplesPerBit + j] = v;
    }
    return x;
  }

  /* ── FFT (Cooley–Tukey, radix-2) ── */
  function nextPow2(n) {
    let p = 1; while (p < n) p <<= 1; return p;
  }

  function fft(re, im) {
    const N = re.length;
    if (N <= 1) return;
    // bit-reversal
    let j = 0;
    for (let i = 1; i < N; i++) {
      let bit = N >> 1;
      for (; j & bit; bit >>= 1) j ^= bit;
      j ^= bit;
      if (i < j) {
        [re[i], re[j]] = [re[j], re[i]];
        [im[i], im[j]] = [im[j], im[i]];
      }
    }
    for (let len = 2; len <= N; len <<= 1) {
      const ang = -2 * Math.PI / len;
      const wRe = Math.cos(ang), wIm = Math.sin(ang);
      for (let i = 0; i < N; i += len) {
        let curRe = 1, curIm = 0;
        for (let k = 0; k < len / 2; k++) {
          const uRe = re[i + k], uIm = im[i + k];
          const vRe = re[i + k + len / 2] * curRe - im[i + k + len / 2] * curIm;
          const vIm = re[i + k + len / 2] * curIm + im[i + k + len / 2] * curRe;
          re[i + k] = uRe + vRe; im[i + k] = uIm + vIm;
          re[i + k + len / 2] = uRe - vRe; im[i + k + len / 2] = uIm - vIm;
          const nextRe = curRe * wRe - curIm * wIm;
          curIm = curRe * wIm + curIm * wRe; curRe = nextRe;
        }
      }
    }
  }

  /**
   * Compute single-sided magnitude spectrum (dB).
   * Returns { freqs, mag } arrays length N/2.
   */
  function spectrum(signal, sampleRate) {
    const N = nextPow2(signal.length);
    const re = new Float64Array(N);
    const im = new Float64Array(N);
    for (let i = 0; i < signal.length; i++) re[i] = signal[i];
    fft(re, im);
    const half = N / 2;
    const freqs = new Float64Array(half);
    const mag = new Float64Array(half);
    for (let i = 0; i < half; i++) {
      freqs[i] = i * sampleRate / N;
      const m = Math.sqrt(re[i] * re[i] + im[i] * im[i]) / N * (i === 0 ? 1 : 2);
      mag[i] = m;
    }
    return { freqs, mag };
  }

  /** mag array → dB (floor at -80 dB) */
  function magTodB(mag) {
    return Array.from(mag).map(m => m > 0 ? Math.max(20 * Math.log10(m), -80) : -80);
  }

  /* ── Noise ── */
  function gaussianNoise(N, sigma = 1) {
    const n = new Float64Array(N);
    for (let i = 0; i < N - 1; i += 2) {
      const u1 = Math.random() || 1e-15, u2 = Math.random();
      const mag = sigma * Math.sqrt(-2 * Math.log(u1));
      n[i]     = mag * Math.cos(2 * Math.PI * u2);
      n[i + 1] = mag * Math.sin(2 * Math.PI * u2);
    }
    return n;
  }

  /** Add AWGN at given SNR (dB) to signal */
  function addAWGN(signal, snrDb) {
    const sigPow = signal.reduce((s, v) => s + v * v, 0) / signal.length;
    const snrLin = Math.pow(10, snrDb / 10);
    const noiseSigma = Math.sqrt(sigPow / snrLin);
    const noise = gaussianNoise(signal.length, noiseSigma);
    const out = new Float64Array(signal.length);
    for (let i = 0; i < signal.length; i++) out[i] = signal[i] + noise[i];
    return out;
  }

  /* ── Modulation Helpers ── */

  /** AM modulation: s(t) = [1 + m*m(t)/A] * cos(2π fc t) */
  function modulateAM(message, carrier_freq, sampleRate, modIndex) {
    const N = message.length;
    const out = new Float64Array(N);
    for (let i = 0; i < N; i++) {
      const t = i / sampleRate;
      out[i] = (1 + modIndex * message[i]) * Math.cos(2 * Math.PI * carrier_freq * t);
    }
    return out;
  }

  /** DSB-SC: s(t) = m(t) * cos(2π fc t) */
  function modulateDSB(message, carrier_freq, sampleRate) {
    const N = message.length;
    const out = new Float64Array(N);
    for (let i = 0; i < N; i++) {
      const t = i / sampleRate;
      out[i] = message[i] * Math.cos(2 * Math.PI * carrier_freq * t);
    }
    return out;
  }

  /** FM modulation: s(t) = Ac cos(2π fc t + 2π kf ∫m(τ)dτ) */
  function modulateFM(message, carrier_freq, sampleRate, kf) {
    const N = message.length;
    const out = new Float64Array(N);
    let phase = 0;
    for (let i = 0; i < N; i++) {
      const t = i / sampleRate;
      phase += 2 * Math.PI * kf * message[i] / sampleRate;
      out[i] = Math.cos(2 * Math.PI * carrier_freq * t + phase);
    }
    return out;
  }

  /** Demodulate AM (envelope detector approximation) */
  function demodAM(amSignal, carrier_freq, sampleRate, cutoff = 0.05) {
    const N = amSignal.length;
    // Square + LPF (RC approximation)
    const env = new Float64Array(N);
    let prev = 0;
    const alpha = cutoff; // simple one-pole IIR
    for (let i = 0; i < N; i++) {
      const v = Math.abs(amSignal[i]);
      prev = prev + alpha * (v - prev);
      env[i] = prev;
    }
    // Remove DC
    const mean = env.reduce((a, b) => a + b, 0) / N;
    for (let i = 0; i < N; i++) env[i] -= mean;
    return env;
  }

  /* ── Digital Modulation ── */

  /** ASK: bit=1 → Ac cos, bit=0 → 0 */
  function modulateASK(bits, carrier_freq, sampleRate, samplesPerBit) {
    const N = bits.length * samplesPerBit;
    const out = new Float64Array(N);
    for (let i = 0; i < bits.length; i++) {
      const amp = bits[i] > 0 ? 1 : 0;
      for (let j = 0; j < samplesPerBit; j++) {
        const t = (i * samplesPerBit + j) / sampleRate;
        out[i * samplesPerBit + j] = amp * Math.cos(2 * Math.PI * carrier_freq * t);
      }
    }
    return out;
  }

  /** FSK: bit=1 → f1, bit=0 → f2 */
  function modulateFSK(bits, f1, f2, sampleRate, samplesPerBit) {
    const N = bits.length * samplesPerBit;
    const out = new Float64Array(N);
    let phase1 = 0, phase2 = 0;
    for (let i = 0; i < bits.length; i++) {
      for (let j = 0; j < samplesPerBit; j++) {
        const idx = i * samplesPerBit + j;
        phase1 += 2 * Math.PI * f1 / sampleRate;
        phase2 += 2 * Math.PI * f2 / sampleRate;
        out[idx] = bits[i] > 0 ? Math.cos(phase1) : Math.cos(phase2);
      }
    }
    return out;
  }

  /** BPSK: bit=1 → phase 0, bit=-1 → phase π */
  function modulateBPSK(bits, carrier_freq, sampleRate, samplesPerBit) {
    const N = bits.length * samplesPerBit;
    const out = new Float64Array(N);
    for (let i = 0; i < bits.length; i++) {
      const ph = bits[i] > 0 ? 0 : Math.PI;
      for (let j = 0; j < samplesPerBit; j++) {
        const t = (i * samplesPerBit + j) / sampleRate;
        out[i * samplesPerBit + j] = Math.cos(2 * Math.PI * carrier_freq * t + ph);
      }
    }
    return out;
  }

  /** QPSK: dibit → one of 4 phases {π/4, 3π/4, -π/4, -3π/4} */
  function modulateQPSK(bits, carrier_freq, sampleRate, samplesPerBit) {
    const phases = [Math.PI / 4, 3 * Math.PI / 4, -3 * Math.PI / 4, -Math.PI / 4];
    const N = Math.floor(bits.length / 2) * samplesPerBit;
    const out = new Float64Array(N);
    for (let i = 0; i < Math.floor(bits.length / 2); i++) {
      const b1 = bits[2 * i] > 0 ? 1 : 0;
      const b2 = bits[2 * i + 1] > 0 ? 1 : 0;
      const ph = phases[b1 * 2 + b2];
      for (let j = 0; j < samplesPerBit; j++) {
        const t = (i * samplesPerBit + j) / sampleRate;
        out[i * samplesPerBit + j] = Math.cos(2 * Math.PI * carrier_freq * t + ph);
      }
    }
    return out;
  }

  /* ── BER Theory ── */
  function erfc(x) {
    // Abramowitz & Stegun approx
    const t = 1 / (1 + .3275911 * Math.abs(x));
    const p = t * (.254829592 + t * (-.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))));
    const v = 1 - p * Math.exp(-x * x);
    return x >= 0 ? 1 - v : 1 + v;
  }

  function qFunc(x) { return .5 * erfc(x / Math.SQRT2); }

  function berBPSK(snrDb)  { return qFunc(Math.sqrt(2 * Math.pow(10, snrDb / 10))); }
  function berQPSK(snrDb)  { return qFunc(Math.sqrt(2 * Math.pow(10, snrDb / 10))); }
  function berFSK(snrDb)   { return qFunc(Math.sqrt(Math.pow(10, snrDb / 10))); }
  function berASK(snrDb)   { return qFunc(Math.sqrt(Math.pow(10, snrDb / 10) / 2)); }

  /* ── Baseband Coding ── */
  function encodeNRZ_L(bits) { return bitsToSamples(bits, 1, 1, -1); }
  function encodeNRZ_unipolar(bits) { return bitsToSamples(bits, 1, 1, 0); }

  function encodeRZ(bits) {
    const N = bits.length * 2;
    const x = new Float64Array(N);
    for (let i = 0; i < bits.length; i++) {
      x[i * 2] = bits[i] > 0 ? 1 : -1;
      x[i * 2 + 1] = 0;
    }
    return x;
  }

  function encodeManchester(bits) {
    const N = bits.length * 2;
    const x = new Float64Array(N);
    for (let i = 0; i < bits.length; i++) {
      if (bits[i] > 0) { x[i * 2] = 1; x[i * 2 + 1] = -1; }
      else              { x[i * 2] = -1; x[i * 2 + 1] = 1; }
    }
    return x;
  }

  /* ── PCM ── */
  function uniformQuantize(signal, bits) {
    const levels = Math.pow(2, bits);
    const maxVal = Math.max(...signal.map(Math.abs)) * 1.01;
    const step = (2 * maxVal) / levels;
    const quantized = new Float64Array(signal.length);
    const codes = new Int32Array(signal.length);
    for (let i = 0; i < signal.length; i++) {
      const idx = Math.floor((signal[i] + maxVal) / step);
      const clamped = Math.max(0, Math.min(levels - 1, idx));
      codes[i] = clamped;
      quantized[i] = -maxVal + (clamped + .5) * step;
    }
    return { quantized, codes, step, maxVal };
  }

  function sqnrUniform(bits) {
    return 6.02 * bits + 1.76; // dB
  }

  /* ── Sampling ── */
  function sampleSignal(signal, originalRate, newRate) {
    const step = originalRate / newRate;
    const samples = [];
    const sampleTimes = [];
    for (let i = 0; i < signal.length; i += step) {
      const idx = Math.round(i);
      if (idx < signal.length) {
        samples.push(signal[idx]);
        sampleTimes.push(idx);
      }
    }
    return { samples, sampleTimes };
  }

  /** Sinc interpolation (ideal reconstruction) */
  function sincInterpolate(samples, sampleTimes, outputLength) {
    const out = new Float64Array(outputLength);
    for (let n = 0; n < outputLength; n++) {
      let sum = 0;
      for (let k = 0; k < samples.length; k++) {
        const x = n - sampleTimes[k];
        sum += samples[k] * (x === 0 ? 1 : Math.sin(Math.PI * x / (outputLength / samples.length)) / (Math.PI * x / (outputLength / samples.length)));
      }
      out[n] = sum;
    }
    return out;
  }

  /* ── Utility ── */
  function arrayToPoints(yArr, xArr) {
    return Array.from(yArr).map((y, i) => ({ x: xArr ? xArr[i] : i, y }));
  }

  function downsample(arr, maxPoints) {
    if (arr.length <= maxPoints) return arr;
    const step = arr.length / maxPoints;
    const out = [];
    for (let i = 0; i < maxPoints; i++) out.push(arr[Math.round(i * step)]);
    return out;
  }

  function power(signal) {
    return signal.reduce((s, v) => s + v * v, 0) / signal.length;
  }

  function rms(signal) { return Math.sqrt(power(signal)); }

  return {
    sine, cosine, linspace, zeros, sineWave, squareWave, randomBits,
    bitsToSamples, nextPow2, fft, spectrum, magTodB, gaussianNoise,
    addAWGN, modulateAM, modulateDSB, modulateFM, demodAM,
    modulateASK, modulateFSK, modulateBPSK, modulateQPSK,
    berBPSK, berQPSK, berFSK, berASK, qFunc,
    encodeNRZ_L, encodeNRZ_unipolar, encodeRZ, encodeManchester,
    uniformQuantize, sqnrUniform, sampleSignal, sincInterpolate,
    arrayToPoints, downsample, power, rms
  };
})();
