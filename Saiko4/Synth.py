import numpy as np

def SynthThread(freq: float, Amp: complex, window_size: int, block_num: int, volume: float, envelop: np.ndarray[np.float32], slide: np.ndarray[np.float32], sr: int = 64000):
    # Unknown
    UNIT_FREQ = 2 * np.pi / sr
    WindowSampling = np.arange(window_size)
    # Window
    window = np.hanning(window_size)
    # Total Length
    wave_length = window_size // 2 * block_num
    # Envelop Interp
    real_envelop = np.interp(np.arange(wave_length) / wave_length * envelop.size, np.arange(envelop.size), envelop).astype(np.float32)
    # Slide Interp
    real_freq = np.interp(np.arange(block_num) / block_num * slide.size, np.arange(slide.size), slide).astype(np.float32) * freq
    # Output
    buffer = np.zeros(window_size // 2 *( block_num + 1), dtype=np.float32)
    # Synth
    for offset in range(block_num):
        buffer[offset * window_size // 2: (offset + 2) * window_size // 2] += \
            window * (
                Amp.real * np.cos(UNIT_FREQ * WindowSampling * real_freq[offset]) +
                Amp.imag * np.sin(UNIT_FREQ * WindowSampling * real_freq[offset])
            ) * volume
    return buffer[window_size // 2:] * real_envelop



if __name__ == '__main__':
    import soundfile as sf
    from typing import Callable
    convert: Callable[[float], float] = lambda x : 2 ** (x / 12)
    slide = np.array([convert(0), convert(2), convert(-2), convert(2), convert(-2), convert(2), convert(-2), convert(0)], dtype=np.float32)
    envelop = np.array([1, 1, 1, 0.5, 0.2], dtype=np.float32)
    result = []
    result.append(SynthThread(400 * convert(0), 1, 64000 // 50 * 2, 50, 1, envelop, slide))
    result.append(SynthThread(400 * convert(2), 1, 64000 // 50 * 2, 50, 1, envelop, slide))
    result.append(SynthThread(400 * convert(4), 1, 64000 // 50 * 2, 50, 1, envelop, slide))
    result.append(SynthThread(400 * convert(5), 1, 64000 // 50 * 2, 50, 1, envelop, slide))
    result.append(SynthThread(400 * convert(7), 1, 64000 // 50 * 2, 50, 1, envelop, slide))
    result.append(SynthThread(400 * convert(9), 1, 64000 // 50 * 2, 50, 1, envelop, slide))
    result.append(SynthThread(400 * convert(11), 1, 64000 // 50 * 2, 50, 1, envelop, slide))
    result.append(SynthThread(400 * convert(12), 1, 64000 // 50 * 2, 50, 1, envelop, slide))
    output = np.concatenate(result)
    # Norm
    output /= np.max(output)
    sf.write('tmp/test2.wav', output, 64000, 'PCM_16')


