#  Copyright 2024 Qiong-Mengzi
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# Main Of Saiko.
# These codes is very mess.

import json
from typing import Any, Callable
import numpy as np
import soundfile as sf

if __name__ == '__main__':
    from Synth import SynthesisNote
    from pitch import PITCH
    from Ver import SAIKO_VERSION
else:
    from .Synth import SynthesisNote
    from .pitch import PITCH
    from .Ver import SAIKO_VERSION

convert_pitch: Callable[[float], float] = lambda x : 2 ** (x / 12)

def ParseSkSheet(project_name: str, show_detail: bool = True):
    with open(project_name + '.sksheet', 'r', encoding='utf-8') as f:
        sksheet: dict[str, Any] = json.load(f)
    # Parse Saiko Sheet
    # #1 Collect All Voice
    if show_detail:
        print('Saiko Synthesis: Parsing Saiko Sheet...')
    VoiceDict: dict[str, tuple[tuple[float, complex], ...]] = {"none": ((1.0, 0.0j), )}
    if 'Saiko' not in sksheet:
        print('Saiko Synthesis: [WARNING] Unknown Saiko Version.')
    else:
        try:
            t_ver = tuple(SAIKO_VERSION.split('.'))
            t_sver = tuple(sksheet['Saiko'].split('.'))
            ver = int(t_ver[0]) * 1_000 + int(t_ver[1])
            sver = int(t_sver[0]) * 1_000 + int(t_sver[1])
            if ver < sver:
                print('Saiko Synthesis: [WARNING] The sheet version is larger than the synthesizer version, which may cause compatibility issues.')
            elif int(t_ver[0]) != int(t_sver[0]):
                print('Saiko Synthesis: [WARNING] The large version of the score is inconsistent with the large version of the synthesizer, which may cause compatibility issues.')
        except:
            print('Saiko Synthesis: [WARNING] Unknown Saiko Version Format.')
        finally:
            pass

    if 'Voice' in sksheet:
        voice = sksheet['Voice']
        for voice_name in voice:
            name: str = voice_name
            voice_raw_data: dict[str, str] = voice[voice_name]
            voice_data: list[tuple[float, complex]] = []
            for freq in voice_raw_data:
                voice_data.append((float(freq), complex(voice_raw_data[freq])))
            VoiceDict[name] = tuple(voice_data)
    # #2 Get All Envelop
    EnvelopDict: dict[str, list[float]] = {'default': [1.0]}
    EnvelopDict.update(sksheet.get('envelop', {}))
    # #3 Get All Slide
    SlideDict: dict[str, list[float]] = {'default': [1.0]}
    SlideDict.update(sksheet.get('slide', {}))
    # #4 Sound Info.
    A4_Frequency: int | float = sksheet.get('A4', 440.0)
    SampleRate: int = sksheet.get('sr', 64000)
    GlobalVolume: float = sksheet.get('volume', 1.0)
    # #5 Get Synthesis Arguments
    SynthArg: dict[str, Any] = sksheet.get('Synth', {})
    window_size: int = SynthArg.get("window-length", SampleRate // 200)
    offset_of_window: int = SynthArg.get("offset", 4)
    # #6 Read Sheet And Synthesis
    if show_detail:
        print('Saiko Synthesis: Loading Track Data...')
    Sheet: dict[str, list[Any]] = sksheet['Sheet']
    TrackNameList: list[str] = list(Sheet)
    AllTrackResult: list[np.ndarray[np.float32]] = []
    for TrackNameIndex in range(len(TrackNameList)):
        TrackData: list[dict[str, Any]] = Sheet[TrackNameList[TrackNameIndex]]
        TrackResult: list[np.ndarray[np.float32]] = []
        # Synth a Track
        for NoteIndex in range(len(TrackData)):
            if show_detail:
                print(f'Saiko Synthesis: Synthesis {TrackNameIndex}/{len(TrackNameList)} Tracks <{TrackNameList[TrackNameIndex]}>, {NoteIndex}/{len(TrackData)} Notes...', end=' '*16 + '\r')
            Note = TrackData[NoteIndex]
            # Get Note Length
            NoteLength = int(Note.get('length', float(Note.get('delay', 0.0)) * SampleRate))
            # Create Buffer
            NoteResult = np.zeros(NoteLength)
            # Set Envelop
            note_envelop: str | list[float] = Note.get('envelop', 'default')
            if isinstance(note_envelop, str):
                note_envelop = EnvelopDict.get(note_envelop, EnvelopDict['default'])
            # Set Slide
            note_slide: str | list[float] = Note.get('slide', 'default')
            if isinstance(note_slide, str):
                note_slide = SlideDict.get(note_slide, SlideDict['default'])
            # Set Local Volume
            volume = Note.get('volume', GlobalVolume)
            # Set Pitchs
            freqs: list[float] = Note.get('freqs', [A4_Frequency * convert_pitch(PITCH[pitch]) for pitch in Note.get('pitchs', [])])
            # Choose Voice
            voice = VoiceDict[Note.get('voice', 'none')]
            block_num = NoteLength // window_size * 2 + 2
            for freq in freqs:
                # Synthesis
                temp_note_result = SynthesisNote(freq, voice, volume, np.array(note_envelop, np.float32), np.array(note_slide, np.float32), window_size, block_num, offset_of_window, SampleRate)
                # Norm
                if SynthArg.get('norm', True):
                    max_sample = np.max(np.abs(temp_note_result))
                    if max_sample > 1.0:
                        temp_note_result /= max_sample
                # Remix Note
                NoteResult += temp_note_result[:NoteLength]
            # Add To Track
            TrackResult.append(NoteResult)
        # Cat All Notes
        temp_track_result = np.concatenate(TrackResult)
        # Add To Track Buffer
        AllTrackResult.append(temp_track_result)
    if show_detail:
        print('\nSaiko Synthesis: Remixing...')
    # Remix Tracks
    max_sound_length = 0
    for track in AllTrackResult:
        max_sound_length = max(max_sound_length, track.size)
    SoundResult = np.zeros(max_sound_length, np.float32)
    for track in AllTrackResult:
        SoundResult[:track.size] += track
    max_sound_sample = np.max(np.abs(SoundResult))
    # Norm
    if max_sound_sample > 1.0:
        SoundResult /= max_sound_sample
    if show_detail:
        print('Saiko Synthesis: Saving...')
    sf.write(project_name + '.wav', SoundResult, SampleRate, sksheet.get('PCM', 'PCM_16'))

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        ParseSkSheet(sys.argv[1])
    else:
        print('Saiko Synthesis: Usage: python Saiko4/Sheet.py <input-file-name-without-suffix-name>')

