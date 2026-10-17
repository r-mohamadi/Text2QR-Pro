import io
import os
import zlib
import base64
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_L

from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput


# ---------- helpers ----------
def compress_text(text: str) -> str:
    """Compress UTF-8 text and encode it as printable Base64."""
    return base64.b64encode(zlib.compress(text.encode("utf-8"), 9)).decode("ascii")


def split_chunks(data: str, size: int):
    """Split a string into fixed-size chunks."""
    return [data[i:i + size] for i in range(0, len(data), size)]


def browse_start_path() -> str:
    for path in (
        "/storage/emulated/0/Download",
        "/storage/emulated/0",
        os.path.expanduser("~"),
    ):
        if os.path.isdir(path):
            return path
    return "/"


def get_save_dir() -> Path:
    """Use Android shared storage when available, otherwise the app's home."""
    try:
        from android.storage import primary_external_storage_path
        base = Path(primary_external_storage_path())
    except Exception:
        base = Path.home()

    output_dir = base / "TextToQR"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    except Exception:
        app = App.get_running_app()
        fallback = Path(app.user_data_dir) / "QRs"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


# ---------- screen 1: input ----------
class InputScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8),
        )

        layout.add_widget(Label(
            text="Text  →  QR",
            size_hint_y=None,
            height=dp(44),
            font_size=dp(22),
            bold=True,
        ))

        settings = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(6),
        )
        settings.add_widget(Label(
            text="Chars/QR:",
            size_hint_x=0.35,
            font_size=dp(13),
        ))
        self.spinner = Spinner(
            text="1800",
            values=("800", "1200", "1500", "1800", "2000", "2500"),
            size_hint_x=0.35,
        )
        settings.add_widget(self.spinner)
        settings.add_widget(Label(
            text="Compress:",
            size_hint_x=0.2,
            font_size=dp(13),
        ))
        self.compress_cb = CheckBox(active=True, size_hint_x=0.1)
        settings.add_widget(self.compress_cb)
        layout.add_widget(settings)

        self.text_input = TextInput(
            multiline=True,
            hint_text="Paste or type your text here...",
            font_size=dp(14),
        )
        layout.add_widget(self.text_input)

        row1 = BoxLayout(
            size_hint_y=None,
            height=dp(52),
            spacing=dp(8),
        )
        load_btn = Button(
            text="Open File",
            font_size=dp(15),
            bold=True,
            background_color=(0.4, 0.6, 0.95, 1),
        )
        load_btn.bind(on_release=self.open_file)
        row1.add_widget(load_btn)

        clear_btn = Button(
            text="Clear",
            font_size=dp(15),
            background_color=(0.9, 0.35, 0.35, 1),
        )
        clear_btn.bind(on_release=self.clear)
        row1.add_widget(clear_btn)
        layout.add_widget(row1)

        convert_btn = Button(
            text="CONVERT TO QR",
            size_hint_y=None,
            height=dp(64),
            font_size=dp(20),
            bold=True,
            background_color=(0.35, 0.85, 0.4, 1),
        )
        convert_btn.bind(on_release=self.convert)
        layout.add_widget(convert_btn)

        self.status = Label(
            text="Ready",
            size_hint_y=None,
            height=dp(36),
            font_size=dp(12),
        )
        layout.add_widget(self.status)
        self.add_widget(layout)

    def open_file(self, *args):
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
        )
        chooser = FileChooserListView(
            path=browse_start_path(),
            filters=["*.txt", "*.md", "*.py", "*"],
        )
        content.add_widget(chooser)

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(6),
        )
        cancel_btn = Button(text="Cancel")
        open_btn = Button(
            text="Open",
            bold=True,
            background_color=(0.35, 0.85, 0.4, 1),
        )
        buttons.add_widget(cancel_btn)
        buttons.add_widget(open_btn)
        content.add_widget(buttons)

        popup = Popup(
            title="Select text file",
            content=content,
            size_hint=(0.95, 0.95),
        )
        cancel_btn.bind(on_release=popup.dismiss)

        def do_open(*_):
            if not chooser.selection:
                return
            selected_path = chooser.selection[0]
            try:
                with open(
                    selected_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore",
                ) as file:
                    self.text_input.text = file.read()
                self.status.text = (
                    f"Loaded: {os.path.basename(selected_path)}"
                )
                popup.dismiss()
            except Exception as exc:
                self.status.text = f"Error: {exc}"

        open_btn.bind(on_release=do_open)
        popup.open()

    def clear(self, *args):
        self.text_input.text = ""
        self.status.text = "Cleared"

    def convert(self, *args):
        text = self.text_input.text.strip()
        if not text:
            self.status.text = "No text to convert"
            return

        try:
            chunk_size = int(self.spinner.text)
        except ValueError:
            chunk_size = 1800

        payload = (
            compress_text(text)
            if self.compress_cb.active
            else text
        )
        raw_chunks = split_chunks(payload, chunk_size)
        total = len(raw_chunks)
        chunks = [
            f"{index + 1}/{total}|{chunk}"
            for index, chunk in enumerate(raw_chunks)
        ]

        app = App.get_running_app()
        app.chunks = chunks
        app.current_idx = 0
        app.render_qr()

        self.status.text = f"{len(text):,} chars → {total} QR code(s)"
        app.sm.transition.direction = "left"
        app.sm.current = "qr"


# ---------- screen 2: QR viewer ----------
class QRScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(
            orientation="vertical",
            padding=dp(8),
            spacing=dp(8),
        )

        top = BoxLayout(
            size_hint_y=None,
            height=dp(46),
            spacing=dp(6),
        )
        back_btn = Button(
            text="< Back",
            size_hint_x=0.35,
            font_size=dp(15),
            bold=True,
        )
        back_btn.bind(
            on_release=lambda *_: setattr(self.manager, "current", "input")
        )
        top.add_widget(back_btn)
        self.page_label = Label(text="-", font_size=dp(17), bold=True)
        top.add_widget(self.page_label)
        layout.add_widget(top)

        self.qr_image = Image()
        layout.add_widget(self.qr_image)

        nav = BoxLayout(
            size_hint_y=None,
            height=dp(56),
            spacing=dp(8),
        )
        prev_btn = Button(
            text="<",
            font_size=dp(26),
            bold=True,
            size_hint_x=0.3,
        )
        prev_btn.bind(on_release=self.prev)
        nav.add_widget(prev_btn)
        nav.add_widget(Label(
            text="Scan with any QR app",
            font_size=dp(12),
        ))
        next_btn = Button(
            text=">",
            font_size=dp(26),
            bold=True,
            size_hint_x=0.3,
        )
        next_btn.bind(on_release=self.next)
        nav.add_widget(next_btn)
        layout.add_widget(nav)

        save_row = BoxLayout(
            size_hint_y=None,
            height=dp(56),
            spacing=dp(8),
        )
        save_one_btn = Button(
            text="Save This",
            font_size=dp(15),
            bold=True,
            background_color=(0.4, 0.75, 0.95, 1),
        )
        save_one_btn.bind(on_release=self.save_one)
        save_row.add_widget(save_one_btn)

        save_all_btn = Button(
            text="Save All",
            font_size=dp(15),
            bold=True,
            background_color=(0.95, 0.85, 0.45, 1),
        )
        save_all_btn.bind(on_release=self.save_all)
        save_row.add_widget(save_all_btn)
        layout.add_widget(save_row)

        self.footer = Label(
            text="",
            size_hint_y=None,
            height=dp(36),
            font_size=dp(11),
        )
        layout.add_widget(self.footer)
        self.add_widget(layout)

    def prev(self, *args):
        app = App.get_running_app()
        if not app.chunks:
            return
        app.current_idx = (app.current_idx - 1) % len(app.chunks)
        app.render_qr()

    def next(self, *args):
        app = App.get_running_app()
        if not app.chunks:
            return
        app.current_idx = (app.current_idx + 1) % len(app.chunks)
        app.render_qr()

    def save_one(self, *args):
        app = App.get_running_app()
        if not app.chunks:
            return
        try:
            output_dir = get_save_dir()
            path = output_dir / f"qr_{app.current_idx + 1:04d}.png"
            app.make_qr(app.chunks[app.current_idx]).save(path)
            self.footer.text = f"Saved: {path}"
        except Exception as exc:
            self.footer.text = f"Save failed: {exc}"

    def save_all(self, *args):
        app = App.get_running_app()
        if not app.chunks:
            return
        try:
            output_dir = get_save_dir()
            for index, data in enumerate(app.chunks):
                path = output_dir / f"qr_{index + 1:04d}.png"
                app.make_qr(data).save(path)
            self.footer.text = f"Saved {len(app.chunks)} files → {output_dir}"
        except Exception as exc:
            self.footer.text = f"Save failed: {exc}"


# ---------- application ----------
class QRApp(App):
    def build(self):
        self.title = "Text2QR Pro"
        self.chunks = []
        self.current_idx = 0

        self.sm = ScreenManager(transition=SlideTransition())
        self.sm.add_widget(InputScreen(name="input"))
        self.sm.add_widget(QRScreen(name="qr"))
        return self.sm

    def make_qr(self, data: str):
        qr = qrcode.QRCode(
            version=None,
            error_correction=ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        return qr.make_image(
            fill_color="black",
            back_color="white",
        ).get_image()

    def render_qr(self):
        if not self.chunks:
            return

        image = self.make_qr(self.chunks[self.current_idx])
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        core_image = CoreImage(buffer, ext="png")

        qr_screen = self.sm.get_screen("qr")
        qr_screen.qr_image.texture = core_image.texture
        qr_screen.page_label.text = (
            f"{self.current_idx + 1} / {len(self.chunks)}"
        )


if __name__ == "__main__":
    QRApp().run()
