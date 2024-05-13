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

# ! Unfinished. DO NOT USE IT.

import sys
sys.path.append('.')

import os, json, time, struct
import numpy as np
from hashlib import blake2s
from typing import Any, Callable

import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox

from Saiko4.Ver import SAIKO_VERSION
import Saiko4.SheetV2 as SaikoSynthesizer

SKSHEET_EDITOR_VERSION:str = '0.0.1'

class EditorMain(object):
    def __init__(self):
        # File And Data
        self.opened_file: str = 'temp/untitled-' + blake2s(struct.pack('d', time.time()), digest_size=4).hexdigest() + '.sksheet'
        self.sksheet: dict[str, Any] = {}
        # Root Widget
        self.root = tk.Tk()
        self.root.title(f'Saiko Sheet Editor {SKSHEET_EDITOR_VERSION} (Saiko {SAIKO_VERSION}) [{self.opened_file}]')
        self.root.iconbitmap('assets/editor.ico')
        self.root.geometry('800x600')
        # Menu Create
        self.Menu()
        self.FileMenu()
        self.SynthMenu()
        # Others
        self.root.config(menu=self.menu)

    def Menu(self):
        self.menu = tk.Menu(self.root)

    def FileMenu(self):
        self.file_menu = tk.Menu(self.menu, tearoff=False)
        self.file_menu.add_command(label='Open', command=self.__OpenFileCB)
        self.file_menu.add_command(label='Save', command=self.__SaveFileCB)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Quit (May Lose Data)', command=self.root.quit, foreground='#800000')
        self.menu.add_cascade(label='File', menu=self.file_menu)
    
    def SynthMenu(self):
        self.synth_menu = tk.Menu(self.menu, tearoff=False)
        self.synth_menu.add_command(label='Option', command=self.__SynthOptCB)
        #self.synth_menu.add_command(label='Synth', command=)
        self.menu.add_cascade(label='Synth', menu=self.synth_menu)

    def __OpenFileCB(self):
        tmp_file_name = filedialog.askopenfilename(title='Choose a sheet', filetypes=[('Saiko Sheet', '.sksheet')])
        try:
            with open(tmp_file_name, 'r', encoding='utf-8') as f:
                self.sksheet = json.load(f)
        except:
            tkinter.messagebox.showerror('Saiko Sheet Editor Error', 'Error: Bad Format.')
        else:
            self.opened_file = tmp_file_name

    def __SaveFileCB(self):
        tmp_save_name = filedialog.asksaveasfilename(title='Choose saving path', filetypes=[('Saiko Sheet', '.sksheet')])
        with open(tmp_save_name, 'w', encoding='utf-8') as f:
            json.dump(self.sksheet, f)
        self.opened_file = tmp_save_name

    def __SynthOptCB(self):
        so_root = tk.Tk()
        so_root.title('Synthesis Options')
        so_root.iconbitmap('assets/editor.ico')
        so_root.geometry('400x300')
        so_nano = {}
        # A4
        so_nano['A4-Text'] = tk.Label(so_root, text='A4 Frequency')
        so_nano['A4-Text'].place(relheight=20/300, relwidth=90/400, relx=10/400, rely=7.5/300)
        so_nano['A4-Input'] = tk.Text(so_root, width=5)
        so_nano['A4-Input'].place(relheight=20/300, relwidth=90/400, relx=110/400, rely=7.5/300)
        so_nano['A4-Input'].insert('insert', '440')
        # SampleRate
        so_nano['sr-Text'] = tk.Label(so_root, text='SampleRate')
        so_nano['sr-Text'].place(relheight=20/300, relwidth=90/400, relx=10/400, rely=(7.5+20+7.5)/300)
        so_nano['sr-Input'] = tk.Text(so_root)
        so_nano['sr-Input'].place(relheight=20/300, relwidth=90/400, relx=110/400, rely=(7.5+20+7.5)/300)
        so_nano['sr-Input'].insert('insert', '64000')
        

        so_root.mainloop()


    def __call__(self):
        self.root.mainloop()

if __name__ == '__main__':
    Editor = EditorMain()
    Editor()

