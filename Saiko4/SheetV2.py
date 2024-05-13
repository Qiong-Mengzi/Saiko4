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

SKSHEET = dict[str, Any]

convert_pitch: Callable[[float], float] = lambda x : 2 ** (x / 12)
convert_pitch_ex: Callable[[np.ndarray], np.ndarray] = lambda x : np.power(2, x / 12)

class SaikoSynthesizer(object):
    def __init__(self, project_name: str, show_detail: bool = False):
        self.project_name = project_name
        self.show_detail = show_detail
        if self.show_detail:
            print('Saiko Synthesis: Parsing Saiko Sheet...')
        self.sksheet = self.OpenSkSheet(project_name)
        if not self.CheckVersion(self.sksheet) and self.show_detail:
            print('Saiko Synthesis: [WARNING] The large version of the score is inconsistent with the large version of the synthesizer, which may cause compatibility issues.')
        self.VoiceDict = self.CollectVoice(self.sksheet)
        self.EnvelopDict = self.GetEnvelop(self.sksheet)
        self.SlideDict = self.GetSlide(self.sksheet)
        self.GetSynthArg()

    @staticmethod
    def OpenSkSheet(project_name:str):
        with open(project_name + '.sksheet', 'r', encoding='utf-8') as f:
            sksheet: SKSHEET = json.load(f)
        return sksheet

    @staticmethod
    def CheckVersion(sksheet: SKSHEET):
        if 'Saiko' not in sksheet:
            return None
        else:
            try:
                t_ver = tuple(SAIKO_VERSION.split('.'))
                t_sver = tuple(sksheet['Saiko'].split('.'))
                ver = int(t_ver[0]) * 1_000 + int(t_ver[1])
                sver = int(t_sver[0]) * 1_000 + int(t_sver[1])
                if ver < sver:
                    return False
                elif int(t_ver[0]) != int(t_sver[0]):
                    return False
                else:
                    return True
            except:
                return None

    @staticmethod
    def CollectVoice(sksheet: SKSHEET):
        VoiceDict: dict[str, tuple[tuple[float, complex], ...]] = {"none": ((1.0, 0.0j), )}
        if 'Voice' in sksheet:
            voice = sksheet['Voice'] # What is the type of this?
            for voice_name in voice:
                name: str = voice_name
                voice_raw_data: dict[str, str] = voice[voice_name]
                voice_data: list[tuple[float, complex]] = []
                for freq in voice_raw_data:
                    voice_data.append((float(freq), complex(voice_raw_data[freq])))
                VoiceDict[name] = tuple(voice_data)
        return VoiceDict

    @staticmethod
    def GetEnvelop(sksheet: SKSHEET):
        EnvelopDict: dict[str, list[float]] = {'default': [1.0]}
        EnvelopDict.update(sksheet.get('envelop', {}))
        return EnvelopDict

    @staticmethod
    def GetSlide(sksheet: SKSHEET):
        SlideDict: dict[str, list[float]] = {'default': [1.0]}
        SlideDict.update(sksheet.get('slide', {}))
        return SlideDict
    
    def GetSynthArg(self):
        self.A4_Frequency: int | float = self.sksheet.get('A4', 440.0)
        self.SampleRate: int = self.sksheet.get('sr', 64000)
        self.GlobalVolume: float = self.sksheet.get('volume', 1.0)
        SynthArg: dict[str, Any] = self.sksheet.get('Synth', {})
        self.window_size: int = SynthArg.get("window-length", self.SampleRate // 200)
        self.offset_of_window: int = SynthArg.get("offset", 4)
        self.norm: bool = SynthArg.get('norm', True)
        self.SavingFormat: str = self.sksheet.get('PCM', 'PCM_16')
        self.BeatPerMinute: float | None = self.sksheet.get('bpm', None)
        if self.BeatPerMinute != None:
            print('Using {:.2} BPM.'.format(float(self.BeatPerMinute)))
            self.BeatPerMinute = self.SampleRate / self.BeatPerMinute * 60
        

    def GetNote(self, Note: dict[str, Any], local_track: dict[str, Any] = {}):
        # Get Note Length
        if self.BeatPerMinute != None:
            if 'length' in Note:
                NoteLength: int = Note['length']
            elif 'beat' in Note:
                NoteLength: int = int(Note['beat'] * self.BeatPerMinute)
            elif 'delay' in Note:
                NoteLength: int = int(Note['delay'] * self.SampleRate)
            else:
                NoteLength = 0
        else:
            NoteLength = int(Note.get('length', Note.get('delay', 0.0) * self.SampleRate))
        # Set Envelop
        note_envelop: str | list[float] = Note.get('envelop', local_track.get('envelop', 'default'))
        if isinstance(note_envelop, str):
            note_envelop = self.EnvelopDict.get(note_envelop, self.EnvelopDict['default'])
        # Set Slide
        note_slide: str | list[float] = Note.get('slide', local_track.get('slide', 'default'))
        if isinstance(note_slide, str):
            note_slide = self.SlideDict.get(note_slide, self.SlideDict['default'])
        # Set Local Volume
        volume: float = Note.get('volume', local_track.get('volume', self.GlobalVolume))
        # Set Pitchs
        freqs: list[float] = Note.get('freqs', [self.A4_Frequency * convert_pitch(PITCH[pitch]) for pitch in Note.get('pitchs', [])])
        # Choose Voice
        voice = self.VoiceDict.get(Note.get('voice', local_track.get('voice', 'none')), self.VoiceDict['none'])
        block_num = NoteLength // (self.window_size // self.offset_of_window) + 1
        return (NoteLength, freqs, voice, volume, np.array(note_envelop, np.float32), convert_pitch_ex(np.array(note_slide, np.float32)), self.window_size, block_num, self.offset_of_window, self.SampleRate)
    
    def SynthNote(self, Note: dict[str, Any], local_track: dict[str, Any] = {}):
        NoteArg = self.GetNote(Note, local_track)
        NoteResult = np.zeros(NoteArg[0], dtype=np.float32)
        for freq in NoteArg[1]:
            # Synthesis
            temp_note_result = SynthesisNote(freq, *NoteArg[2:])
            # Norm
            if self.norm:
                max_sample = np.max(np.abs(temp_note_result))
                if max_sample > 0.015625:
                    temp_note_result /= max_sample
                temp_note_result *= NoteArg[3]
            # Remix Note
            NoteResult += temp_note_result[:NoteArg[0]]
        return NoteResult
    
    def Synthesis(self):
        if self.show_detail:
            print('Saiko Synthesis: Loading Track Data...')
        # Saiko 4.1+ will use track-configuration.
        Sheet: dict[str, list[Any] | dict[str, list[dict[str, Any]] | str | float | Any]] = self.sksheet['Sheet']
        TrackNameList: list[str] = list(Sheet)
        AllTrackResult: list[np.ndarray[np.float32]] = [None] * len(TrackNameList)
        for TrackNameIndex in range(len(TrackNameList)):
            TrackData: list[dict[str, Any]] | dict[str, list[dict[str, Any]] | str | float | Any] = Sheet[TrackNameList[TrackNameIndex]]
            if isinstance(TrackData, list):
                TrackResult: list[np.ndarray[np.float32]] = [None] * len(TrackData) # Please ignore this error.
                # Synth a Track
                for NoteIndex in range(len(TrackData)):
                    if self.show_detail:
                        print(f'Saiko Synthesis: Synthesis {TrackNameIndex}/{len(TrackNameList)} Tracks <{TrackNameList[TrackNameIndex]}>, {NoteIndex}/{len(TrackData)} Notes...', end=' '*16 + '\r')
                    Note = TrackData[NoteIndex]
                    TrackResult[NoteIndex] = self.SynthNote(Note)
            else:
                TrackResult: list[np.ndarray[np.float32]] = [None] * len(TrackData['track'])
                # Synth a Track
                for NoteIndex in range(len(TrackData['track'])):
                    if self.show_detail:
                        print('Saiko Synthesis: Synthesis {0}/{1} Tracks <{2}>, {3}/{4} Notes...'.format(TrackNameIndex, len(TrackNameList), TrackNameList[TrackNameIndex], NoteIndex, len(TrackData['track'])), end=' '*16 + '\r')
                    Note = TrackData['track'][NoteIndex]
                    TrackResult[NoteIndex] = self.SynthNote(Note, TrackData)
            AllTrackResult[TrackNameIndex] = np.concatenate(TrackResult)
        return AllTrackResult
    
    def RemixTracks(self, AllTrackResult: list[np.ndarray[np.float32]]):
        # Remix Tracks
        max_sound_length = 0
        for track in AllTrackResult:
            max_sound_length = max(max_sound_length, track.size)
        SoundResult = np.zeros(max_sound_length, np.float32)
        if SoundResult.size == 0:
            return SoundResult
        for track in AllTrackResult:
            SoundResult[:track.size] += track
        max_sound_sample = np.max(np.abs(SoundResult))
        # Norm
        if max_sound_sample > 1.0:
            SoundResult /= max_sound_sample
        return SoundResult
    
    def SaveSound(self, SoundResult: np.ndarray[np.float32]):
        if self.show_detail:
            print('Saiko Synthesis: Saving...')
        sf.write(self.project_name + '.wav', SoundResult, self.SampleRate, self.SavingFormat)
    
    def PlaySound(self):
        try:
            import winsound
        except:
            print('Saiko Synthesis: [ERROR] Cannot Import `winsound` module. Playing the sound is not support yet.')
        else:
            print('Saiko Synthesis: Playing Result...')
            winsound.PlaySound(self.project_name + '.wav', winsound.SND_FILENAME or winsound.SND_NODEFAULT or winsound.SND_ASYNC)
            input('(Press Enter To Exit.)')

    def __call__(self, save: bool = True, play: bool = False):
        tracks = self.Synthesis()
        result = self.RemixTracks(tracks)
        if save:
            self.SaveSound(result)
        if play:
            self.PlaySound()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        sksynth = SaikoSynthesizer(sys.argv[1], show_detail=True)
        if len(sys.argv) == 3:
            if sys.argv[2] == '--play':
                sksynth(play=True)
            else:
                sksynth()
        else:
            sksynth()
    else:
        print('Saiko Synthesis: Usage: python Saiko4/Sheet.py <input-file-name-without-suffix-name>')




