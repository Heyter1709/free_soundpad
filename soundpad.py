import sys, os, json, threading, time, queue
from typing import Dict, List, Tuple, Optional

import numpy as np
import soundfile as sf
import sounddevice as sd
import keyboard

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QComboBox, QListWidgetItem,
    QScrollArea, QFrame, QFileDialog, QMessageBox, QDialog,
    QSystemTrayIcon, QMenu, QGridLayout, QSplitter, QLineEdit,
    QInputDialog, QTreeWidget, QTreeWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QLinearGradient, QFont,
    QIcon, QPixmap, QAction, QImage, QDrag, QRadialGradient, QCursor
)

# ─── CONFIG ──────────────────────────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".soundpad2_config.json")
SAMPLE_RATE = 44100
BLOCK_SIZE  = 2048

# ─── LANGUAGE ────────────────────────────────────────────────────────────────
LANG = "en"

_T = {
    "en": {
        "stop_all":"⏹  Stop All","settings":"⚙  Settings","add_sounds":"＋  Add Sounds",
        "search":"🔍  Search sounds…","pt_on":"🎤  Passthrough: ON","pt_off":"🎤  Passthrough: OFF",
        "virt_cable":"Virtual Cable (out):","mic":"Microphone (in):","all_sounds":"All Sounds",
        "library":"LIBRARY","new_folder":"New Folder","folder_name":"Folder name:",
        "rename":"✏  Rename","trim":"✂  Trim","delete_lib":"🗑  Delete from library",
        "rem_folder":"📤  Remove from folder","add_folder":"📁  Add to folder",
        "play":"▶  Play","volume":"🔊 Volume","hotkey":"⌨ Global Hotkey",
        "folder_hotkey":"📁 Folder Hotkey","clear_hk":"✕ Clear",
        "sel_sound":"Select a sound to see options","rename_dlg":"Rename Sound","new_name":"New name:",
        "ren_folder":"Rename Folder","del_folder":"Delete Folder",
        "del_folder_q":"Delete folder '{}'? Sounds stay in the library (their folder assignments will be removed).",
        "del_sound_q":"Remove '{}' from the library?","open_app":"Open SoundPad","quit":"Quit",
        "save":"  Save  ","cancel":"Cancel","preview":"▶  Preview","stop_btn":"⏹  Stop",
        "save_trim":"💾  Save Trim","glob_hk":"⚙  Global Hotkeys",
        "glob_hk_note":"These hotkeys work globally (even when minimized).",
        "next_trk":"⏭  Next Track","prev_trk":"⏮  Prev Track","stop_hk":"⏹  Stop All",
        "clr_hk":"Clear All Hotkeys","assign":"⌨  Assign","hold_keys":"🎹 Hold keys…",
        "language":"Language","no_folder":"(No folder)","yes":"Yes","no":"No",
        "drag_tip":"Drag sounds onto folders","no_sounds":"No sounds here.\nClick  ＋ Add Sounds  to get started.",
        "start":"Start","end":"End","length":"Length","audio_error":"Audio Error",
        "error":"Error","start_before_end":"Start must be before end",
        "save_trimmed":"Save trimmed file","wav_files":"WAV files (*.wav)",
        "audio_files":"Audio Files (*.wav *.mp3 *.ogg *.flac *.aiff *.aif);;All Files (*)",
        "select_audio":"Select audio files","note_hotkeys":"Note: hold keys then release to capture.",
        "folder_hk_tip":"Triggers only when this folder view is active.",
    },
    "ru": {
        "stop_all":"⏹  Стоп","settings":"⚙  Настройки","add_sounds":"＋  Добавить",
        "search":"🔍  Поиск…","pt_on":"🎤  Сквозной: ВКЛ","pt_off":"🎤  Сквозной: ВЫКЛ",
        "virt_cable":"Виртуальный кабель (вых):","mic":"Микрофон (вх):","all_sounds":"Все звуки",
        "library":"БИБЛИОТЕКА","new_folder":"Новая папка","folder_name":"Название папки:",
        "rename":"✏  Переименовать","trim":"✂  Обрезать","delete_lib":"🗑  Удалить из библиотеки",
        "rem_folder":"📤  Убрать из папки","add_folder":"📁  В папку",
        "play":"▶  Играть","volume":"🔊 Громкость","hotkey":"⌨ Глоб. клавиша",
        "folder_hotkey":"📁 Клавиша папки","clear_hk":"✕ Сброс",
        "sel_sound":"Выберите звук для настройки","rename_dlg":"Переименовать звук","new_name":"Новое имя:",
        "ren_folder":"Переименовать папку","del_folder":"Удалить папку",
        "del_folder_q":"Удалить папку '{}'? Звуки останутся в библиотеке (привязки к папке будут удалены).",
        "del_sound_q":"Удалить '{}' из библиотеки?","open_app":"Открыть SoundPad","quit":"Выйти",
        "save":"  Сохранить  ","cancel":"Отмена","preview":"▶  Предпросмотр","stop_btn":"⏹  Стоп",
        "save_trim":"💾  Сохранить","glob_hk":"⚙  Глобальные горячие клавиши",
        "glob_hk_note":"Работают даже когда приложение свёрнуто.",
        "next_trk":"⏭  Следующий","prev_trk":"⏮  Предыдущий","stop_hk":"⏹  Стоп всё",
        "clr_hk":"Сбросить все","assign":"⌨  Назначить","hold_keys":"🎹 Держите клавиши…",
        "language":"Язык","no_folder":"(Без папки)","yes":"Да","no":"Нет",
        "drag_tip":"Перетащите звуки в папку","no_sounds":"Нет звуков.\nНажмите  ＋ Добавить  для начала.",
        "start":"Начало","end":"Конец","length":"Длина","audio_error":"Ошибка аудио",
        "error":"Ошибка","start_before_end":"Начало должно быть раньше конца",
        "save_trimmed":"Сохранить обрезанный файл","wav_files":"WAV файлы (*.wav)",
        "audio_files":"Аудио файлы (*.wav *.mp3 *.ogg *.flac *.aiff *.aif);;Все файлы (*)",
        "select_audio":"Выберите аудио файлы","note_hotkeys":"Удерживайте клавиши, затем отпустите.",
        "folder_hk_tip":"Срабатывает только когда активен вид этой папки.",
    },
    "zh": {
        "stop_all":"⏹  全部停止","settings":"⚙  设置","add_sounds":"＋  添加音效",
        "search":"🔍  搜索音效…","pt_on":"🎤  直通: 开","pt_off":"🎤  直通: 关",
        "virt_cable":"虚拟音频线 (输出):","mic":"麦克风 (输入):","all_sounds":"所有音效",
        "library":"音效库","new_folder":"新建文件夹","folder_name":"文件夹名称:",
        "rename":"✏  重命名","trim":"✂  剪辑","delete_lib":"🗑  从库中删除",
        "rem_folder":"📤  从文件夹移除","add_folder":"📁  添加到文件夹",
        "play":"▶  播放","volume":"🔊 音量","hotkey":"⌨ 全局热键",
        "folder_hotkey":"📁 文件夹热键","clear_hk":"✕ 清除",
        "sel_sound":"选择音效查看选项","rename_dlg":"重命名音效","new_name":"新名称:",
        "ren_folder":"重命名文件夹","del_folder":"删除文件夹",
        "del_folder_q":"删除文件夹 '{}'？音效保留在库中（将移除对该文件夹的分配）。",
        "del_sound_q":"从库中删除 '{}'？","open_app":"打开音效板","quit":"退出",
        "save":"  保存  ","cancel":"取消","preview":"▶  预览","stop_btn":"⏹  停止",
        "save_trim":"💾  保存剪辑","glob_hk":"⚙  全局热键",
        "glob_hk_note":"即使应用最小化也可使用这些热键。",
        "next_trk":"⏭  下一首","prev_trk":"⏮  上一首","stop_hk":"⏹  全部停止",
        "clr_hk":"清除所有热键","assign":"⌨  分配","hold_keys":"🎹 按住按键…",
        "language":"语言","no_folder":"(无文件夹)","yes":"是","no":"否",
        "drag_tip":"拖动音效到文件夹","no_sounds":"没有音效。\n点击  ＋ 添加音效  开始。",
        "start":"开始","end":"结束","length":"长度","audio_error":"音频错误",
        "error":"错误","start_before_end":"开始必须早于结束",
        "save_trimmed":"保存剪辑文件","wav_files":"WAV 文件 (*.wav)",
        "audio_files":"音频文件 (*.wav *.mp3 *.ogg *.flac *.aiff *.aif);;所有文件 (*)",
        "select_audio":"选择音频文件","note_hotkeys":"按住按键然后松开以捕获。",
        "folder_hk_tip":"仅在该文件夹视图激活时触发。",
    },
    "de": {
        "stop_all":"⏹  Alles stoppen","settings":"⚙  Einstellungen","add_sounds":"＋  Töne hinzufügen",
        "search":"🔍  Töne suchen…","pt_on":"🎤  Durchleitung: AN","pt_off":"🎤  Durchleitung: AUS",
        "virt_cable":"Virtuelles Kabel (Aus):","mic":"Mikrofon (Ein):","all_sounds":"Alle Töne",
        "library":"BIBLIOTHEK","new_folder":"Neuer Ordner","folder_name":"Ordnername:",
        "rename":"✏  Umbenennen","trim":"✂  Zuschneiden","delete_lib":"🗑  Aus Bibliothek löschen",
        "rem_folder":"📤  Aus Ordner entfernen","add_folder":"📁  Zu Ordner hinzufügen",
        "play":"▶  Abspielen","volume":"🔊 Lautstärke","hotkey":"⌨ Glob. Taste",
        "folder_hotkey":"📁 Ordner-Taste","clear_hk":"✕ Löschen",
        "sel_sound":"Ton auswählen","rename_dlg":"Ton umbenennen","new_name":"Neuer Name:",
        "ren_folder":"Ordner umbenennen","del_folder":"Ordner löschen",
        "del_folder_q":"Ordner '{}' löschen? Töne bleiben in der Bibliothek (Zuordnungen werden entfernt).",
        "del_sound_q":"'{}' aus der Bibliothek entfernen?","open_app":"SoundPad öffnen","quit":"Beenden",
        "save":"  Speichern  ","cancel":"Abbrechen","preview":"▶  Vorschau","stop_btn":"⏹  Stopp",
        "save_trim":"💾  Schnitt speichern","glob_hk":"⚙  Globale Tastenkürzel",
        "glob_hk_note":"Funktionieren auch wenn die App minimiert ist.",
        "next_trk":"⏭  Nächster Titel","prev_trk":"⏮  Vorheriger Titel","stop_hk":"⏹  Alles stoppen",
        "clr_hk":"Alle löschen","assign":"⌨  Zuweisen","hold_keys":"🎹 Tasten halten…",
        "language":"Sprache","no_folder":"(Kein Ordner)","yes":"Ja","no":"Nein",
        "drag_tip":"Töne auf Ordner ziehen","no_sounds":"Keine Töne.\nKlicke  ＋ Töne hinzufügen  zum Starten.",
        "start":"Start","end":"Ende","length":"Länge","audio_error":"Audiofehler",
        "error":"Fehler","start_before_end":"Start muss vor Ende liegen",
        "save_trimmed":"Geschnittene Datei speichern","wav_files":"WAV-Dateien (*.wav)",
        "audio_files":"Audiodateien (*.wav *.mp3 *.ogg *.flac *.aiff *.aif);;Alle Dateien (*)",
        "select_audio":"Audiodateien auswählen","note_hotkeys":"Tasten halten, dann loslassen.",
        "folder_hk_tip":"Wirkt nur wenn die Ordneransicht aktiv ist.",
    },
}

def tr(key, *args):
    text = _T.get(LANG, _T["en"]).get(key, _T["en"].get(key, key))
    if args:
        text = text.format(*args)
    return text

# ─── TREE ITEM ROLES ─────────────────────────────────────────────────────────
ITEM_ALL    = "all"
ITEM_FOLDER = "folder"
ITEM_SOUND  = "sound"
ROLE_IDX    = Qt.ItemDataRole.UserRole
ROLE_TYPE   = Qt.ItemDataRole.UserRole + 1

# ─── THEME ───────────────────────────────────────────────────────────────────
class T:
    BG="#08080e"; BG2="#0d0d18"; BG3="#13131f"; CARD="#181826"; CARD2="#1e1e30"
    PANEL="#111120"; BORDER="#252540"; BORDER2="#353560"
    ACCENT="#3d7fff"; ACCENT2="#6fa0ff"; ACCD="#2255cc"
    CYAN="#00d4c8"; CYAND="#009e94"; GREEN="#00e070"; GREEND="#00aa55"
    RED="#ff3d5c"; REDD="#cc2040"; YELLOW="#ffc040"
    TEXT="#dde2f5"; TEXTD="#6870a0"; TEXTDD="#30305a"; WHITE="#ffffff"
    FOLDER_COLORS=["#3d7fff","#00d4c8","#ff6b40","#c86bff","#00e070","#ffc040","#ff3d5c"]

QSS = f"""
QWidget{{background:{T.BG};color:{T.TEXT};font-family:'Segoe UI','Ubuntu',sans-serif;font-size:13px;}}
QScrollBar:vertical{{background:transparent;width:5px;margin:0;}}
QScrollBar::handle:vertical{{background:{T.BORDER2};border-radius:2px;min-height:24px;}}
QScrollBar::handle:vertical:hover{{background:{T.ACCENT};}}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{{background:transparent;}}
QScrollBar:horizontal{{background:transparent;height:5px;margin:0;}}
QScrollBar::handle:horizontal{{background:{T.BORDER2};border-radius:2px;min-width:24px;}}
QScrollBar::handle:horizontal:hover{{background:{T.ACCENT};}}
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal{{width:0;}}
QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal{{background:transparent;}}
QComboBox{{background:{T.BG3};border:1px solid {T.BORDER};border-radius:6px;padding:5px 10px;color:{T.TEXT};font-size:12px;}}
QComboBox:hover{{border-color:{T.ACCENT};}}
QComboBox::drop-down{{border:none;width:20px;}}
QComboBox::down-arrow{{width:0;height:0;border-left:4px solid transparent;border-right:4px solid transparent;border-top:5px solid {T.TEXTD};}}
QComboBox QAbstractItemView{{background:{T.BG3};border:1px solid {T.BORDER2};selection-background-color:{T.ACCENT};outline:none;padding:2px;}}
QSlider::groove:horizontal{{background:{T.BG3};height:3px;border-radius:1px;}}
QSlider::handle:horizontal{{background:{T.ACCENT2};width:13px;height:13px;margin:-5px 0;border-radius:6px;border:1px solid {T.ACCD};}}
QSlider::handle:horizontal:hover{{background:{T.WHITE};}}
QSlider::sub-page:horizontal{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {T.ACCD},stop:1 {T.ACCENT2});border-radius:1px;}}
QLineEdit{{background:{T.BG3};border:1px solid {T.ACCENT};border-radius:6px;padding:4px 10px;color:{T.TEXT};font-size:13px;}}
QToolTip{{background:{T.CARD2};color:{T.TEXT};border:1px solid {T.BORDER2};border-radius:5px;padding:5px 9px;font-size:12px;}}
QTreeWidget{{background:transparent;border:none;outline:none;}}
QTreeWidget::item{{padding:4px 6px;border-radius:5px;margin:1px 3px;color:{T.TEXTD};}}
QTreeWidget::item:hover{{background:{T.CARD};color:{T.TEXT};}}
QTreeWidget::item:selected{{background:{T.CARD2};color:{T.TEXT};}}
QTreeWidget::branch{{background:transparent;}}
"""

# ─── DATA CLASSES ────────────────────────────────────────────────────────────
class Sound:
    def __init__(self, name, path, keybind=None, keybind_raw=None,
                 volume=1.0, start_sec=0.0, end_sec=-1.0,
                 folder_assignments: Optional[Dict[str, Dict]] = None):
        self.name = name
        self.path = path
        self.keybind = keybind
        self.keybind_raw = keybind_raw
        self.volume = volume
        self.start_sec = start_sec
        self.end_sec = end_sec
        self.folder_assignments = folder_assignments if folder_assignments is not None else {}

    def has_folder(self, folder: str) -> bool:
        return folder in self.folder_assignments

    def add_folder(self, folder: str):
        if folder not in self.folder_assignments:
            self.folder_assignments[folder] = {'keybind': None, 'keybind_raw': None}

    def remove_folder(self, folder: str):
        if folder in self.folder_assignments:
            del self.folder_assignments[folder]

    def get_folder_hotkey(self, folder: str) -> Tuple[Optional[str], Optional[str]]:
        data = self.folder_assignments.get(folder, {})
        return data.get('keybind'), data.get('keybind_raw')

    def set_folder_hotkey(self, folder: str, display: Optional[str], raw: Optional[str]):
        if folder not in self.folder_assignments:
            self.folder_assignments[folder] = {}
        self.folder_assignments[folder]['keybind'] = display
        self.folder_assignments[folder]['keybind_raw'] = raw

class AppSettings:
    def __init__(self):
        self.hotkey_next_display=""; self.hotkey_next_raw=""
        self.hotkey_prev_display=""; self.hotkey_prev_raw=""
        self.hotkey_stop_display=""; self.hotkey_stop_raw=""
        self.language="en"

# ─── AUDIO ROUTER ────────────────────────────────────────────────────────────
class AudioRouter:
    def __init__(self):
        self.virtual_device=None; self.mic_device=None
        self.passthrough_active=False
        self._mic_stream=None; self._out_stream=None
        self._sfx_buf=np.zeros((0,2),dtype="float32")
        self._sfx_lock=threading.Lock()
        self._active_plays={}; self._play_lock=threading.Lock()
        # Serialise stop+play sequences so rapid switches don't race
        self._play_serial_lock = threading.Lock()

    def get_output_devices(self):
        return[(i,d["name"])for i,d in enumerate(sd.query_devices())if d["max_output_channels"]>0]

    def get_input_devices(self):
        return[(i,d["name"])for i,d in enumerate(sd.query_devices())if d["max_input_channels"]>0]

    def auto_select_devices(self):
        devs=sd.query_devices()
        kw=['cable input','virtual audio cable','vb-audio','voicemeeter','virtual cable','vac']
        cable=None
        for i,d in enumerate(devs):
            if d["max_output_channels"]>0 and any(k in d["name"].lower()for k in kw):
                cable=i; break
        try: default_in=sd.default.device[0]
        except: default_in=None
        if default_in is None or default_in<0:
            for i,d in enumerate(devs):
                if d["max_input_channels"]>0: default_in=i; break
        return cable,default_in

    @staticmethod
    def _soft_limit(out):
        thr=0.82; ceil=1.0; ab=np.abs(out); mask=ab>thr
        if np.any(mask):
            kr=ceil-thr
            out[mask]=(np.sign(out[mask])*(thr+kr*np.tanh((ab[mask]-thr)/kr)))
        return out

    def start_passthrough(self):
        if self.passthrough_active: return
        if self.virtual_device is None or self.mic_device is None:
            raise RuntimeError("Devices not selected.")
        with self._sfx_lock: self._sfx_buf=np.zeros((0,2),dtype="float32")
        self._mic_q=queue.Queue(maxsize=6)
        def _mic_cb(indata,frames,ti,status):
            data=indata[:,0:1].repeat(2,axis=1).astype("float32",copy=False)
            if self._mic_q.full():
                try: self._mic_q.get_nowait()
                except: pass
            try: self._mic_q.put_nowait(data)
            except: pass
        def _out_cb(outdata,frames,ti,status):
            out=np.zeros((frames,2),dtype="float32")
            collected=0
            while collected<frames:
                try:
                    blk=self._mic_q.get_nowait(); n=min(frames-collected,len(blk))
                    out[collected:collected+n]+=blk[:n]*0.85; collected+=n
                except: break
            with self._sfx_lock:
                n=min(frames,len(self._sfx_buf))
                if n>0: out[:n]+=self._sfx_buf[:n]; self._sfx_buf=self._sfx_buf[n:]
            self._soft_limit(out); outdata[:]=out
        try:
            self._mic_stream=sd.InputStream(device=self.mic_device,channels=1,
                samplerate=SAMPLE_RATE,blocksize=BLOCK_SIZE,dtype="float32",latency='low',callback=_mic_cb)
            self._out_stream=sd.OutputStream(device=self.virtual_device,channels=2,
                samplerate=SAMPLE_RATE,blocksize=BLOCK_SIZE,dtype="float32",latency='high',callback=_out_cb)
            self._mic_stream.start(); self._out_stream.start()
            self.passthrough_active=True
        except Exception as e:
            self._close_streams(); raise RuntimeError(f"Stream error: {e}")

    def _close_streams(self):
        for attr in('_mic_stream','_out_stream'):
            s=getattr(self,attr,None)
            if s:
                try: s.stop(); s.close()
                except: pass
                setattr(self,attr,None)

    def stop_passthrough(self):
        self.passthrough_active=False; self._close_streams()

    def set_output_device(self,d): self.virtual_device=d
    def set_input_device(self,d): self.mic_device=d

    def play_sound(self, path, volume=1.0, start_sec=0.0, end_sec=-1.0):
        """Stop any existing play of this path, then start a new one."""
        with self._play_lock:
            if path in self._active_plays:
                self._active_plays[path].set()
        stop_evt = threading.Event()
        t = threading.Thread(
            target=self._play_thread,
            args=(path, volume, start_sec, end_sec, stop_evt),
            daemon=True
        )
        t.start()
        with self._play_lock:
            self._active_plays[path] = stop_evt
        return stop_evt

    def _load_sound(self,path,volume,start_sec,end_sec):
        data,sr=sf.read(path,dtype="float32",always_2d=True)
        if data.shape[1]==1: data=np.repeat(data,2,axis=1)
        elif data.shape[1]>2: data=data[:,:2]
        if sr!=SAMPLE_RATE:
            n_out=int(round(len(data)*SAMPLE_RATE/sr))
            xs_old=np.linspace(0,len(data)-1,len(data)); xs_new=np.linspace(0,len(data)-1,n_out)
            data=np.column_stack([np.interp(xs_new,xs_old,data[:,ch])for ch in range(2)]).astype("float32")
        total=len(data)
        s=max(0,int(start_sec*SAMPLE_RATE))if start_sec>0 else 0
        e=int(end_sec*SAMPLE_RATE)if end_sec>0 else total
        e=max(s+1,min(e,total)); segment=data[s:e]*volume
        peak=np.max(np.abs(segment))
        if peak>0.95: segment=segment*(0.95/peak)
        return segment.astype("float32")

    def _play_thread(self, path, volume, start_sec, end_sec, stop_evt):
        try:
            # Load audio first (can be slow for large files)
            data = self._load_sound(path, volume, start_sec, end_sec)

            # Bail out immediately if we were already cancelled
            if stop_evt.is_set():
                return

            if self.passthrough_active:
                with self._sfx_lock:
                    self._sfx_buf = (
                        np.vstack([self._sfx_buf, data])
                        if len(self._sfx_buf) else data.copy()
                    )
                dur = len(data) / SAMPLE_RATE
                deadline = time.monotonic() + dur + 0.2
                while time.monotonic() < deadline and not stop_evt.is_set():
                    time.sleep(0.05)
                if stop_evt.is_set():
                    with self._sfx_lock:
                        self._sfx_buf = np.zeros((0, 2), dtype="float32")
            else:
                # One final check before touching the audio device so a rapid
                # stop+play cycle cannot sneak a stale play through.
                if stop_evt.is_set():
                    return
                dev = self.virtual_device
                try:
                    if dev is not None:
                        sd.play(data, SAMPLE_RATE, device=dev, blocking=False)
                    else:
                        sd.play(data, SAMPLE_RATE, blocking=False)
                except Exception as ex:
                    print(f"[AudioRouter] sd.play error: {ex}")
                    return
                dur = len(data) / SAMPLE_RATE
                t0 = time.monotonic()
                while not stop_evt.is_set() and (time.monotonic() - t0) < dur:
                    time.sleep(0.05)
                if stop_evt.is_set():
                    try:
                        sd.stop()
                    except Exception:
                        pass
        except Exception as ex:
            print(f"[AudioRouter] play error: {ex}")
        finally:
            with self._play_lock:
                if self._active_plays.get(path) is stop_evt:
                    del self._active_plays[path]

    def stop_sound_by_path(self, path):
        with self._play_lock:
            ev = self._active_plays.get(path)
        if ev:
            ev.set()

    def stop_all_sounds(self):
        with self._play_lock:
            evs = list(self._active_plays.values())
            self._active_plays.clear()
        for ev in evs:
            ev.set()
        with self._sfx_lock:
            self._sfx_buf = np.zeros((0, 2), dtype="float32")
        if not self.passthrough_active:
            try:
                sd.stop()
            except Exception:
                pass

    def stop_all_and_wait(self, timeout=0.12):
        """Stop all sounds then wait briefly so the audio device fully releases."""
        self.stop_all_sounds()
        time.sleep(timeout)

    def is_playing(self, path):
        with self._play_lock:
            ev = self._active_plays.get(path)
        return ev is not None and not ev.is_set()

# ─── WAVEFORM WIDGET ─────────────────────────────────────────────────────────
class WaveformWidget(QWidget):
    positionChanged=pyqtSignal(float)
    def __init__(self,parent=None):
        super().__init__(parent); self.setMinimumHeight(90)
        self.peaks=[]; self.start_ratio=0.0; self.end_ratio=1.0
        self.playhead_ratio=0.0; self._dragging=None; self._hover_x=-1; self._total_dur=1.0
        self.setMouseTracking(True); self.setCursor(Qt.CursorShape.CrossCursor)

    def set_peaks(self,peaks,total): self.peaks=peaks; self._total_dur=max(total,0.001); self.update()
    def set_region(self,s,e): self.start_ratio=max(0.0,min(1.0,s)); self.end_ratio=max(0.0,min(1.0,e)); self.update()
    def set_playhead(self,r): self.playhead_ratio=r; self.update()

    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=self.width(),self.height(); cx=h//2
        bg=QLinearGradient(0,0,0,h); bg.setColorAt(0,QColor(T.BG3)); bg.setColorAt(1,QColor(T.BG2))
        p.fillRect(0,0,w,h,QBrush(bg))
        sx=int(self.start_ratio*w); ex=int(self.end_ratio*w)
        reg=QColor(T.ACCENT); reg.setAlpha(20); p.fillRect(sx,0,ex-sx,h,reg)
        if self.peaks:
            bar_w=max(1,w//len(self.peaks))
            for i,amp in enumerate(self.peaks):
                x=i*w//len(self.peaks); bh=max(2,int(amp*(h-10))); y=cx-bh//2
                ratio=i/len(self.peaks)
                if self.start_ratio<=ratio<=self.end_ratio: col=QColor(T.ACCENT2); col.setAlpha(200)
                else: col=QColor(T.TEXTDD); col.setAlpha(160)
                p.fillRect(x,y,max(1,bar_w-1),bh,col)
        p.setPen(QPen(QColor(T.GREEN),2)); p.drawLine(sx,0,sx,h)
        p.setBrush(QColor(T.GREEN)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(sx-5,3,10,10)
        p.setPen(QPen(QColor(T.RED),2)); p.drawLine(ex,0,ex,h)
        p.setBrush(QColor(T.RED)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(ex-5,3,10,10)
        if self.playhead_ratio>0:
            px=int(self.playhead_ratio*w); p.setPen(QPen(QColor(T.YELLOW),2)); p.drawLine(px,0,px,h)
        if self._hover_x>=0:
            p.setPen(QPen(QColor(T.WHITE),1,Qt.PenStyle.DotLine)); p.drawLine(self._hover_x,0,self._hover_x,h)
        p.setFont(QFont("Segoe UI",8)); p.setPen(QColor(T.TEXTD))
        t_s=self.start_ratio*self._total_dur; t_e=self.end_ratio*self._total_dur
        p.drawText(sx+3,h-4,f"{t_s:.2f}s"); p.drawText(max(2,ex-42),h-4,f"{t_e:.2f}s")

    def mousePressEvent(self,e):
        x=e.position().x(); w=max(1,self.width())
        if abs(x-self.start_ratio*w)<10: self._dragging='start'
        elif abs(x-self.end_ratio*w)<10: self._dragging='end'
        else: self.positionChanged.emit(x/w)

    def mouseMoveEvent(self,e):
        x=e.position().x(); w=max(1,self.width()); self._hover_x=int(x)
        if self._dragging:
            r=max(0.0,min(1.0,x/w))
            if self._dragging=='start'and r<self.end_ratio-0.01: self.start_ratio=r; self.positionChanged.emit(-1.0)
            elif self._dragging=='end'and r>self.start_ratio+0.01: self.end_ratio=r; self.positionChanged.emit(-2.0)
        self.update()

    def mouseReleaseEvent(self,e): self._dragging=None
    def leaveEvent(self,e): self._hover_x=-1; self.update()

# ─── TRIM EDITOR ─────────────────────────────────────────────────────────────
class TrimEditor(QDialog):
    saved=pyqtSignal(object)
    def __init__(self,sound,parent=None):
        super().__init__(parent); self.sound=sound; self.data=None; self.sr=None; self.total=0
        self.start_sec=max(0.0,sound.start_sec); self.end_sec=sound.end_sec if sound.end_sec>0 else None
        self._ph_timer=QTimer(self); self._ph_timer.setInterval(50); self._ph_timer.timeout.connect(self._update_playhead)
        self._ph_start_time=None; self._ph_start_sec=0
        self.setWindowTitle(f"Trim — {sound.name}"); self.setMinimumSize(820,500); self.setModal(True)
        self.setStyleSheet(QSS+f"QDialog{{background:{T.BG};}}")
        self._load(); self._build()

    def _load(self):
        try:
            self.data,self.sr=sf.read(self.sound.path,dtype="float32",always_2d=True)
            if self.data.shape[1]==1: self.data=np.repeat(self.data,2,axis=1)
            self.total=len(self.data)/self.sr
            if self.end_sec is None or self.end_sec>self.total: self.end_sec=self.total
            if self.start_sec>self.end_sec: self.start_sec=0.0
        except Exception as e: QMessageBox.critical(self,tr("error"),str(e)); self.close()

    def _build(self):
        lay=QVBoxLayout(self); lay.setSpacing(14); lay.setContentsMargins(24,20,24,20)
        title=QLabel(f"✂  {self.sound.name}"); title.setFont(QFont("Segoe UI",14,QFont.Weight.Bold))
        title.setStyleSheet(f"color:{T.ACCENT2};"); lay.addWidget(title)
        self.wave=WaveformWidget(); self.wave.setMinimumHeight(110)
        self.wave.positionChanged.connect(self._on_wave)
        if self.data is not None:
            self.wave.set_peaks(self._compute_peaks(400),self.total)
            self.wave.set_region(self.start_sec/self.total,self.end_sec/self.total)
        lay.addWidget(self.wave)
        self.seek=QSlider(Qt.Orientation.Horizontal); self.seek.setRange(0,1000)
        self.seek.sliderMoved.connect(lambda v:self.wave.set_playhead(v/1000)); lay.addWidget(self.seek)
        info=QHBoxLayout(); self.lbl_s=QLabel(); self.lbl_e=QLabel(); self.lbl_d=QLabel()
        for l in[self.lbl_s,self.lbl_e,self.lbl_d]: l.setFont(QFont("Segoe UI",10)); info.addWidget(l); info.addSpacing(20)
        info.addStretch(); lay.addLayout(info); self._update_labels()
        ctrl=QHBoxLayout(); ctrl.setSpacing(16)
        ctrl.addWidget(QLabel(tr("start")+":"))
        self.sl_s=QSlider(Qt.Orientation.Horizontal); self.sl_s.setRange(0,10000)
        self.sl_s.setValue(int(self.start_sec/self.total*10000)); self.sl_s.sliderMoved.connect(self._start_moved); ctrl.addWidget(self.sl_s,2)
        ctrl.addSpacing(20); ctrl.addWidget(QLabel(tr("end")+":"))
        self.sl_e=QSlider(Qt.Orientation.Horizontal); self.sl_e.setRange(0,10000)
        self.sl_e.setValue(int(self.end_sec/self.total*10000)); self.sl_e.sliderMoved.connect(self._end_moved); ctrl.addWidget(self.sl_e,2)
        lay.addLayout(ctrl)
        btns=QHBoxLayout()
        for text,col,fn in[(tr("preview"),T.ACCENT,self._preview),(tr("stop_btn"),T.RED,self._stop_preview),(tr("save_trim"),T.GREEN,self._save),(tr("cancel"),T.BG3,self.close)]:
            b=self._btn(text,col,fn); btns.addWidget(b)
        lay.addLayout(btns)

    def _btn(self,text,color,fn):
        b=QPushButton(text); b.setCursor(Qt.CursorShape.PointingHandCursor); b.setFixedHeight(36)
        b.setStyleSheet(f"QPushButton{{background:{color};color:white;border:none;border-radius:7px;padding:0 18px;font-size:12px;font-weight:bold;}}QPushButton:hover{{background:{color}cc;}}")
        b.clicked.connect(fn); return b

    def _compute_peaks(self,n=400):
        total=len(self.data); step=max(1,total//n)
        return[float(np.max(np.abs(self.data[i:i+step])))for i in range(0,total,step)]

    def _update_labels(self):
        self.lbl_s.setText(f"<span style='color:{T.GREEN}'>▶ {tr('start')}: <b>{self.start_sec:.3f}s</b></span>")
        self.lbl_e.setText(f"<span style='color:{T.RED}'>■ {tr('end')}: <b>{self.end_sec:.3f}s</b></span>")
        self.lbl_d.setText(f"<span style='color:{T.ACCENT2}'>⏱ {tr('length')}: <b>{self.end_sec-self.start_sec:.3f}s</b></span>")

    def _start_moved(self,v):
        self.start_sec=max(0.0,min(v/10000*self.total,self.end_sec-0.05))
        self.wave.set_region(self.start_sec/self.total,self.end_sec/self.total); self._update_labels()

    def _end_moved(self,v):
        self.end_sec=max(self.start_sec+0.05,min(v/10000*self.total,self.total))
        self.wave.set_region(self.start_sec/self.total,self.end_sec/self.total); self._update_labels()

    def _on_wave(self,r):
        if r==-1.0:
            self.start_sec=self.wave.start_ratio*self.total; self.sl_s.setValue(int(self.wave.start_ratio*10000))
        elif r==-2.0:
            self.end_sec=self.wave.end_ratio*self.total; self.sl_e.setValue(int(self.wave.end_ratio*10000))
        else:
            self.start_sec=r*self.total; self.sl_s.setValue(int(r*10000))
            self.wave.set_region(self.start_sec/self.total,self.end_sec/self.total)
        self._update_labels()

    def _preview(self):
        self._stop_preview()
        if self.data is None: return
        seg=self.data[int(self.start_sec*self.sr):int(self.end_sec*self.sr)]
        self._ph_start_sec=self.start_sec; self._ph_start_time=time.time(); self._ph_timer.start()
        threading.Thread(target=lambda:sd.play(seg,self.sr,blocking=True),daemon=True).start()

    def _stop_preview(self):
        sd.stop(); self._ph_timer.stop(); self.wave.set_playhead(0)

    def _update_playhead(self):
        if self._ph_start_time is None: return
        elapsed=time.time()-self._ph_start_time; sec=self._ph_start_sec+elapsed
        if sec>=self.end_sec: self._ph_timer.stop(); self.wave.set_playhead(0); return
        self.wave.set_playhead(sec/self.total); self.seek.setValue(int((sec/self.total)*1000))

    def _save(self):
        if self.start_sec>=self.end_sec: QMessageBox.warning(self,tr("error"),tr("start_before_end")); return
        path,_=QFileDialog.getSaveFileName(self,tr("save_trimmed"),f"trimmed_{os.path.basename(self.sound.path)}",tr("wav_files"))
        if not path: return
        seg=self.data[int(self.start_sec*self.sr):int(self.end_sec*self.sr)]; sf.write(path,seg,self.sr)
        self.sound.path=path; self.sound.start_sec=0.0; self.sound.end_sec=-1.0
        self.sound.name=os.path.splitext(os.path.basename(path))[0]; self.saved.emit(self.sound); self.accept()

    def closeEvent(self,e): self._stop_preview(); super().closeEvent(e)

# ─── HOTKEY CAPTURE ──────────────────────────────────────────────────────────
class HotkeyCapture(QWidget):
    captured=pyqtSignal(str,str); _upd_disp=pyqtSignal(str)
    def __init__(self,current="",parent=None):
        super().__init__(parent); self._listening=False; self._pressed=set(); self._seq=[]; self._running=False
        lay=QHBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(6)
        self.key_lbl=QLabel(current if current else f"— {tr('assign')} —")
        self.key_lbl.setStyleSheet(self._lbl_style(False)); self.key_lbl.setMinimumWidth(120); lay.addWidget(self.key_lbl)
        self.btn_assign=QPushButton(tr("assign")); self.btn_assign.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_assign.setFixedHeight(28)
        self.btn_assign.setStyleSheet(f"QPushButton{{background:{T.ACCENT};color:white;border:none;border-radius:5px;padding:0 10px;font-size:11px;font-weight:bold;}}QPushButton:hover{{background:{T.ACCENT2};}}")
        self.btn_assign.clicked.connect(self._start); lay.addWidget(self.btn_assign)
        self.btn_cancel=QPushButton("✕"); self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setFixedSize(28,28); self.btn_cancel.setVisible(False)
        self.btn_cancel.setStyleSheet(f"QPushButton{{background:{T.BG3};color:{T.RED};border:1px solid {T.BORDER};border-radius:5px;font-weight:bold;}}QPushButton:hover{{background:{T.RED};color:white;}}")
        self.btn_cancel.clicked.connect(self._stop); lay.addWidget(self.btn_cancel)
        self._upd_disp.connect(self._on_upd)

    def _lbl_style(self,active):
        if active: return f"background:{T.ACCD};color:{T.WHITE};border:1px solid {T.ACCENT2};border-radius:5px;padding:3px 10px;font-size:11px;font-weight:bold;"
        return f"background:{T.BG3};color:{T.ACCENT2};border:1px solid {T.BORDER};border-radius:5px;padding:3px 10px;font-size:11px;font-weight:bold;"

    def set_hotkey(self,display):
        self.key_lbl.setText(display if display else f"— {tr('assign')} —"); self.key_lbl.setStyleSheet(self._lbl_style(False))

    def _start(self):
        if self._listening: return
        self._listening=True; self._pressed.clear(); self._seq.clear()
        self.key_lbl.setText(tr("hold_keys")); self.key_lbl.setStyleSheet(self._lbl_style(True))
        self.btn_assign.setVisible(False); self.btn_cancel.setVisible(True)
        self._running=True; threading.Thread(target=self._hook_loop,daemon=True).start()

    def _stop(self):
        self._running=False; self._listening=False
        self.btn_assign.setVisible(True); self.btn_cancel.setVisible(False)
        self.key_lbl.setStyleSheet(self._lbl_style(False))

    def _norm(self,key): return key.replace('left ','').replace('right ','')

    def _hook_loop(self):
        # Используем scan codes — они не зависят от раскладки клавиатуры.
        _pressed_sc: set  = set()   # scan codes зажатых клавиш
        _seq_sc:     list = []      # порядок scan codes (для raw-строки)
        _seq_names:  list = []      # названия клавиш (для отображения)

        def handler(ev):
            if not self._running:
                return
            key = ev.name.lower() if ev.name else ""
            if key == 'esc':
                self._running = False
                self._upd_disp.emit(f"— {tr('assign')} —")
                return
            sc = ev.scan_code
            if not sc:      # игнорируем события без валидного scan code
                return
            norm = self._norm(key) if key else str(sc)

            if ev.event_type == 'down':
                if sc not in _pressed_sc:
                    _pressed_sc.add(sc)
                    _seq_sc.append(sc)
                    _seq_names.append(norm)
                self._upd_disp.emit("🎹 " + " + ".join(k.upper() for k in _seq_names))
            elif ev.event_type == 'up':
                if sc in _pressed_sc:
                    _pressed_sc.remove(sc)
                if not _pressed_sc and _seq_sc and self._running:
                    # raw = combo из scan codes, напр. "57+30"
                    raw  = "+".join(str(s) for s in _seq_sc)
                    disp = " + ".join(k.upper() for k in _seq_names)
                    self._running = False
                    self._upd_disp.emit(disp)
                    self.captured.emit(disp, raw)

        keyboard.hook(handler)
        while self._running:
            time.sleep(0.01)
        keyboard.unhook(handler)
        if self._listening:
            self._listening = False
            self.btn_assign.setVisible(True)
            self.btn_cancel.setVisible(False)

    def _on_upd(self,text):
        self.key_lbl.setText(text); active=self._running or self._listening
        self.key_lbl.setStyleSheet(self._lbl_style(active))
        if not active: self.btn_assign.setVisible(True); self.btn_cancel.setVisible(False)

# ─── SETTINGS DIALOG ─────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    saved=pyqtSignal(object); lang_changed=pyqtSignal(str)
    def __init__(self,settings:AppSettings,parent=None):
        super().__init__(parent); self.s=settings
        self.setWindowTitle(tr("settings")); self.setMinimumWidth(540); self.setModal(True)
        self.setStyleSheet(QSS+f"QDialog{{background:{T.BG2};}}")
        self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setSpacing(18); lay.setContentsMargins(28,24,28,24)
        title=QLabel(tr("glob_hk")); title.setFont(QFont("Segoe UI",15,QFont.Weight.Bold))
        title.setStyleSheet(f"color:{T.ACCENT2};border:none;"); lay.addWidget(title)
        sep=QFrame(); sep.setFixedHeight(1); sep.setStyleSheet(f"background:{T.BORDER};"); lay.addWidget(sep)
        note=QLabel(tr("glob_hk_note")); note.setStyleSheet(f"color:{T.TEXTD};font-size:11px;"); lay.addWidget(note)

        grid_w=QWidget(); grid=QGridLayout(grid_w)
        grid.setSpacing(12); grid.setContentsMargins(0,0,0,0)
        def mk_row(lbl_txt,display,row):
            lbl=QLabel(lbl_txt); lbl.setStyleSheet(f"color:{T.TEXT};font-size:12px;font-weight:bold;")
            grid.addWidget(lbl,row,0); hk=HotkeyCapture(display,self); grid.addWidget(hk,row,1); return hk
        self.hk_next=mk_row(tr("next_trk"),self.s.hotkey_next_display,0)
        self.hk_prev=mk_row(tr("prev_trk"),self.s.hotkey_prev_display,1)
        self.hk_stop=mk_row(tr("stop_hk"),self.s.hotkey_stop_display,2)
        lay.addWidget(grid_w)

        lang_row=QHBoxLayout()
        lang_lbl=QLabel(f"🌐  {tr('language')}:"); lang_lbl.setStyleSheet(f"color:{T.TEXT};font-size:12px;font-weight:bold;")
        lang_row.addWidget(lang_lbl)
        self.lang_cb=QComboBox(); self.lang_cb.setFixedWidth(200)
        langs=[("en","English"),("ru","Русский"),("zh","中文"),("de","Deutsch")]
        for code,name in langs: self.lang_cb.addItem(name,code)
        for i in range(self.lang_cb.count()):
            if self.lang_cb.itemData(i)==self.s.language: self.lang_cb.setCurrentIndex(i); break
        lang_row.addWidget(self.lang_cb); lang_row.addStretch()
        lay.addLayout(lang_row)

        clr=QPushButton(tr("clr_hk")); clr.setCursor(Qt.CursorShape.PointingHandCursor); clr.setFixedHeight(30)
        clr.setStyleSheet(f"QPushButton{{background:{T.BG3};color:{T.RED};border:1px solid {T.BORDER};border-radius:6px;padding:0 14px;font-size:11px;}}QPushButton:hover{{background:{T.RED};color:white;}}")
        clr.clicked.connect(self._clear_all); lay.addWidget(clr,alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addStretch()

        btns=QHBoxLayout(); btns.addStretch()
        cancel=QPushButton(tr("cancel")); cancel.setFixedHeight(36); cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(f"QPushButton{{background:{T.BG3};color:{T.TEXTD};border:1px solid {T.BORDER};border-radius:7px;padding:0 20px;font-size:12px;}}QPushButton:hover{{border-color:{T.BORDER2};color:{T.TEXT};}}")
        cancel.clicked.connect(self.close); btns.addWidget(cancel)
        save=QPushButton(tr("save")); save.setFixedHeight(36); save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.setStyleSheet(f"QPushButton{{background:{T.ACCENT};color:white;border:none;border-radius:7px;padding:0 24px;font-size:12px;font-weight:bold;}}QPushButton:hover{{background:{T.ACCENT2};}}")
        save.clicked.connect(self._save); btns.addWidget(save); lay.addLayout(btns)

        self.hk_next.captured.connect(lambda d,r:(setattr(self.s,'hotkey_next_display',d)or setattr(self.s,'hotkey_next_raw',r)))
        self.hk_prev.captured.connect(lambda d,r:(setattr(self.s,'hotkey_prev_display',d)or setattr(self.s,'hotkey_prev_raw',r)))
        self.hk_stop.captured.connect(lambda d,r:(setattr(self.s,'hotkey_stop_display',d)or setattr(self.s,'hotkey_stop_raw',r)))

    def _clear_all(self):
        for attr in['hotkey_next_display','hotkey_next_raw','hotkey_prev_display','hotkey_prev_raw','hotkey_stop_display','hotkey_stop_raw']:
            setattr(self.s,attr,"")
        self.hk_next.set_hotkey(""); self.hk_prev.set_hotkey(""); self.hk_stop.set_hotkey("")

    def _save(self):
        new_lang=self.lang_cb.currentData()
        lang_changed=(new_lang!=self.s.language)
        self.s.language=new_lang
        self.saved.emit(self.s)
        if lang_changed: self.lang_changed.emit(new_lang)
        self.accept()

# ─── LIBRARY TREE ────────────────────────────────────────────────────────────
class LibraryTree(QTreeWidget):
    soundFolderChanged  = pyqtSignal(int,str)
    viewChanged         = pyqtSignal(str,str)
    soundSelected       = pyqtSignal(int, str)
    folderRenameReq     = pyqtSignal(str)
    folderDeleteReq     = pyqtSignal(str)
    soundRenameReq      = pyqtSignal(int)
    soundTrimReq        = pyqtSignal(int)
    soundDeleteReq      = pyqtSignal(int)
    soundRemFolderReq   = pyqtSignal(int, str)
    soundAddFolderReq   = pyqtSignal(int)
    newFolderReq        = pyqtSignal()

    def __init__(self,parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True); self.setAnimated(True); self.setIndentation(16)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setExpandsOnDoubleClick(True)
        self.setDragEnabled(False)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self._drag_start=None; self._drag_idx=None; self._drag_name=""
        self.setStyleSheet(f"""
            QTreeWidget{{background:transparent;border:none;outline:none;}}
            QTreeWidget::item{{padding:5px 6px;border-radius:5px;margin:1px 3px;color:{T.TEXTD};}}
            QTreeWidget::item:hover{{background:{T.CARD};color:{T.TEXT};}}
            QTreeWidget::item:selected{{background:{T.CARD2};color:{T.TEXT};}}
            QTreeWidget::branch{{background:transparent;}}
        """)

    def rebuild(self,sounds,folders,folder_colors,active_type,active_folder):
        self.clear()
        all_item=QTreeWidgetItem(self)
        all_item.setText(0,f"  📚 {tr('all_sounds')}  ({len(sounds)})")
        all_item.setData(0,ROLE_TYPE,ITEM_ALL); all_item.setData(0,ROLE_IDX,"")
        all_item.setFont(0,QFont("Segoe UI",10,QFont.Weight.Bold))
        all_item.setForeground(0,QColor(T.CYAN)); all_item.setExpanded(True)
        all_item.setToolTip(0,tr("drag_tip"))
        for i,s in enumerate(sounds):
            child=QTreeWidgetItem(all_item)
            kb_txt=f"  [{s.keybind}]" if s.keybind else ""
            child.setText(0,f"    {s.name}{kb_txt}")
            child.setData(0,ROLE_TYPE,ITEM_SOUND); child.setData(0,ROLE_IDX,i)
            child.setToolTip(0,s.path)
        for fname in folders:
            col=folder_colors.get(fname,T.ACCENT)
            fsounds = [(i,s) for i,s in enumerate(sounds) if s.has_folder(fname)]
            fi=QTreeWidgetItem(self)
            fi.setText(0,f"  📁 {fname}  ({len(fsounds)})")
            fi.setData(0,ROLE_TYPE,ITEM_FOLDER); fi.setData(0,ROLE_IDX,fname)
            fi.setFont(0,QFont("Segoe UI",10,QFont.Weight.Bold))
            fi.setForeground(0,QColor(col)); fi.setExpanded(True)
            for gi,s in fsounds:
                child=QTreeWidgetItem(fi)
                label=f"    {s.name}"
                fhk,_ = s.get_folder_hotkey(fname)
                if fhk:
                    label += f"  [📁{fhk}]"
                child.setText(0,label)
                child.setData(0,ROLE_TYPE,ITEM_SOUND); child.setData(0,ROLE_IDX,gi)
                child.setToolTip(0,s.path)
        nf=QTreeWidgetItem(self); nf.setText(0,f"  ＋ {tr('new_folder')}")
        nf.setData(0,ROLE_TYPE,"new_folder")
        nf.setForeground(0,QColor(T.TEXTDD))
        self._restore_selection(active_type,active_folder)

    def _restore_selection(self,active_type,active_folder):
        root=self.invisibleRootItem()
        for i in range(root.childCount()):
            item=root.child(i)
            t=item.data(0,ROLE_TYPE)
            if active_type==ITEM_ALL and t==ITEM_ALL:
                self.setCurrentItem(item); return
            if active_type==ITEM_FOLDER and t==ITEM_FOLDER and item.data(0,ROLE_IDX)==active_folder:
                self.setCurrentItem(item); return
        if root.childCount()>0:
            self.setCurrentItem(root.child(0))

    def mousePressEvent(self,e):
        item=self.itemAt(e.position().toPoint())
        if item:
            t=item.data(0,ROLE_TYPE)
            if t==ITEM_SOUND and e.button()==Qt.MouseButton.LeftButton:
                self._drag_start=e.position().toPoint()
                self._drag_idx=item.data(0,ROLE_IDX)
                self._drag_name=item.text(0).strip().split("  [")[0].strip()
            else:
                self._drag_start=None; self._drag_idx=None
        super().mousePressEvent(e)

    def mouseMoveEvent(self,e):
        if (self._drag_start and self._drag_idx is not None and
                (e.position().toPoint()-self._drag_start).manhattanLength()>10):
            drag=QDrag(self.viewport())
            mime=QMimeData(); mime.setText(f"sound:{self._drag_idx}"); drag.setMimeData(mime)
            pm=QPixmap(180,28); pm.fill(QColor(T.ACCD))
            p=QPainter(pm); p.setPen(QColor(T.WHITE)); p.setFont(QFont("Segoe UI",9,QFont.Weight.Bold))
            name=self._drag_name[:22] if len(self._drag_name)>22 else self._drag_name
            p.drawText(8,19,f"🔊  {name}"); p.end()
            drag.setPixmap(pm); drag.setHotSpot(QPoint(90,14))
            drag.exec(Qt.DropAction.MoveAction)
            self._drag_start=None; self._drag_idx=None
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self,e):
        item=self.itemAt(e.position().toPoint())
        if item and e.button()==Qt.MouseButton.LeftButton:
            t=item.data(0,ROLE_TYPE)
            if t==ITEM_ALL:
                self.viewChanged.emit(ITEM_ALL,"")
            elif t==ITEM_FOLDER:
                self.viewChanged.emit(ITEM_FOLDER,item.data(0,ROLE_IDX))
            elif t==ITEM_SOUND:
                parent = item.parent()
                folder = ""
                if parent and parent.data(0,ROLE_TYPE) == ITEM_FOLDER:
                    folder = parent.data(0,ROLE_IDX)
                self.soundSelected.emit(item.data(0,ROLE_IDX), folder)
            elif t=="new_folder":
                self.newFolderReq.emit()
        self._drag_start=None
        super().mouseReleaseEvent(e)

    def dragEnterEvent(self,e):
        if e.mimeData().hasText() and e.mimeData().text().startswith("sound:"):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self,e):
        item=self.itemAt(e.position().toPoint())
        if item:
            t=item.data(0,ROLE_TYPE)
            if t in (ITEM_FOLDER, ITEM_ALL):
                e.acceptProposedAction(); self.setCurrentItem(item); return
        e.ignore()

    def dropEvent(self,e):
        item=self.itemAt(e.position().toPoint())
        if item and e.mimeData().hasText():
            txt=e.mimeData().text()
            if txt.startswith("sound:"):
                sound_idx=int(txt.split(":")[1]); t=item.data(0,ROLE_TYPE)
                if t==ITEM_FOLDER:
                    self.soundFolderChanged.emit(sound_idx, item.data(0,ROLE_IDX))
                    e.acceptProposedAction(); return
                elif t==ITEM_ALL:
                    e.acceptProposedAction(); return
        e.ignore()

    def contextMenuEvent(self,e):
        item=self.itemAt(e.pos())
        if not item: return
        t=item.data(0,ROLE_TYPE)
        menu=QMenu(self)
        menu.setStyleSheet(f"QMenu{{background:{T.BG3};border:1px solid {T.BORDER};border-radius:8px;padding:4px;}}QMenu::item{{padding:7px 18px;color:{T.TEXT};border-radius:4px;}}QMenu::item:selected{{background:{T.ACCENT};}}")
        if t==ITEM_FOLDER:
            fname=item.data(0,ROLE_IDX)
            menu.addAction(QAction(tr("rename"),self,triggered=lambda:self.folderRenameReq.emit(fname)))
            menu.addAction(QAction(tr("del_folder"),self,triggered=lambda:self.folderDeleteReq.emit(fname)))
        elif t==ITEM_SOUND:
            idx=item.data(0,ROLE_IDX)
            parent=item.parent()
            in_folder = parent and parent.data(0,ROLE_TYPE) == ITEM_FOLDER
            if in_folder:
                folder_name = parent.data(0,ROLE_IDX)
                menu.addAction(QAction(tr("rem_folder"),self,triggered=lambda:self.soundRemFolderReq.emit(idx, folder_name)))
            menu.addAction(QAction(tr("rename"),self,triggered=lambda:self.soundRenameReq.emit(idx)))
            menu.addAction(QAction(tr("trim"),self,triggered=lambda:self.soundTrimReq.emit(idx)))
            menu.addSeparator()
            menu.addAction(QAction(tr("add_folder"),self,triggered=lambda:self.soundAddFolderReq.emit(idx)))
            menu.addSeparator()
            menu.addAction(QAction(tr("delete_lib"),self,triggered=lambda:self.soundDeleteReq.emit(idx)))
        else: return
        menu.exec(e.globalPos())

# ─── SOUND CARD ───────────────────────────────────────────────────────────────
class SoundCard(QFrame):
    clicked=pyqtSignal(int); rightClicked=pyqtSignal(int,object)
    def __init__(self,sound,idx,parent=None):
        super().__init__(parent); self.sound=sound; self.idx=idx
        self._playing=False; self._anim=0.0
        self._anim_t=QTimer(self); self._anim_t.setInterval(120); self._anim_t.timeout.connect(self._anim_step)
        self.setFixedSize(158,110); self.setCursor(Qt.CursorShape.PointingHandCursor); self._build()

    def _build(self):
        self._set_style(False); lay=QVBoxLayout(self); lay.setSpacing(3); lay.setContentsMargins(10,8,10,8)
        top=QHBoxLayout(); self.lbl_icon=QLabel("🔊"); self.lbl_icon.setFont(QFont("Segoe UI",16)); top.addWidget(self.lbl_icon); top.addStretch()
        if self.sound.keybind:
            kb=QLabel(self.sound.keybind)
            kb.setStyleSheet(f"background:{T.ACCD};color:white;border-radius:3px;padding:1px 4px;font-size:8px;font-weight:bold;")
            top.addWidget(kb)
        lay.addLayout(top)
        self.lbl_name=QLabel(self.sound.name); self.lbl_name.setFont(QFont("Segoe UI",9,QFont.Weight.Bold))
        self.lbl_name.setStyleSheet(f"color:{T.TEXT};"); self.lbl_name.setWordWrap(True); self.lbl_name.setMaximumHeight(36); lay.addWidget(self.lbl_name)
        if self.sound.folder_assignments:
            fl=QLabel(f"📁 {list(self.sound.folder_assignments.keys())[0]}")
            fl.setStyleSheet(f"color:{T.TEXTD};font-size:8px;"); lay.addWidget(fl)
        self.lbl_st=QLabel("● Ready"); self.lbl_st.setFont(QFont("Segoe UI",8)); self.lbl_st.setStyleSheet(f"color:{T.TEXTDD};"); lay.addWidget(self.lbl_st)

    def _set_style(self,playing):
        if playing: self.setStyleSheet(f"SoundCard{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {T.ACCD},stop:1 {T.BG3});border:1px solid {T.ACCENT};border-radius:10px;}}")
        else: self.setStyleSheet(f"SoundCard{{background:{T.CARD};border:1px solid {T.BORDER};border-radius:10px;}}SoundCard:hover{{background:{T.CARD2};border-color:{T.ACCENT};}}")

    def set_playing(self,playing):
        if self._playing==playing: return
        self._playing=playing; self._set_style(playing)
        if playing: self.lbl_st.setText("▶ Playing"); self.lbl_st.setStyleSheet(f"color:{T.CYAN};"); self._anim_t.start()
        else: self._anim_t.stop(); self.lbl_icon.setText("🔊"); self.lbl_st.setText("● Ready"); self.lbl_st.setStyleSheet(f"color:{T.TEXTDD};")

    def _anim_step(self):
        self._anim=(self._anim+1)%4; self.lbl_icon.setText(["🔊","🔉","🔈","🔉"][int(self._anim)])

    def update_name(self,name): self.sound.name=name; self.lbl_name.setText(name)
    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton: self.clicked.emit(self.idx)
        elif e.button()==Qt.MouseButton.RightButton: self.rightClicked.emit(self.idx,e.globalPosition().toPoint())
    def mouseDoubleClickEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton: self.clicked.emit(self.idx)

# ─── MAIN WINDOW ─────────────────────────────────────────────────────────────
class SoundpadApp(QMainWindow):
    _hotkey_signal      = pyqtSignal(int)
    _folder_hk_signal   = pyqtSignal(int, str)
    _hotkey_next_sig    = pyqtSignal()
    _hotkey_prev_sig    = pyqtSignal()
    _hotkey_stop_sig    = pyqtSignal()
    _pt_error           = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.router=AudioRouter(); self.sounds:list[Sound]=[]
        self.folders:list[str]=[]; self.folder_colors:dict[str,str]={}
        self.keybinds:dict[str,int]={}
        self.folder_keybinds:dict[str,tuple[int,str]]={}
        self.settings=AppSettings()
        self.selected:int|None=None; self._cards:list[SoundCard]=[]
        self._active_type=ITEM_ALL; self._active_folder=""
        self._hotkey_signal.connect(self._on_sound_hotkey)
        self._folder_hk_signal.connect(self._on_folder_hotkey)
        self._hotkey_next_sig.connect(self._play_next)
        self._hotkey_prev_sig.connect(self._play_prev)
        self._hotkey_stop_sig.connect(self.router.stop_all_sounds)
        self._pt_error.connect(lambda m:QMessageBox.critical(self,tr("audio_error"),m))
        self._status_timer=QTimer(self); self._status_timer.setInterval(250)
        self._status_timer.timeout.connect(self._tick_status); self._status_timer.start()
        self._load_config()
        self._build_ui()
        self._refresh_devices(); self._rebuild_tree(); self._refresh_grid()
        self._register_hotkeys(); self._create_tray(); self.setWindowIcon(self._make_icon())
        QTimer.singleShot(600,self._auto_passthrough)

    def _auto_passthrough(self):
        if not self.router.passthrough_active:
            try: self.router.start_passthrough(); self._update_pt_indicator()
            except Exception as e: self._pt_error.emit(f"{tr('audio_error')}:\n{e}")

    def _make_icon(self):
        img=QImage(32,32,QImage.Format.Format_ARGB32); img.fill(QColor(0,0,0,0))
        p=QPainter(img); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(T.ACCENT)); p.setPen(Qt.PenStyle.NoPen); p.drawRoundedRect(1,1,30,30,7,7)
        p.setPen(QPen(QColor(T.WHITE),2.5))
        for x,y1,y2 in[(7,11,21),(11,8,24),(16,13,19),(21,6,26),(25,11,21)]: p.drawLine(x,y1,x,y2)
        p.end(); return QIcon(QPixmap.fromImage(img))

    def _create_tray(self):
        self.tray=QSystemTrayIcon(self._make_icon(),self)
        menu=QMenu()
        menu.setStyleSheet(f"QMenu{{background:{T.BG3};border:1px solid {T.BORDER};border-radius:8px;padding:4px;}}QMenu::item{{padding:7px 18px;color:{T.TEXT};border-radius:4px;}}QMenu::item:selected{{background:{T.ACCENT};}}")
        menu.addAction(QAction(tr("open_app"),self,triggered=self.show_window))
        menu.addSeparator()
        menu.addAction(QAction(tr("quit"),self,triggered=self.quit_app))
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda r:self.show_window()if r==QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self.tray.show()

    def show_window(self): self.showNormal(); self.raise_(); self.activateWindow()

    def quit_app(self):
        self.router.stop_passthrough(); self._save_config(); keyboard.unhook_all()
        self.tray.hide(); QApplication.quit()

    def closeEvent(self,e): e.ignore(); self.hide()

    # ─── CONFIG ──────────────────────────────────────────────────────────────
    def _load_config(self):
        global LANG
        if not os.path.exists(CONFIG_FILE): return
        try:
            with open(CONFIG_FILE)as f: cfg=json.load(f)
        except: return
        self.sounds=[]
        for s_dict in cfg.get("sounds",[]):
            folder_assignments = s_dict.get("folder_assignments", {})
            if not folder_assignments and "folder" in s_dict and s_dict["folder"]:
                folder = s_dict["folder"]
                fk = s_dict.get("folder_keybind")
                fkr = s_dict.get("folder_keybind_raw")
                folder_assignments[folder] = {"keybind": fk, "keybind_raw": fkr}
            sound = Sound(
                name=s_dict["name"], path=s_dict["path"],
                keybind=s_dict.get("keybind"), keybind_raw=s_dict.get("keybind_raw"),
                volume=s_dict.get("volume",1.0), start_sec=s_dict.get("start_sec",0.0),
                end_sec=s_dict.get("end_sec",-1.0), folder_assignments=folder_assignments
            )
            self.sounds.append(sound)
        self.folders=cfg.get("folders",[])
        self.folder_colors=cfg.get("folder_colors",{})
        self.keybinds={}
        self.folder_keybinds={}
        for i,s in enumerate(self.sounds):
            if s.keybind_raw:
                self.keybinds[s.keybind_raw]=i
            for fname, data in s.folder_assignments.items():
                raw = data.get("keybind_raw")
                if raw:
                    self.folder_keybinds[raw] = (i, fname)
        so=cfg.get("virtual_device"); si=cfg.get("mic_device")
        if so is not None: self.router.virtual_device=so
        if si is not None: self.router.mic_device=si
        st=cfg.get("settings",{})
        self.settings.hotkey_next_display=st.get("hotkey_next_display","")
        self.settings.hotkey_next_raw=st.get("hotkey_next_raw","")
        self.settings.hotkey_prev_display=st.get("hotkey_prev_display","")
        self.settings.hotkey_prev_raw=st.get("hotkey_prev_raw","")
        self.settings.hotkey_stop_display=st.get("hotkey_stop_display","")
        self.settings.hotkey_stop_raw=st.get("hotkey_stop_raw","")
        self.settings.language=st.get("language","en")
        LANG=self.settings.language

    def _save_config(self):
        cfg={
            "virtual_device":self.router.virtual_device,
            "mic_device":self.router.mic_device,
            "folders":self.folders,
            "folder_colors":self.folder_colors,
            "settings":{
                "hotkey_next_display":self.settings.hotkey_next_display,
                "hotkey_next_raw":self.settings.hotkey_next_raw,
                "hotkey_prev_display":self.settings.hotkey_prev_display,
                "hotkey_prev_raw":self.settings.hotkey_prev_raw,
                "hotkey_stop_display":self.settings.hotkey_stop_display,
                "hotkey_stop_raw":self.settings.hotkey_stop_raw,
                "language":self.settings.language
            },
            "sounds":[]
        }
        for s in self.sounds:
            cfg["sounds"].append({
                "name":s.name,"path":s.path,"keybind":s.keybind,"keybind_raw":s.keybind_raw,
                "volume":s.volume,"start_sec":s.start_sec,"end_sec":s.end_sec,
                "folder_assignments":s.folder_assignments
            })
        with open(CONFIG_FILE,"w")as f: json.dump(cfg,f,indent=2)

    # ─── HOTKEYS ─────────────────────────────────────────────────────────────
    def _register_hotkeys(self):
        keyboard.unhook_all()

        # Словарь: frozenset(scan_codes) -> callable
        self._sc_hotkey_map: dict    = {}
        self._pressed_sc:    set     = set()
        self._last_fired_sc: frozenset = frozenset()

        def _is_sc(raw: str) -> bool:
            """True если raw — набор scan codes, напр. '57+30'."""
            return bool(raw) and all(p.isdigit() for p in raw.split("+"))

        def _add(raw: str, cb):
            if _is_sc(raw):
                # Новый формат: физические scan codes → не зависит от раскладки
                self._sc_hotkey_map[frozenset(int(p) for p in raw.split("+"))] = cb
            else:
                # Старый формат из сохранённых конфигов: имена клавиш
                try:
                    keyboard.add_hotkey(raw, cb)
                except Exception as e:
                    print(f"[Hotkey legacy] {raw}: {e}")

        for raw, idx in self.keybinds.items():
            _add(raw, lambda _i=idx: self._hotkey_signal.emit(_i))

        for raw, (idx, folder) in self.folder_keybinds.items():
            if raw not in self.keybinds:
                _add(raw, lambda _i=idx, _f=folder: self._folder_hk_signal.emit(_i, _f))

        if self.settings.hotkey_next_raw:
            _add(self.settings.hotkey_next_raw, self._hotkey_next_sig.emit)
        if self.settings.hotkey_prev_raw:
            _add(self.settings.hotkey_prev_raw, self._hotkey_prev_sig.emit)
        if self.settings.hotkey_stop_raw:
            _add(self.settings.hotkey_stop_raw, self._hotkey_stop_sig.emit)

        if self._sc_hotkey_map:
            def _global_sc_hook(ev):
                sc = ev.scan_code
                if not sc:
                    return
                if ev.event_type == 'down':
                    self._pressed_sc.add(sc)
                    fs = frozenset(self._pressed_sc)
                    # Срабатываем ровно один раз пока комбо зажато
                    if fs in self._sc_hotkey_map and fs != self._last_fired_sc:
                        self._last_fired_sc = fs
                        self._sc_hotkey_map[fs]()
                elif ev.event_type == 'up':
                    self._pressed_sc.discard(sc)
                    if not self._pressed_sc:
                        self._last_fired_sc = frozenset()  # сброс — можно нажать снова

            keyboard.hook(_global_sc_hook)

    def _on_sound_hotkey(self, idx):
        """Global hotkey handler — always plays regardless of active folder view."""
        if idx >= len(self.sounds): return
        s = self.sounds[idx]
        if self.router.is_playing(s.path):
            self.router.stop_sound_by_path(s.path)
        else:
            threading.Thread(
                target=self._play_with_stop,
                args=(idx,),
                daemon=True
            ).start()

    def _on_folder_hotkey(self, idx, folder):
        """Folder-scoped hotkey — only fires when that folder view is active."""
        if idx >= len(self.sounds): return
        if self._active_type != ITEM_FOLDER or self._active_folder != folder:
            return
        s = self.sounds[idx]
        if self.router.is_playing(s.path):
            self.router.stop_sound_by_path(s.path)
        else:
            threading.Thread(
                target=self._play_with_stop,
                args=(idx,),
                daemon=True
            ).start()

    def _play_with_stop(self, idx):
        """
        Background helper: stop everything, wait for the audio device to
        fully release, then start the new sound.  Running in a daemon thread
        keeps the UI responsive during the short wait.
        """
        # Snapshot the sound now; the list could change while we sleep.
        if idx >= len(self.sounds):
            return
        s = self.sounds[idx]

        # Serialise concurrent stop+play calls so rapid hotkey/click combos
        # don't race each other onto the audio device.
        with self.router._play_serial_lock:
            self.router.stop_all_and_wait(0.10)
            # Re-validate after the wait (user may have deleted the sound).
            if idx < len(self.sounds):
                self.router.play_sound(s.path, s.volume, s.start_sec, s.end_sec)

    def _visible_sounds(self) -> List[Tuple[int, Sound]]:
        if self._active_type == ITEM_ALL:
            return list(enumerate(self.sounds))
        return [(i,s) for i,s in enumerate(self.sounds) if s.has_folder(self._active_folder)]

    def _play_next(self):
        threading.Thread(target=self._play_next_thread, daemon=True).start()

    def _play_prev(self):
        threading.Thread(target=self._play_prev_thread, daemon=True).start()

    def _play_next_thread(self):
        vis = self._visible_sounds()
        if not vis: return
        playing_idx = next((gi for gi, s in vis if self.router.is_playing(s.path)), None)
        with self.router._play_serial_lock:
            self.router.stop_all_and_wait(0.10)
            if playing_idx is None:
                target_gi = vis[0][0]
            else:
                pos = next((i for i, (gi, _) in enumerate(vis) if gi == playing_idx), 0)
                target_gi = vis[(pos + 1) % len(vis)][0]
            s = self.sounds[target_gi]
            self.router.play_sound(s.path, s.volume, s.start_sec, s.end_sec)

    def _play_prev_thread(self):
        vis = self._visible_sounds()
        if not vis: return
        playing_idx = next((gi for gi, s in vis if self.router.is_playing(s.path)), None)
        with self.router._play_serial_lock:
            self.router.stop_all_and_wait(0.10)
            if playing_idx is None:
                target_gi = vis[-1][0]
            else:
                pos = next((i for i, (gi, _) in enumerate(vis) if gi == playing_idx), 0)
                target_gi = vis[(pos - 1) % len(vis)][0]
            s = self.sounds[target_gi]
            self.router.play_sound(s.path, s.volume, s.start_sec, s.end_sec)

    # ─── UI BUILD ────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle("SoundPad"); self.setMinimumSize(1020,680); self.resize(1180,760); self.setStyleSheet(QSS)
        central=QWidget(); self.setCentralWidget(central)
        root=QVBoxLayout(central); root.setSpacing(0); root.setContentsMargins(0,0,0,0)

        topbar=QFrame(); topbar.setFixedHeight(56)
        topbar.setStyleSheet(f"background:{T.BG2};border-bottom:1px solid {T.BORDER};")
        tl=QHBoxLayout(topbar); tl.setContentsMargins(20,0,20,0)
        logo=QLabel("◈  SoundPad"); logo.setFont(QFont("Segoe UI",16,QFont.Weight.Bold))
        logo.setStyleSheet(f"color:{T.ACCENT2};border:none;"); tl.addWidget(logo); tl.addStretch()
        self.lbl_now_playing=QLabel(); self.lbl_now_playing.setStyleSheet(f"color:{T.CYAN};font-size:11px;font-weight:bold;border:none;")
        tl.addWidget(self.lbl_now_playing); tl.addSpacing(16)
        btn_stop=self._pill_btn(tr("stop_all"),T.RED); btn_stop.clicked.connect(self.router.stop_all_sounds); tl.addWidget(btn_stop); tl.addSpacing(6)
        btn_settings=self._pill_btn(tr("settings"),T.BG3,border=True); btn_settings.clicked.connect(self._open_settings); tl.addWidget(btn_settings)
        root.addWidget(topbar)

        devbar=QFrame(); devbar.setFixedHeight(48)
        devbar.setStyleSheet(f"background:{T.BG3};border-bottom:1px solid {T.BORDER};")
        dl=QHBoxLayout(devbar); dl.setContentsMargins(20,0,20,0); dl.setSpacing(10)
        dl.addWidget(self._dim_lbl(tr("virt_cable")))
        self.cb_out=QComboBox(); self.cb_out.setFixedWidth(240); self.cb_out.currentIndexChanged.connect(self._on_out_changed); dl.addWidget(self.cb_out)
        dl.addSpacing(14); dl.addWidget(self._dim_lbl(tr("mic")))
        self.cb_in=QComboBox(); self.cb_in.setFixedWidth(240); self.cb_in.currentIndexChanged.connect(self._on_in_changed); dl.addWidget(self.cb_in)
        dl.addSpacing(18); self.lbl_pt=QLabel(tr("pt_off")); self.lbl_pt.setStyleSheet(self._pt_style(False)); dl.addWidget(self.lbl_pt); dl.addStretch()
        root.addWidget(devbar)

        splitter=QSplitter(Qt.Orientation.Horizontal); splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle{{background:{T.BORDER};}}")

        left=QFrame(); left.setStyleSheet(f"background:{T.BG2};border:none;border-right:1px solid {T.BORDER};")
        left_l=QVBoxLayout(left); left_l.setContentsMargins(0,0,0,0); left_l.setSpacing(0)
        hdr=QFrame(); hdr.setFixedHeight(38); hdr.setStyleSheet(f"background:{T.BG3};border-bottom:1px solid {T.BORDER};")
        hl=QHBoxLayout(hdr); hl.setContentsMargins(14,0,10,0)
        lbl_lib=QLabel(tr("library")); lbl_lib.setFont(QFont("Segoe UI",8,QFont.Weight.Bold))
        lbl_lib.setStyleSheet(f"color:{T.TEXTDD};letter-spacing:2px;"); hl.addWidget(lbl_lib); hl.addStretch()
        left_l.addWidget(hdr)
        self.tree=LibraryTree(left)
        self.tree.soundFolderChanged.connect(self._on_tree_add_to_folder)
        self.tree.viewChanged.connect(self._on_tree_view_change)
        self.tree.soundSelected.connect(self._on_tree_sound_select)
        self.tree.folderRenameReq.connect(self._rename_folder)
        self.tree.folderDeleteReq.connect(self._delete_folder)
        self.tree.soundRenameReq.connect(self._rename_sound_dialog)
        self.tree.soundTrimReq.connect(self._open_trim)
        self.tree.soundDeleteReq.connect(self._remove_sound_from_library)
        self.tree.soundRemFolderReq.connect(self._remove_from_folder)
        self.tree.soundAddFolderReq.connect(self._show_add_folder_menu)
        self.tree.newFolderReq.connect(self._create_folder)
        left_l.addWidget(self.tree,1)
        tip=QLabel(f"⟵ {tr('drag_tip')}"); tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip.setStyleSheet(f"color:{T.TEXTDD};font-size:9px;padding:6px;border-top:1px solid {T.BORDER};")
        left_l.addWidget(tip)
        splitter.addWidget(left)

        right=QWidget(); right.setStyleSheet(f"background:{T.BG};")
        right_l=QVBoxLayout(right); right_l.setContentsMargins(0,0,0,0); right_l.setSpacing(0)

        tb=QFrame(); tb.setFixedHeight(48); tb.setStyleSheet(f"background:{T.BG};border:none;border-bottom:1px solid {T.BORDER};")
        tb_l=QHBoxLayout(tb); tb_l.setContentsMargins(16,0,16,0); tb_l.setSpacing(10)
        self.lbl_view=QLabel(); self.lbl_view.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        self.lbl_view.setStyleSheet(f"color:{T.ACCENT2};border:none;"); tb_l.addWidget(self.lbl_view)
        self.search_box=QLineEdit(); self.search_box.setPlaceholderText(tr("search")); self.search_box.setFixedHeight(30)
        self.search_box.setStyleSheet(f"QLineEdit{{background:{T.BG3};border:1px solid {T.BORDER};border-radius:6px;padding:0 10px;color:{T.TEXT};font-size:12px;}}QLineEdit:focus{{border-color:{T.ACCENT};}}")
        self.search_box.textChanged.connect(self._on_search); tb_l.addWidget(self.search_box,1)
        btn_add=self._pill_btn(tr("add_sounds"),T.ACCENT); btn_add.clicked.connect(self._add_sounds); tb_l.addWidget(btn_add)
        right_l.addWidget(tb)

        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        self.grid_host=QWidget(); self.grid_host.setStyleSheet("background:transparent;")
        self.grid_lay=QGridLayout(self.grid_host); self.grid_lay.setSpacing(10); self.grid_lay.setContentsMargins(16,12,16,12)
        self.scroll.setWidget(self.grid_host); right_l.addWidget(self.scroll,1)

        self.detail_frame=QFrame(); self.detail_frame.setFixedHeight(195)
        self.detail_frame.setStyleSheet(f"QFrame{{background:{T.BG2};border-top:1px solid {T.BORDER};}}")
        self.detail_lay=QVBoxLayout(self.detail_frame); self.detail_lay.setContentsMargins(20,10,20,10); self.detail_lay.setSpacing(6)
        self._build_detail_empty()
        right_l.addWidget(self.detail_frame)

        splitter.addWidget(right); splitter.setSizes([240,940]); root.addWidget(splitter,1)

    # ─── TREE SIGNALS ────────────────────────────────────────────────────────
    def _on_tree_add_to_folder(self, idx, folder_name):
        self.sounds[idx].add_folder(folder_name)
        self._rebuild_tree(); self._refresh_grid(self.search_box.text()); self._save_config()

    def _on_tree_view_change(self, vtype, folder_name):
        self._active_type=vtype; self._active_folder=folder_name
        self._update_view_label(); self._refresh_grid(self.search_box.text())
        if self.selected is not None:
            self._build_detail(self.selected, "")

    def _on_tree_sound_select(self, idx, folder):
        self.selected=idx
        self._build_detail(idx, folder)
        for card in self._cards:
            if card.idx==idx:
                self.scroll.ensureWidgetVisible(card); break

    def _update_view_label(self):
        if self._active_type==ITEM_ALL: self.lbl_view.setText(f"📚  {tr('all_sounds')}")
        else: self.lbl_view.setText(f"📁  {self._active_folder}")

    def _rebuild_tree(self):
        self.tree.rebuild(self.sounds, self.folders, self.folder_colors, self._active_type, self._active_folder)

    # ─── FOLDER OPERATIONS ───────────────────────────────────────────────────
    def _create_folder(self):
        name,ok=QInputDialog.getText(self,tr("new_folder"),tr("folder_name"))
        if ok and name.strip():
            name=name.strip()
            if name not in self.folders:
                self.folders.append(name)
                self.folder_colors[name]=T.FOLDER_COLORS[len(self.folders)%len(T.FOLDER_COLORS)]
            self._rebuild_tree(); self._save_config()

    def _rename_folder(self, old_name):
        new_name,ok=QInputDialog.getText(self,tr("ren_folder"),tr("new_name"),text=old_name)
        if ok and new_name.strip() and new_name!=old_name:
            new_name=new_name.strip()
            idx=self.folders.index(old_name); self.folders[idx]=new_name
            color=self.folder_colors.pop(old_name,T.ACCENT); self.folder_colors[new_name]=color
            for s in self.sounds:
                if old_name in s.folder_assignments:
                    data = s.folder_assignments.pop(old_name)
                    s.folder_assignments[new_name] = data
            new_fk = {}
            for raw, (snd_idx, fname) in self.folder_keybinds.items():
                if fname == old_name:
                    new_fk[raw] = (snd_idx, new_name)
                else:
                    new_fk[raw] = (snd_idx, fname)
            self.folder_keybinds = new_fk
            if self._active_folder == old_name:
                self._active_folder = new_name
            self._rebuild_tree(); self._refresh_grid(self.search_box.text()); self._save_config()
            self._register_hotkeys()

    def _delete_folder(self, fname):
        reply=QMessageBox.question(self, tr("del_folder"), tr("del_folder_q", fname),
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if reply==QMessageBox.StandardButton.Yes:
            self.folders.remove(fname); self.folder_colors.pop(fname, None)
            for s in self.sounds:
                if fname in s.folder_assignments:
                    raw = s.folder_assignments[fname].get("keybind_raw")
                    if raw and raw in self.folder_keybinds:
                        del self.folder_keybinds[raw]
                    del s.folder_assignments[fname]
            if self._active_folder == fname:
                self._active_type = ITEM_ALL; self._active_folder = ""
            self._rebuild_tree(); self._refresh_grid(self.search_box.text()); self._save_config()
            self._register_hotkeys()

    def _remove_from_folder(self, idx, folder_name):
        if folder_name in self.sounds[idx].folder_assignments:
            raw = self.sounds[idx].folder_assignments[folder_name].get("keybind_raw")
            if raw and raw in self.folder_keybinds:
                del self.folder_keybinds[raw]
            self.sounds[idx].remove_folder(folder_name)
            self._rebuild_tree(); self._refresh_grid(self.search_box.text()); self._save_config()
            self._register_hotkeys()
            if self.selected == idx:
                self._build_detail(idx, "")

    def _show_add_folder_menu(self, idx):
        if not self.folders:
            self._create_folder(); return
        menu=QMenu(self)
        menu.setStyleSheet(f"QMenu{{background:{T.BG3};border:1px solid {T.BORDER};border-radius:8px;padding:4px;}}QMenu::item{{padding:7px 18px;color:{T.TEXT};border-radius:4px;}}QMenu::item:selected{{background:{T.ACCENT};}}")
        for fn in self.folders:
            action = QAction(f"📁  {fn}", self)
            action.triggered.connect(lambda checked, n=fn: self._assign_to_folder(idx, n))
            menu.addAction(action)
        menu.exec(QCursor.pos())

    def _assign_to_folder(self, idx, folder_name):
        self.sounds[idx].add_folder(folder_name)
        self._rebuild_tree(); self._refresh_grid(self.search_box.text()); self._save_config()
        if self.selected == idx:
            self._build_detail(idx, "")

    # ─── DEVICES ─────────────────────────────────────────────────────────────
    def _refresh_devices(self):
        out_devs=self.router.get_output_devices(); in_devs=self.router.get_input_devices()
        self.cb_out.blockSignals(True); self.cb_out.clear()
        for i,name in out_devs: self.cb_out.addItem(f"{i}: {name}",i)
        self.cb_out.blockSignals(False)
        self.cb_in.blockSignals(True); self.cb_in.clear()
        for i,name in in_devs: self.cb_in.addItem(f"{i}: {name}",i)
        self.cb_in.blockSignals(False)
        cable_idx,default_in=self.router.auto_select_devices()
        chosen_out=self.router.virtual_device if self.router.virtual_device is not None else cable_idx
        if chosen_out is None and out_devs: chosen_out=out_devs[0][0]
        chosen_in=self.router.mic_device if self.router.mic_device is not None else default_in
        if chosen_in is None and in_devs: chosen_in=in_devs[0][0]
        self._select_cb(self.cb_out,chosen_out); self._select_cb(self.cb_in,chosen_in)
        if chosen_out is not None: self.router.virtual_device=chosen_out
        if chosen_in is not None: self.router.mic_device=chosen_in
        self._save_config()

    def _select_cb(self,cb,dev_id):
        if dev_id is None: return
        for j in range(cb.count()):
            if cb.itemData(j)==dev_id: cb.blockSignals(True); cb.setCurrentIndex(j); cb.blockSignals(False); return

    def _on_out_changed(self,idx):
        dev=self.cb_out.itemData(idx)
        if dev is None: return
        was=self.router.passthrough_active; self.router.stop_passthrough(); self.router.set_output_device(dev); self._save_config()
        if was:
            try: self.router.start_passthrough()
            except Exception as e: QMessageBox.critical(self,tr("error"),str(e))
        self._update_pt_indicator()

    def _on_in_changed(self,idx):
        dev=self.cb_in.itemData(idx)
        if dev is None: return
        was=self.router.passthrough_active; self.router.stop_passthrough(); self.router.set_input_device(dev); self._save_config()
        if was:
            try: self.router.start_passthrough()
            except Exception as e: QMessageBox.critical(self,tr("error"),str(e))
        self._update_pt_indicator()

    def _pt_style(self,on):
        if on: return f"background:{T.GREEN};color:{T.BG};border:none;border-radius:7px;font-size:11px;font-weight:bold;padding:3px 12px;"
        return f"background:{T.BG};color:{T.TEXTD};border:1px solid {T.BORDER};border-radius:7px;font-size:11px;font-weight:bold;padding:3px 12px;"

    def _update_pt_indicator(self):
        on=self.router.passthrough_active
        self.lbl_pt.setText(tr("pt_on")if on else tr("pt_off")); self.lbl_pt.setStyleSheet(self._pt_style(on))

    # ─── GRID ────────────────────────────────────────────────────────────────
    def _refresh_grid(self, search=""):
        while self.grid_lay.count():
            item=self.grid_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._cards=[]
        vis=self._visible_sounds()
        if search: vis=[(gi,s) for gi,s in vis if search.lower() in s.name.lower()]
        self._update_view_label()
        if not vis:
            lbl=QLabel(tr("no_sounds")); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{T.TEXTDD};font-size:14px;"); self.grid_lay.addWidget(lbl,0,0,1,5)
            self._build_detail_empty(); return
        cols=5
        for pos,(gi,s) in enumerate(vis):
            card=SoundCard(s,gi)
            card.clicked.connect(self._card_clicked)
            card.rightClicked.connect(self._card_context_menu)
            r,c=divmod(pos,cols); self.grid_lay.addWidget(card,r,c); self._cards.append(card)
        for c in range(cols): self.grid_lay.setColumnStretch(c,1)

    def _on_search(self, text): self._refresh_grid(text)

    # ─── GRID CONTEXT MENU ───────────────────────────────────────────────────
    def _card_context_menu(self, idx, pos):
        s=self.sounds[idx]
        menu=QMenu(self)
        menu.setStyleSheet(f"QMenu{{background:{T.BG3};border:1px solid {T.BORDER};border-radius:8px;padding:4px;}}QMenu::item{{padding:7px 18px;color:{T.TEXT};border-radius:4px;}}QMenu::item:selected{{background:{T.ACCENT};}}")
        menu.addAction(QAction(tr("rename"),self,triggered=lambda:self._rename_sound_dialog(idx)))
        menu.addAction(QAction(tr("trim"),self,triggered=lambda:self._open_trim(idx)))
        menu.addSeparator()
        if self.folders:
            add_m=QMenu(tr("add_folder"),self); add_m.setStyleSheet(menu.styleSheet())
            for fn in self.folders:
                add_m.addAction(QAction(f"📁  {fn}", self, triggered=lambda checked, n=fn: self._assign_to_folder(idx, n)))
            menu.addMenu(add_m)
        if s.folder_assignments:
            rem_m=QMenu(tr("rem_folder"),self); rem_m.setStyleSheet(menu.styleSheet())
            for fn in s.folder_assignments.keys():
                rem_m.addAction(QAction(f"📁  {fn}", self, triggered=lambda checked, n=fn: self._remove_from_folder(idx, n)))
            menu.addMenu(rem_m)
        menu.addSeparator()
        menu.addAction(QAction(tr("delete_lib"),self,triggered=lambda:self._remove_sound_from_library(idx)))
        menu.exec(pos)

    # ─── DETAIL PANEL ────────────────────────────────────────────────────────
    def _clear_detail(self):
        for i in reversed(range(self.detail_lay.count())):
            w=self.detail_lay.itemAt(i).widget()
            if w: w.deleteLater()

    def _build_detail_empty(self):
        self._clear_detail()
        lbl=QLabel(tr("sel_sound")); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color:{T.TEXTDD};font-size:13px;"); self.detail_lay.addWidget(lbl)

    def _build_detail(self, idx, context_folder: str = ""):
        self._clear_detail()
        s=self.sounds[idx]

        row1=QHBoxLayout()
        self._detail_name_lbl=QLabel(s.name); self._detail_name_lbl.setFont(QFont("Segoe UI",13,QFont.Weight.Bold))
        self._detail_name_lbl.setStyleSheet(f"color:{T.TEXT};"); row1.addWidget(self._detail_name_lbl)
        btn_rename=QPushButton("✏"); btn_rename.setFixedSize(26,26); btn_rename.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_rename.setStyleSheet(f"QPushButton{{background:{T.BG3};color:{T.TEXTD};border:1px solid {T.BORDER};border-radius:5px;font-size:12px;}}QPushButton:hover{{background:{T.ACCENT};color:white;border-color:{T.ACCENT};}}")
        btn_rename.clicked.connect(lambda: self._rename_sound_inline(idx)); row1.addWidget(btn_rename)

        if s.folder_assignments:
            folder_list = ", ".join(s.folder_assignments.keys())
            fl=QLabel(f"  📁 {folder_list}"); fl.setStyleSheet(f"color:{T.ACCENT2};font-size:11px;")
            row1.addWidget(fl)

        row1.addStretch()
        for text,col,fn in[(tr("play"),T.GREEN,lambda:self._toggle_sound(idx)),(tr("trim"),T.ACCENT,lambda:self._open_trim(idx)),(tr("delete_lib"),T.RED,lambda:self._remove_sound_from_library(idx))]:
            b=self._pill_btn(text,col); b.clicked.connect(fn); row1.addWidget(b)
        w1=QWidget(); w1.setLayout(row1); self.detail_lay.addWidget(w1)

        pl=QLabel(s.path); pl.setStyleSheet(f"color:{T.TEXTD};font-size:10px;"); self.detail_lay.addWidget(pl)

        row2=QHBoxLayout(); row2.setSpacing(12)
        row2.addWidget(self._dim_lbl(tr("volume")))
        vol_sl=QSlider(Qt.Orientation.Horizontal); vol_sl.setRange(0,100); vol_sl.setValue(int(s.volume*100)); vol_sl.setFixedWidth(100)
        vol_pct=QLabel(f"{int(s.volume*100)}%"); vol_pct.setStyleSheet(f"color:{T.ACCENT2};font-size:12px;min-width:34px;")
        def vol_ch(v,_s=s): _s.volume=v/100; vol_pct.setText(f"{v}%"); self._save_config()
        vol_sl.valueChanged.connect(vol_ch); row2.addWidget(vol_sl); row2.addWidget(vol_pct); row2.addSpacing(12)
        row2.addWidget(self._dim_lbl(tr("hotkey")))
        hk=HotkeyCapture(s.keybind or "",self)
        def on_hk_cap(display,raw,_idx=idx):
            _s=self.sounds[_idx]
            if _s.keybind_raw and _s.keybind_raw in self.keybinds: del self.keybinds[_s.keybind_raw]
            _s.keybind=display; _s.keybind_raw=raw; self.keybinds[raw]=_idx
            self._register_hotkeys(); self._refresh_grid(self.search_box.text()); self._build_detail(_idx, context_folder); self._rebuild_tree(); self._save_config()
        hk.captured.connect(on_hk_cap); row2.addWidget(hk)
        if s.keybind:
            cb=QPushButton(tr("clear_hk")); cb.setCursor(Qt.CursorShape.PointingHandCursor); cb.setFixedHeight(28)
            cb.setStyleSheet(f"QPushButton{{background:{T.BG3};color:{T.RED};border:1px solid {T.BORDER};border-radius:5px;padding:0 8px;font-size:11px;}}QPushButton:hover{{background:{T.RED};color:white;}}")
            cb.clicked.connect(lambda: self._clear_global_hotkey(idx)); row2.addWidget(cb)
        row2.addStretch()
        w2=QWidget(); w2.setLayout(row2); self.detail_lay.addWidget(w2)

        if context_folder and s.has_folder(context_folder):
            fhk_display, fhk_raw = s.get_folder_hotkey(context_folder)
            row = QHBoxLayout(); row.setSpacing(12)
            lbl = QLabel(f"📁 {context_folder}:")
            lbl.setStyleSheet(f"color:{self.folder_colors.get(context_folder, T.CYAN)};font-size:11px;font-weight:bold;")
            row.addWidget(lbl)
            fhk = HotkeyCapture(fhk_display or "", self)
            def on_folder_hk_cap(display, raw, _idx=idx, _folder=context_folder):
                _s = self.sounds[_idx]
                old_raw = _s.folder_assignments.get(_folder, {}).get("keybind_raw")
                if old_raw and old_raw in self.folder_keybinds:
                    del self.folder_keybinds[old_raw]
                _s.set_folder_hotkey(_folder, display, raw)
                if raw:
                    self.folder_keybinds[raw] = (_idx, _folder)
                self._register_hotkeys()
                self._refresh_grid(self.search_box.text())
                self._build_detail(_idx, _folder)
                self._rebuild_tree()
                self._save_config()
            fhk.captured.connect(on_folder_hk_cap)
            row.addWidget(fhk)
            if fhk_display:
                clear_btn = QPushButton(tr("clear_hk"))
                clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                clear_btn.setFixedHeight(28)
                clear_btn.setStyleSheet(f"QPushButton{{background:{T.BG3};color:{T.RED};border:1px solid {T.BORDER};border-radius:5px;padding:0 8px;font-size:11px;}}QPushButton:hover{{background:{T.RED};color:white;}}")
                clear_btn.clicked.connect(lambda checked, _folder=context_folder, _idx=idx: self._clear_folder_hotkey(_idx, _folder))
                row.addWidget(clear_btn)
            tip_lbl = QLabel(f"  ℹ  {tr('folder_hk_tip')}")
            tip_lbl.setStyleSheet(f"color:{T.TEXTDD};font-size:9px;")
            row.addWidget(tip_lbl)
            row.addStretch()
            w = QWidget(); w.setLayout(row); self.detail_lay.addWidget(w)

    # ─── RENAME SOUND ────────────────────────────────────────────────────────
    def _rename_sound_dialog(self,idx):
        new_name,ok=QInputDialog.getText(self,tr("rename_dlg"),tr("new_name"),text=self.sounds[idx].name)
        if ok and new_name.strip(): self._apply_rename(idx,new_name.strip())

    def _rename_sound_inline(self,idx):
        s=self.sounds[idx]; edit=QLineEdit(s.name); edit.setFixedHeight(28); edit.selectAll()
        old_lbl=self._detail_name_lbl; parent_widget=old_lbl.parentWidget(); lay=parent_widget.layout()
        lay.replaceWidget(old_lbl,edit); old_lbl.deleteLater(); self._detail_name_lbl=edit; edit.setFocus()
        def commit():
            name=edit.text().strip()
            if name: self._apply_rename(idx,name)
        edit.returnPressed.connect(commit); edit.editingFinished.connect(commit)

    def _apply_rename(self,idx,new_name):
        self.sounds[idx].name=new_name
        for card in self._cards:
            if card.idx==idx: card.update_name(new_name)
        self._rebuild_tree(); self._build_detail(idx, ""); self._save_config()

    # ─── SETTINGS ────────────────────────────────────────────────────────────
    def _open_settings(self):
        dlg=SettingsDialog(self.settings,self)
        dlg.saved.connect(self._on_settings_saved)
        dlg.lang_changed.connect(self._change_language)
        dlg.exec()

    def _on_settings_saved(self,s:AppSettings):
        self.settings=s; self._register_hotkeys(); self._save_config()

    def _change_language(self,lang):
        global LANG
        LANG=lang; self.settings.language=lang; self._save_config()
        self._build_ui()
        self._refresh_devices(); self._rebuild_tree(); self._refresh_grid()

    # ─── ACTIONS ─────────────────────────────────────────────────────────────
    def _card_clicked(self, idx):
        self.selected = idx
        context = self._active_folder if self._active_type == ITEM_FOLDER else ""
        self._build_detail(idx, context)
        self._toggle_sound(idx)

    def _toggle_sound(self, idx):
        """Toggle playback: stop if playing, otherwise stop-all then play."""
        if idx >= len(self.sounds):
            return
        s = self.sounds[idx]
        if self.router.is_playing(s.path):
            self.router.stop_sound_by_path(s.path)
        else:
            threading.Thread(
                target=self._play_with_stop,
                args=(idx,),
                daemon=True
            ).start()

    def _add_sounds(self):
        paths,_=QFileDialog.getOpenFileNames(self,tr("select_audio"),"",tr("audio_files"))
        for p in paths:
            name=os.path.splitext(os.path.basename(p))[0]
            folder = self._active_folder if self._active_type==ITEM_FOLDER else None
            s = Sound(name, p)
            if folder:
                s.add_folder(folder)
            self.sounds.append(s)
        if paths: self._rebuild_tree(); self._refresh_grid(self.search_box.text()); self._save_config()

    def _remove_sound_from_library(self,idx):
        s=self.sounds[idx]
        reply=QMessageBox.question(self,tr("delete_lib"),tr("del_sound_q",s.name),
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if reply==QMessageBox.StandardButton.Yes:
            if s.keybind_raw and s.keybind_raw in self.keybinds: del self.keybinds[s.keybind_raw]
            for fname, data in s.folder_assignments.items():
                raw = data.get("keybind_raw")
                if raw and raw in self.folder_keybinds: del self.folder_keybinds[raw]
            self.sounds.pop(idx)
            self.keybinds = {k:(v if v<idx else v-1) for k,v in self.keybinds.items()}
            self.folder_keybinds = {k:( (v[0] if v[0]<idx else v[0]-1, v[1]) ) for k,v in self.folder_keybinds.items()}
            self.selected=None; self._rebuild_tree(); self._refresh_grid(self.search_box.text())
            self._register_hotkeys(); self._build_detail_empty(); self._save_config()

    def _open_trim(self,idx):
        ed=TrimEditor(self.sounds[idx],self)
        ed.saved.connect(lambda _:(self._rebuild_tree(), self._refresh_grid(self.search_box.text()), self._save_config()))
        ed.exec()

    def _clear_global_hotkey(self,idx):
        s=self.sounds[idx]
        if s.keybind_raw and s.keybind_raw in self.keybinds: del self.keybinds[s.keybind_raw]
        s.keybind=None; s.keybind_raw=None
        self._register_hotkeys(); self._rebuild_tree(); self._refresh_grid(self.search_box.text()); self._build_detail(idx, ""); self._save_config()

    def _clear_folder_hotkey(self, idx, folder_name):
        s = self.sounds[idx]
        if folder_name in s.folder_assignments:
            raw = s.folder_assignments[folder_name].get("keybind_raw")
            if raw and raw in self.folder_keybinds:
                del self.folder_keybinds[raw]
            s.set_folder_hotkey(folder_name, None, None)
            self._register_hotkeys()
            self._rebuild_tree()
            self._refresh_grid(self.search_box.text())
            self._build_detail(idx, folder_name)
            self._save_config()

    # ─── STATUS TICK ─────────────────────────────────────────────────────────
    def _tick_status(self):
        playing=[]
        for card in self._cards:
            is_p=self.router.is_playing(card.sound.path); card.set_playing(is_p)
            if is_p: playing.append(card.sound.name)
        self.lbl_now_playing.setText(f"▶  {', '.join(playing)}"if playing else "")
        self._update_pt_indicator()

    # ─── HELPERS ─────────────────────────────────────────────────────────────
    def _pill_btn(self,text,color,border=False):
        b=QPushButton(text); b.setCursor(Qt.CursorShape.PointingHandCursor); b.setFixedHeight(32)
        if border: b.setStyleSheet(f"QPushButton{{background:transparent;color:{T.TEXTD};border:1px solid {T.BORDER};border-radius:7px;padding:0 14px;font-size:12px;}}QPushButton:hover{{border-color:{T.BORDER2};color:{T.TEXT};}}")
        else: b.setStyleSheet(f"QPushButton{{background:{color};color:white;border:none;border-radius:7px;padding:0 14px;font-size:12px;font-weight:bold;}}QPushButton:hover{{background:{color}cc;}}")
        return b

    def _dim_lbl(self,text):
        l=QLabel(text); l.setStyleSheet(f"color:{T.TEXTD};font-size:11px;border:none;"); return l

# ─── ENTRY ───────────────────────────────────────────────────────────────────
if __name__=="__main__":
    app=QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("SoundPad")
    window=SoundpadApp()
    window.show()
    sys.exit(app.exec())
