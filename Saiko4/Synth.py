#   Copyright 2024 Qiong-Mengzi
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# Core of Synthesis

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

def SynthThreadV2(freq: float, Amp: complex, window_size: int, each_offset: int, SynthPointNum: int, volume: float, envelop: np.ndarray[np.float32], slide: np.ndarray[np.float32], sr: int = 64000):
    # Unknown
    UNIT_FREQ = 2 * np.pi / sr
    WindowSampling = np.arange(window_size)
    # Window
    window = np.hanning(window_size)
    # TotalLength
    length = each_offset * SynthPointNum
    # Envelop Interp
    real_envelop = np.interp(np.arange(length) / length * envelop.size, np.arange(envelop.size), envelop).astype(np.float32)
    # Slide Interp
    real_freq = np.interp(np.arange(SynthPointNum) / SynthPointNum * slide.size, np.arange(slide.size), slide).astype(np.float32) * freq
    # Output
    buffer = np.zeros(length + window_size * 2, dtype=np.float32)
    # Synth:
    for offset in range(1, SynthPointNum + 1):
        buffer[offset * each_offset: offset * each_offset + window_size] += \
            window * (
                Amp.real * np.cos(UNIT_FREQ * (WindowSampling + offset * each_offset) * real_freq[offset - 1]) +
                Amp.imag * np.sin(UNIT_FREQ * (WindowSampling + offset * each_offset) * real_freq[offset - 1])
            ) * volume
    return buffer[each_offset: each_offset + length] * real_envelop
    

def SynthesisNote(
    freq: float,
    voice: tuple[tuple[float, complex], ...],
    volume: float,
    envelop: np.ndarray[np.float32],
    slide: np.ndarray[np.float32],
    window_size: int,
    block_num: int,
    offset_of_window: int = 4,
    sr: int = 64000
):
    #wave_length = window_size // 2 * block_num
    wave_length = (window_size // offset_of_window) * (block_num * offset_of_window)
    result = np.zeros(wave_length, np.float32)
    for v in voice:
        #result += SynthThread(freq * v[0], v[1], window_size, block_num, volume, envelop, slide, sr)
        result += SynthThreadV2(freq * v[0], v[1], window_size, window_size // 4, block_num * 4, volume, envelop, slide, sr)
    return result



