"""
Czytnik PDF/EPUB/TXT — Kivy Android APK
TTS przez edge-tts (online) lub pyttsx3 (offline)
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.lang import Builder

import os
import threading
import tempfile

# ── opcjonalne biblioteki ────────────────────────────────────────────────────
try:
    import pymupdf
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    HAS_EPUB = True
except ImportError:
    HAS_EPUB = False

try:
    import edge_tts
    import asyncio
    HAS_EDGE = True
except ImportError:
    HAS_EDGE = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

# ── kolory ───────────────────────────────────────────────────────────────────
BG      = get_color_from_hex("#0d0f14")
SURF    = get_color_from_hex("#161920")
BORDER  = get_color_from_hex("#2a2d38")
ACC     = get_color_from_hex("#5b8af5")
TEXT    = get_color_from_hex("#e2e5f0")
MUTED   = get_color_from_hex("#6b7280")
OK      = get_color_from_hex("#22c55e")
ERR     = get_color_from_hex("#ef4444")

Window.clearcolor = BG

KV = """
<RoundButton@Button>:
    background_color: 0,0,0,0
    background_normal: ''
    canvas.before:
        Color:
            rgba: (0.357,0.541,0.961,1) if self.state=='normal' else (0.271,0.412,0.733,1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]

<GhostButton@Button>:
    background_color: 0,0,0,0
    background_normal: ''
    canvas.before:
        Color:
            rgba: (0.086,0.094,0.078,1) if self.state=='normal' else (0.165,0.098,0.118,1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]
        Color:
            rgba: 0.165,0.176,0.22,1
        Line:
            rounded_rectangle: self.x+1, self.y+1, self.width-2, self.height-2, 10
"""

Builder.load_string(KV)

# ── ekstrakcja tekstu ────────────────────────────────────────────────────────
def extract_txt(path):
    for enc in ("utf-8", "cp1250", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except:
            pass
    return ""

def extract_pdf(path):
    if not HAS_PDF:
        return "BŁĄD: pip install pymupdf"
    doc = pymupdf.open(path)
    return "\n\n".join(f"=== Strona {i+1} ===\n{p.get_text()}" for i, p in enumerate(doc))

def extract_epub(path):
    if not HAS_EPUB:
        return "BŁĄD: pip install ebooklib beautifulsoup4"
    book = epub.read_epub(path)
    parts = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_body_content(), "html.parser")
            t = soup.get_text(separator="\n").strip()
            if t:
                parts.append(t)
    return "\n\n".join(parts)

# ── TTS ──────────────────────────────────────────────────────────────────────
VOICES = [
    ("pl-PL-ZofiaNeural",  "Zofia (PL, kobieta)"),
    ("pl-PL-MarekNeural",  "Marek (PL, mężczyzna)"),
    ("en-US-JennyNeural",  "Jenny (EN, kobieta)"),
    ("en-US-GuyNeural",    "Guy (EN, mężczyzna)"),
    ("de-DE-KatjaNeural",  "Katja (DE, kobieta)"),
    ("fr-FR-DeniseNeural", "Denise (FR, kobieta)"),
]

async def edge_tts_generate(tekst, voice, rate, out_path):
    rate_str = f"+{rate}%" if rate >= 0 else f"{rate}%"
    comm = edge_tts.Communicate(tekst, voice, rate=rate_str)
    await comm.save(out_path)

# ── główny ekran ─────────────────────────────────────────────────────────────
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tekst = ""
        self.tts_thread = None
        self.audio_path = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))

        # nagłówek
        hdr = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        hdr_label = Label(
            text="📖 Czytnik PDF/EPUB/TXT",
            font_size=dp(18), bold=True,
            color=ACC, halign="left", valign="middle"
        )
        hdr_label.bind(size=hdr_label.setter("text_size"))
        hdr.add_widget(hdr_label)
        root.add_widget(hdr)

        # przycisk wczytaj plik
        btn_open = Button(
            text="📂  Otwórz plik (PDF / EPUB / TXT)",
            size_hint_y=None, height=dp(48),
            background_color=ACC, color=TEXT,
            font_size=dp(14), bold=True
        )
        btn_open.bind(on_press=self.open_file)
        root.add_widget(btn_open)

        # info o pliku
        self.lbl_info = Label(
            text="Brak wczytanego pliku",
            size_hint_y=None, height=dp(24),
            color=MUTED, font_size=dp(12),
            halign="left", valign="middle"
        )
        self.lbl_info.bind(size=self.lbl_info.setter("text_size"))
        root.add_widget(self.lbl_info)

        # pole tekstowe
        scroll = ScrollView(size_hint_y=0.45)
        self.txt = TextInput(
            text="",
            multiline=True, readonly=False,
            background_color=get_color_from_hex("#0a0c10"),
            foreground_color=TEXT,
            cursor_color=ACC,
            font_size=dp(13),
            padding=[dp(10), dp(10)],
            size_hint_y=None
        )
        self.txt.bind(minimum_height=self.txt.setter("height"))
        scroll.add_widget(self.txt)
        root.add_widget(scroll)

        # separator
        root.add_widget(Label(
            text="── Synteza mowy ──",
            size_hint_y=None, height=dp(24),
            color=MUTED, font_size=dp(11)
        ))

        # wybór lektora
        voice_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        voice_row.add_widget(Label(text="Lektor:", color=MUTED, font_size=dp(13), size_hint_x=0.3))
        self.voice_spinner = Spinner(
            text="Zofia (PL, kobieta)",
            values=[v[1] for v in VOICES],
            size_hint_x=0.7,
            background_color=SURF,
            color=TEXT,
            font_size=dp(13)
        )
        voice_row.add_widget(self.voice_spinner)
        root.add_widget(voice_row)

        # prędkość
        rate_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        rate_row.add_widget(Label(text="Prędkość:", color=MUTED, font_size=dp(13), size_hint_x=0.3))
        self.rate_slider = Slider(min=-50, max=100, value=0, size_hint_x=0.5)
        self.lbl_rate = Label(text="0%", color=ACC, font_size=dp(13), size_hint_x=0.2)
        self.rate_slider.bind(value=lambda i, v: setattr(self.lbl_rate, "text", f"{int(v)}%"))
        rate_row.add_widget(self.rate_slider)
        rate_row.add_widget(self.lbl_rate)
        root.add_widget(rate_row)

        # status TTS
        self.lbl_status = Label(
            text="",
            size_hint_y=None, height=dp(24),
            color=MUTED, font_size=dp(12)
        )
        root.add_widget(self.lbl_status)

        # przyciski TTS
        btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.btn_czytaj = Button(
            text="▶  Czytaj",
            background_color=ACC, color=TEXT,
            font_size=dp(14), bold=True
        )
        self.btn_czytaj.bind(on_press=self.czytaj)
        self.btn_stop = Button(
            text="⏹  Stop",
            background_color=SURF, color=TEXT,
            font_size=dp(14), disabled=True
        )
        self.btn_stop.bind(on_press=self.stop_tts)
        btn_row.add_widget(self.btn_czytaj)
        btn_row.add_widget(self.btn_stop)
        root.add_widget(btn_row)

        self.add_widget(root)

    # ── otwórz plik ──────────────────────────────────────────────────────────
    def open_file(self, *args):
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        fc = FileChooserListView(
            filters=["*.pdf", "*.epub", "*.txt"],
            path=os.path.expanduser("~")
        )
        content.add_widget(fc)

        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        btn_ok = Button(text="Otwórz", background_color=ACC, color=TEXT)
        btn_cancel = Button(text="Anuluj", background_color=SURF, color=TEXT)
        btn_row.add_widget(btn_ok)
        btn_row.add_widget(btn_cancel)
        content.add_widget(btn_row)

        popup = Popup(
            title="Wybierz plik",
            content=content,
            size_hint=(0.95, 0.85),
            background_color=SURF
        )

        def on_open(*a):
            if not fc.selection:
                return
            path = fc.selection[0]
            popup.dismiss()
            self.load_file(path)

        btn_ok.bind(on_press=on_open)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def load_file(self, path):
        self.lbl_info.text = "⏳ Wczytywanie..."
        def _load():
            ext = os.path.splitext(path)[1].lower()
            if ext == ".txt":
                tekst = extract_txt(path)
            elif ext == ".pdf":
                tekst = extract_pdf(path)
            elif ext == ".epub":
                tekst = extract_epub(path)
            else:
                tekst = "Nieobsługiwany format"
            self.tekst = tekst
            Clock.schedule_once(lambda dt: self._on_loaded(path, tekst))
        threading.Thread(target=_load, daemon=True).start()

    def _on_loaded(self, path, tekst):
        self.txt.text = tekst
        name = os.path.basename(path)
        self.lbl_info.text = f"✅ {name} · {len(tekst):,} znaków"

    # ── TTS ──────────────────────────────────────────────────────────────────
    def czytaj(self, *args):
        tekst = self.txt.text.strip()
        if not tekst:
            self.lbl_status.text = "⚠️ Brak tekstu"
            return

        voice_label = self.voice_spinner.text
        voice_id = next((v[0] for v in VOICES if v[1] == voice_label), "pl-PL-ZofiaNeural")
        rate = int(self.rate_slider.value)

        self.btn_czytaj.disabled = True
        self.btn_stop.disabled = False
        self.lbl_status.text = "⏳ Generowanie audio..."

        def _run():
            try:
                if HAS_EDGE:
                    tmp = tempfile.mktemp(suffix=".mp3")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(edge_tts_generate(tekst, voice_id, rate, tmp))
                    loop.close()
                    self.audio_path = tmp
                    Clock.schedule_once(lambda dt: self._play_audio(tmp))
                elif HAS_PYTTSX3:
                    Clock.schedule_once(lambda dt: self._pyttsx3_speak(tekst))
                else:
                    Clock.schedule_once(lambda dt: self._set_status("❌ Brak silnika TTS"))
            except Exception as e:
                Clock.schedule_once(lambda dt: self._set_status(f"❌ {e}"))

        self.tts_thread = threading.Thread(target=_run, daemon=True)
        self.tts_thread.start()

    def _play_audio(self, path):
        try:
            from kivy.core.audio import SoundLoader
            sound = SoundLoader.load(path)
            if sound:
                sound.play()
                self.lbl_status.text = "▶ Odtwarzanie..."
                def on_stop(dt):
                    self.lbl_status.text = "✅ Zakończono"
                    self.btn_czytaj.disabled = False
                    self.btn_stop.disabled = True
                Clock.schedule_once(on_stop, sound.length + 0.5)
            else:
                self._set_status("❌ Błąd odtwarzania")
        except Exception as e:
            self._set_status(f"❌ {e}")

    def _pyttsx3_speak(self, tekst):
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 160)
            engine.say(tekst)
            engine.runAndWait()
            self.lbl_status.text = "✅ Zakończono"
        except Exception as e:
            self.lbl_status.text = f"❌ {e}"
        finally:
            self.btn_czytaj.disabled = False
            self.btn_stop.disabled = True

    def _set_status(self, msg):
        self.lbl_status.text = msg
        self.btn_czytaj.disabled = False
        self.btn_stop.disabled = True

    def stop_tts(self, *args):
        self.lbl_status.text = ""
        self.btn_czytaj.disabled = False
        self.btn_stop.disabled = True


# ── App ──────────────────────────────────────────────────────────────────────
class CzytnikApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        return sm

    def on_pause(self):
        return True

    def on_resume(self):
        pass


if __name__ == "__main__":
    CzytnikApp().run()
