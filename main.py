import math
import html
import random
import struct
import sys
import os
import json
import shutil
import tempfile
from array import array
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from PySide6.QtCore import (
    Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve, QRectF, QPointF,
    QIODevice, QUrl, QThread
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath, QLinearGradient
from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QScrollArea, QFrame, QProgressBar,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QCheckBox, QListWidget,
    QListWidgetItem, QSpinBox, QButtonGroup, QGraphicsOpacityEffect, QSlider,
    QSplitter, QSizePolicy
)

import db

APP_TITLE = "NoToto"

THEMES = {
    "strawberry_night": {
        "label": "🍓 Strawberry Night", "bg1": "#171821", "bg2": "#20192B",
        "panel": "#22212F", "panel2": "#27253A", "border": "#3A3850",
        "text": "#F6F3FA", "muted": "#B7B0C4", "accent": "#F0A8C7",
        "accent_hover": "#F7B4D2", "badge": "#4A3143", "field": "#1E1D2A",
        "danger": "#D89AA8", "progress": "#343142",
    },
    "mint_milk": {
        "label": "🍵 Mint Milk", "bg1": "#121E1C", "bg2": "#1B2A28",
        "panel": "#20302F", "panel2": "#243635", "border": "#365150",
        "text": "#F5FCFA", "muted": "#B8CCC9", "accent": "#9DE5C3",
        "accent_hover": "#B8F2D7", "badge": "#34514A", "field": "#1A2928",
        "danger": "#F0B4BE", "progress": "#314442",
    },
    "peach_pop": {
        "label": "🍑 Peach Pop", "bg1": "#221718", "bg2": "#2C1D22",
        "panel": "#34262A", "panel2": "#3A282A", "border": "#5B4048",
        "text": "#FFF7F5", "muted": "#D3BCBE", "accent": "#FFC19E",
        "accent_hover": "#FFD2B7", "badge": "#604045", "field": "#2B2024",
        "danger": "#F3B1B1", "progress": "#4A363B",
    },
    "lavender_dream": {
        "label": "🫐 Lavender Dream", "bg1": "#1A1829", "bg2": "#232038",
        "panel": "#2B2844", "panel2": "#322F52", "border": "#423E66",
        "text": "#F8F7FF", "muted": "#C5C0E5", "accent": "#C4B5FD",
        "accent_hover": "#DDD6FE", "badge": "#483F73", "field": "#211E36",
        "danger": "#FDA4AF", "progress": "#383357",
    },
    "honey_butter": {
        "label": "🍯 Honey Butter", "bg1": "#211A12", "bg2": "#2D2318",
        "panel": "#382D1F", "panel2": "#403323", "border": "#5E4C34",
        "text": "#FFFDF7", "muted": "#DDCFB8", "accent": "#FCD34D",
        "accent_hover": "#FDE68A", "badge": "#634E31", "field": "#2B2116",
        "danger": "#F87171", "progress": "#4E3E29",
    },
    "cherry_blossom": {
        "label": "🌸 Cherry Blossom", "bg1": "#24171E", "bg2": "#2F1D27",
        "panel": "#38232F", "panel2": "#422938", "border": "#5C394D",
        "text": "#FFF5F9", "muted": "#DBBFCE", "accent": "#F472B6",
        "accent_hover": "#F9A8D4", "badge": "#61334D", "field": "#2B1B24",
        "danger": "#FB7185", "progress": "#4A2D3E",
    },
}

CATEGORY_ICON = {
    "Study": "📚", "Work": "💼", "Personal": "🌷",
    "Health": "🏃", "Creative": "🎨",
}
PRIORITY_ICON = {"low": "🟢", "medium": "🟡", "high": "🔴"}

MODE_FRUIT = {
    "focus": "tomato",
    "short_break": "peach",
    "long_break": "blueberry",
    "custom": "strawberry",
}


def fmt_timer(seconds):
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def fmt_duration(seconds):
    mins = max(0, int(seconds)) // 60
    h, m = divmod(mins, 60)
    return f"{h}h {m}m" if h else f"{m}m"


class Card(QFrame):
    def __init__(self, name="card", parent=None):
        super().__init__(parent)
        self.setObjectName(name)


class FruitMascot(QWidget):
    """Cute bouncing fruit mascot that changes per mode."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(86, 86)
        self.kind = "tomato"
        self.running = False
        self.phase = 0.0
        self.bounce = 0.0
        self.blink = False

        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._step)
        self.timer.start()

        self.blink_timer = QTimer(self)
        self.blink_timer.setInterval(2500)
        self.blink_timer.timeout.connect(self._blink)
        self.blink_timer.start()

    def set_mode(self, mode):
        self.kind = MODE_FRUIT.get(mode, "tomato")
        self.update()

    def set_running(self, running):
        self.running = running

    def _blink(self):
        self.blink = True
        self.update()
        QTimer.singleShot(120, self._open_eyes)

    def _open_eyes(self):
        self.blink = False
        self.update()

    def _step(self):
        speed = 0.18 if self.running else 0.08
        self.phase += speed
        self.bounce = math.sin(self.phase) * (7.5 if self.running else 2.5)
        self.update()

    def _face(self, p, cx, cy, wink=False, happy=True):
        p.setPen(QPen(QColor("#30232d"), 3, Qt.SolidLine, Qt.RoundCap))
        if self.blink or wink:
            p.drawLine(cx - 11, cy - 4, cx - 5, cy - 4)
            p.drawLine(cx + 5, cy - 4, cx + 11, cy - 4)
        else:
            p.drawPoint(cx - 8, cy - 4)
            p.drawPoint(cx + 8, cy - 4)

        p.setPen(QPen(QColor("#30232d"), 2, Qt.SolidLine, Qt.RoundCap))
        if happy:
            p.drawArc(QRectF(cx - 9, cy - 1, 18, 12), 200 * 16, 140 * 16)
        else:
            p.drawArc(QRectF(cx - 9, cy + 2, 18, 10), 20 * 16, 140 * 16)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(0, self.bounce)

        cx, cy = 43, 42
        shadow_alpha = 48 + int((abs(self.bounce) / 8.0) * 30)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, shadow_alpha))
        p.drawEllipse(QRectF(24, 68 - self.bounce * 0.25, 38, 8))

        if self.kind == "tomato":
            grad = QLinearGradient(QPointF(28, 20), QPointF(60, 62))
            grad.setColorAt(0, QColor("#ff7a8e"))
            grad.setColorAt(1, QColor("#ef476f"))
            p.setBrush(QBrush(grad))
            p.drawEllipse(QRectF(17, 16, 52, 50))
            p.setBrush(QColor("#70d68d"))
            leaf = QPainterPath()
            leaf.moveTo(43, 16); leaf.lineTo(34, 6); leaf.lineTo(40, 18)
            leaf.lineTo(49, 6); leaf.lineTo(46, 18); leaf.lineTo(56, 11)
            leaf.lineTo(47, 21); leaf.closeSubpath()
            p.drawPath(leaf)
            p.setBrush(QColor(255, 180, 190, 180))
            p.drawEllipse(QPointF(29, 45), 5, 3)
            p.drawEllipse(QPointF(57, 45), 5, 3)
            self._face(p, cx, cy, happy=True)

        elif self.kind == "peach":
            grad = QLinearGradient(QPointF(25, 18), QPointF(63, 66))
            grad.setColorAt(0, QColor("#ffd6b0"))
            grad.setColorAt(1, QColor("#ff9e7d"))
            p.setBrush(QBrush(grad))
            path = QPainterPath()
            path.moveTo(43, 18)
            path.cubicTo(70, 14, 70, 58, 43, 64)
            path.cubicTo(16, 58, 16, 14, 43, 18)
            p.drawPath(path)
            p.setBrush(QColor("#8fe388"))
            p.drawEllipse(QRectF(38, 9, 14, 7))
            p.setBrush(QColor(255, 185, 170, 170))
            p.drawEllipse(QPointF(31, 46), 5, 3)
            p.drawEllipse(QPointF(55, 46), 5, 3)
            self._face(p, cx, cy, happy=True)
            p.setPen(QPen(QColor("#8fe388"), 2))
            p.drawArc(QRectF(58, 21, 12, 12), 150 * 16, 160 * 16)  # little break swirl

        elif self.kind == "blueberry":
            grad = QLinearGradient(QPointF(22, 16), QPointF(63, 63))
            grad.setColorAt(0, QColor("#85a9ff"))
            grad.setColorAt(1, QColor("#5168d8"))
            p.setBrush(QBrush(grad))
            p.drawEllipse(QRectF(18, 16, 50, 50))
            p.setBrush(QColor("#b8c7ff"))
            p.drawEllipse(QRectF(33, 14, 20, 8))
            p.setBrush(QColor(180, 200, 255, 140))
            p.drawEllipse(QPointF(31, 45), 5, 3)
            p.drawEllipse(QPointF(55, 45), 5, 3)
            self._face(p, cx, cy, wink=True, happy=False)
            p.setPen(QPen(QColor("#ffe18c"), 2))
            p.drawArc(QRectF(57, 16, 13, 13), 40 * 16, 220 * 16)  # moon hint

        else:  # strawberry
            grad = QLinearGradient(QPointF(22, 18), QPointF(62, 65))
            grad.setColorAt(0, QColor("#ff8fb1"))
            grad.setColorAt(1, QColor("#e53e6a"))
            p.setBrush(QBrush(grad))
            berry = QPainterPath()
            berry.moveTo(43, 18)
            berry.cubicTo(65, 20, 65, 52, 43, 66)
            berry.cubicTo(21, 52, 21, 20, 43, 18)
            p.drawPath(berry)
            p.setBrush(QColor("#72de8c"))
            leaf = QPainterPath()
            leaf.moveTo(43, 17); leaf.lineTo(32, 9); leaf.lineTo(39, 19)
            leaf.lineTo(47, 8); leaf.lineTo(46, 19); leaf.lineTo(56, 11)
            leaf.lineTo(47, 22); leaf.closeSubpath()
            p.drawPath(leaf)
            p.setBrush(QColor("#ffcee0"))
            for px, py in [(31,31),(43,29),(53,35),(35,44),(50,47)]:
                p.drawEllipse(QRectF(px, py, 3, 3))
            self._face(p, cx, cy, happy=True)


class TimerRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total = 1500
        self.remaining = 1500
        self.accent = QColor("#F0A8C7")
        self.glow = 0.0
        self.setMinimumSize(330, 330)

    def set_values(self, remaining, total, accent):
        self.remaining = max(0, remaining)
        self.total = max(1, total)
        self.accent = QColor(accent)
        self.update()

    def set_glow(self, value):
        self.glow = float(value)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height())
        rect = QRectF((self.width() - side) / 2 + 16, (self.height() - side) / 2 + 16, side - 32, side - 32)

        if self.glow > 0:
            glow = QColor(self.accent)
            glow.setAlpha(int(35 + self.glow * 70))
            p.setPen(QPen(glow, 22 + self.glow * 6))
            p.drawEllipse(rect.adjusted(6, 6, -6, -6))

        p.setPen(QPen(QColor(255, 255, 255, 20), 10, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 0, 360 * 16)

        ratio = self.remaining / self.total
        span = int(-360 * ratio * 16)
        p.setPen(QPen(self.accent, 10, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 90 * 16, span)


class AmbientSoundDevice(QIODevice):
    """Generates procedural ambient audio in real time."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = None
        self.volume = 0.25
        self.sample_rate = 22050
        self._time = 0
        self._rand = random.Random(42)
        self._fire = 0.0
        self._chirp_phase = 0.0
        self._last_mode = None

    def start(self):
        self.open(QIODevice.ReadOnly)

    def stop(self):
        self.close()

    def set_mode(self, mode):
        self.mode = mode
        self._time = 0
        self._last_mode = mode

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))

    def readData(self, maxlen):
        if not self.mode:
            return bytes(maxlen)
        samples = maxlen // 2  # int16 mono
        out = array('h')
        sr = self.sample_rate

        for _ in range(samples):
            t = self._time / sr
            base = 0.0

            if self.mode == "rain":
                noise = self._rand.uniform(-1, 1)
                low = math.sin(2 * math.pi * 200 * t) * 0.02
                drops = 0.20 if self._rand.random() < 0.0025 else 0.0
                base = noise * 0.18 + low + drops * self._rand.uniform(-1, 1)

            elif self.mode == "waves":
                swell = 0.55 + 0.45 * math.sin(2 * math.pi * 0.18 * t)
                noise = self._rand.uniform(-1, 1) * 0.14
                rumble = math.sin(2 * math.pi * 65 * t) * 0.12
                base = (noise + rumble) * swell

            elif self.mode == "forest":
                wind = self._rand.uniform(-1, 1) * 0.12 * (0.6 + 0.4 * math.sin(2 * math.pi * 0.08 * t))
                chirp = 0.0
                if int(t * 2.4) % 5 == 0:
                    chirp = math.sin(2 * math.pi * (950 + 150 * math.sin(2 * math.pi * 9 * t)) * t) * 0.08
                base = wind + chirp

            elif self.mode == "fire":
                noise = self._rand.uniform(-1, 1) * 0.15
                if self._rand.random() < 0.01:
                    self._fire = self._rand.uniform(0.2, 0.9)
                self._fire *= 0.985
                crackle = self._fire * self._rand.uniform(-1, 1)
                base = noise + crackle * 0.55

            elif self.mode == "cafe":
                murmur = self._rand.uniform(-1, 1) * 0.08
                hum = math.sin(2 * math.pi * 130 * t) * 0.06
                clink = 0.0
                if self._rand.random() < 0.0008:
                    clink = math.sin(2 * math.pi * 1600 * t) * 0.32
                base = murmur + hum + clink

            sample = int(max(-1.0, min(1.0, base * self.volume)) * 32767)
            out.append(sample)
            self._time += 1

        return out.tobytes()

    def writeData(self, data):
        return 0

    def bytesAvailable(self):
        return 4096 + super().bytesAvailable()


class AmbientPanel(Card):
    modeChanged = Signal(object)
    volumeChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__("ambientCard", parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        head = QHBoxLayout()
        title = QLabel("🎧 Cozy Ambient Sounds")
        title.setObjectName("sectionTitle")
        head.addWidget(title)
        head.addStretch()

        self.status = QLabel("Off")
        self.status.setObjectName("muted")
        head.addWidget(self.status)
        root.addLayout(head)

        buttons = QHBoxLayout()
        self.buttons = {}
        for key, label in [
            ("rain", "🌧 Rain"),
            ("waves", "🌊 Waves"),
            ("forest", "🌲 Forest"),
            ("fire", "🔥 Fire"),
            ("cafe", "☕ Cafe"),
        ]:
            b = QPushButton(label)
            b.setCheckable(True)
            b.clicked.connect(lambda checked, k=key: self._choose(k if checked else None))
            self.buttons[key] = b
            buttons.addWidget(b)
        root.addLayout(buttons)

        off_row = QHBoxLayout()
        stop = QPushButton("⏹ Stop Sound")
        stop.clicked.connect(lambda: self._choose(None))
        off_row.addWidget(stop)
        off_row.addStretch()
        root.addLayout(off_row)

        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel("Volume"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(25)
        self.slider.valueChanged.connect(lambda v: self.volumeChanged.emit(v / 100))
        volume_row.addWidget(self.slider)
        root.addLayout(volume_row)

        helper = QLabel("Real procedural ambient audio is generated now, so Rain / Waves / Forest / Fire / Cafe should actually make sound.")
        helper.setWordWrap(True)
        helper.setObjectName("muted")
        root.addWidget(helper)

    def _choose(self, key):
        for k, b in self.buttons.items():
            b.blockSignals(True)
            b.setChecked(k == key)
            b.blockSignals(False)

        self.status.setText(key.title() if key else "Off")
        self.modeChanged.emit(key)


class WheelPickerDialog(QDialog):
    def __init__(self, parent=None, hours=0, minutes=25, title="Pick Custom Time"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(400, 430)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        heading = QLabel(f"🕒  {title}")
        heading.setObjectName("dialogTitle")
        root.addWidget(heading)

        helper = QLabel("Scroll or click numbers to choose exact hours and minutes.")
        helper.setObjectName("muted")
        helper.setWordWrap(True)
        root.addWidget(helper)

        row = QHBoxLayout()
        self.hours = self._wheel(24, hours)
        self.minutes = self._wheel(60, minutes)
        row.addWidget(self._wheel_box("Hours", self.hours))
        row.addWidget(self._wheel_box("Minutes", self.minutes))
        root.addLayout(row)

        presets = QHBoxLayout()
        for mins in (15, 25, 45, 60):
            b = QPushButton(f"{mins}m")
            b.clicked.connect(lambda _, m=mins: self._preset(m))
            presets.addWidget(b)
        root.addLayout(presets)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _wheel(self, n, current):
        w = QListWidget()
        w.setObjectName("wheel")
        w.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        w.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for i in range(n):
            item = QListWidgetItem(f"{i:02d}")
            item.setTextAlignment(Qt.AlignCenter)
            w.addItem(item)
        w.setCurrentRow(current)
        w.scrollToItem(w.currentItem(), QListWidget.PositionAtCenter)
        w.currentRowChanged.connect(
            lambda row, ww=w: ww.scrollToItem(
                ww.item(row), QListWidget.PositionAtCenter
            ) if row >= 0 else None
        )
        return w

    def _wheel_box(self, label, widget):
        box = Card("wheelBox")
        lay = QVBoxLayout(box)
        lbl = QLabel(label.upper())
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setObjectName("tinyTitle")
        lay.addWidget(lbl)
        lay.addWidget(widget)
        return box

    def _preset(self, mins):
        self.hours.setCurrentRow(mins // 60)
        self.minutes.setCurrentRow(mins % 60)

    def value(self):
        return self.hours.currentRow(), self.minutes.currentRow()


class WheelTimeButton(QPushButton):
    def __init__(self, value="09:00", parent=None):
        super().__init__(value, parent)
        self._value = value
        self.setObjectName("wheelTime")
        self.clicked.connect(self.pick)

    def set_value(self, value):
        self._value = value
        self.setText(value)

    def value(self):
        return self._value

    def pick(self):
        try:
            h, m = [int(x) for x in self._value.split(":")]
        except Exception:
            h, m = 9, 0
        d = WheelPickerDialog(self, h, m, "Pick Clock Time")
        if d.exec():
            h, m = d.value()
            self.set_value(f"{h:02d}:{m:02d}")


class SubtaskEditor(QWidget):
    def __init__(self, subtasks=None, parent=None):
        super().__init__(parent)
        self.items = [dict(x) for x in (subtasks or [])]

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        addrow = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Add a small step...")
        add = QPushButton("＋")
        add.setFixedWidth(44)
        add.clicked.connect(self.add_item)
        self.input.returnPressed.connect(self.add_item)
        addrow.addWidget(self.input)
        addrow.addWidget(add)
        root.addLayout(addrow)

        self.list = QListWidget()
        self.list.setObjectName("subtaskEditor")
        self.list.setMaximumHeight(125)
        root.addWidget(self.list)
        self.refresh()

    def add_item(self):
        text = self.input.text().strip()
        if not text:
            return
        self.items.append({"title": text, "completed": False})
        self.input.clear()
        self.refresh()

    def refresh(self):
        self.list.clear()
        for idx, sub in enumerate(self.items):
            item = QListWidgetItem(("✓ " if sub.get("completed") else "○ ") + sub["title"])
            item.setData(Qt.UserRole, idx)
            self.list.addItem(item)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.list.currentItem():
            idx = self.list.currentItem().data(Qt.UserRole)
            self.items.pop(idx)
            self.refresh()
            return
        super().keyPressEvent(event)

    def value(self):
        return [dict(x) for x in self.items]


class TaskDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("Edit Quest" if task else "New Focus Quest")
        self.setMinimumWidth(560)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(16)

        title = QLabel("✏️ Edit Quest" if task else "✨ New Focus Quest")
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        form = QFormLayout()
        form.setSpacing(13)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("What do you want to accomplish?")
        form.addRow("QUEST TITLE *", self.title_edit)

        row = QWidget()
        rowlay = QHBoxLayout(row)
        rowlay.setContentsMargins(0, 0, 0, 0)
        self.category = QComboBox()
        for c in ("Study", "Work", "Personal", "Health", "Creative"):
            self.category.addItem(f"{CATEGORY_ICON[c]} {c}", c)
        self.priority = QComboBox()
        for p in ("low", "medium", "high"):
            self.priority.addItem(f"{PRIORITY_ICON[p]} {p.title()}", p)
        rowlay.addWidget(self.category)
        rowlay.addWidget(self.priority)
        form.addRow("CATEGORY / PRIORITY", row)

        timerow = QWidget()
        tl = QHBoxLayout(timerow)
        tl.setContentsMargins(0, 0, 0, 0)
        self.start_time = WheelTimeButton("09:00")
        self.end_time = WheelTimeButton("10:00")
        tl.addWidget(self.start_time)
        tl.addWidget(QLabel("→"))
        tl.addWidget(self.end_time)
        form.addRow("SCHEDULE", timerow)

        durrow = QWidget()
        dl = QHBoxLayout(durrow)
        dl.setContentsMargins(0, 0, 0, 0)
        self.est_h = QSpinBox(); self.est_h.setRange(0, 99); self.est_h.setWrapping(True)
        self.est_m = QSpinBox(); self.est_m.setRange(0, 59); self.est_m.setWrapping(True)
        self.work_h = QSpinBox(); self.work_h.setRange(0, 999); self.work_h.setWrapping(True)
        self.work_m = QSpinBox(); self.work_m.setRange(0, 59); self.work_m.setWrapping(True)
        for w in (self.est_h, self.est_m, self.work_h, self.work_m):
            w.setMinimumHeight(42)
        dl.addWidget(QLabel("Target"))
        dl.addWidget(self.est_h); dl.addWidget(QLabel("h"))
        dl.addWidget(self.est_m); dl.addWidget(QLabel("m"))
        dl.addSpacing(14)
        dl.addWidget(QLabel("Worked"))
        dl.addWidget(self.work_h); dl.addWidget(QLabel("h"))
        dl.addWidget(self.work_m); dl.addWidget(QLabel("m"))
        form.addRow("TIME", durrow)

        self.subtasks = SubtaskEditor()
        form.addRow("CHECKLIST", self.subtasks)

        self.completed = QCheckBox("Mark quest as completed")
        form.addRow("", self.completed)

        root.addLayout(form)

        note = QLabel("Tip: click Start/End to open the wheel picker. Mouse wheel also works on numeric fields.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        root.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        if task:
            self.title_edit.setText(task["title"])
            self.start_time.set_value(task.get("start_time") or "09:00")
            self.end_time.set_value(task.get("end_time") or "10:00")
            self.est_h.setValue(int(task.get("estimated_minutes", 0)) // 60)
            self.est_m.setValue(int(task.get("estimated_minutes", 0)) % 60)
            worked_m = int(task.get("worked_seconds", 0)) // 60
            self.work_h.setValue(worked_m // 60)
            self.work_m.setValue(worked_m % 60)
            self.completed.setChecked(bool(task.get("completed")))
            self.category.setCurrentIndex(max(0, self.category.findData(task.get("category", "Study"))))
            self.priority.setCurrentIndex(max(0, self.priority.findData(task.get("priority", "medium"))))
            self.subtasks.items = db.get_subtasks(task["id"])
            self.subtasks.refresh()
        else:
            self.est_m.setValue(25)

        self._fade = QPropertyAnimation(self, b"windowOpacity")
        self._fade.setDuration(200)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.OutCubic)

    def showEvent(self, event):
        super().showEvent(event)
        self.setWindowOpacity(0)
        self._fade.start()

    def _accept(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, APP_TITLE, "Please enter a quest title.")
            return
        self.accept()

    def value(self):
        return {
            "title": self.title_edit.text().strip(),
            "start_time": self.start_time.value(),
            "end_time": self.end_time.value(),
            "estimated_minutes": self.est_h.value() * 60 + self.est_m.value(),
            "worked_seconds": (self.work_h.value() * 60 + self.work_m.value()) * 60,
            "completed": self.completed.isChecked(),
            "category": self.category.currentData(),
            "priority": self.priority.currentData(),
            "subtasks": self.subtasks.value(),
        }



class TaskCard(Card):
    """Compact database-row style task inspired by Notion's information density."""
    selectFocus = Signal(int)
    editTask = Signal(int)
    deleteTask = Signal(int)
    completedChanged = Signal(int, bool)
    subtaskToggle = Signal(int)

    def __init__(self, task, active, compact=False, parent=None):
        super().__init__("taskRowActive" if active else "taskRow", parent)
        self.task = task
        self.compact = compact
        self.expanded = False

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 10, 10)
        root.setSpacing(7)

        main = QHBoxLayout()
        main.setSpacing(8)

        check = QCheckBox()
        check.setChecked(bool(task["completed"]))
        check.setToolTip("Mark complete")
        check.stateChanged.connect(
            lambda s: self.completedChanged.emit(task["id"], s == Qt.Checked.value)
        )
        main.addWidget(check, 0)

        title = QLabel(task["title"])
        title.setObjectName("taskDone" if task["completed"] else "taskName")
        title.setWordWrap(False)
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        main.addWidget(title, 1)

        if active:
            badge = QLabel("🍅 Now")
            badge.setObjectName("activeBadge")
            main.addWidget(badge)

        category = QLabel(
            f"{CATEGORY_ICON.get(task.get('category','Study'),'📌')} {task.get('category','Study')}"
        )
        category.setObjectName("propertyChip")
        main.addWidget(category)

        priority = QLabel(f"{PRIORITY_ICON.get(task.get('priority','medium'),'🟡')} {task.get('priority','medium').title()}")
        priority.setObjectName("propertyChip")
        if not compact:
            main.addWidget(priority)

        if not task["completed"]:
            focus = QPushButton("▶")
            focus.setObjectName("rowIconPrimary")
            focus.setFixedSize(36, 32)
            focus.setToolTip("Focus this quest")
            focus.clicked.connect(lambda: self.selectFocus.emit(task["id"]))
            main.addWidget(focus)

        edit = QPushButton("•••")
        edit.setObjectName("rowIcon")
        edit.setFixedSize(40, 32)
        edit.setToolTip("Edit quest")
        edit.clicked.connect(lambda: self.editTask.emit(task["id"]))
        main.addWidget(edit)

        delete = QPushButton("×")
        delete.setObjectName("rowIconDanger")
        delete.setFixedSize(34, 32)
        delete.setToolTip("Delete quest")
        delete.clicked.connect(lambda: self.deleteTask.emit(task["id"]))
        if not compact:
            main.addWidget(delete)

        root.addLayout(main)

        details = QHBoxLayout()
        details.setSpacing(12)

        schedule = task.get("start_time", "") or "—"
        end = task.get("end_time", "") or "—"
        schedule_label = QLabel(f"🕒 {schedule} → {end}")
        schedule_label.setObjectName("taskProperty")
        details.addWidget(schedule_label)

        est = int(task.get("estimated_minutes", 0))
        worked = int(task.get("worked_seconds", 0))
        target_sec = max(1, est * 60)
        progress = min(100, round(worked / target_sec * 100)) if est else 0

        estimate_label = QLabel(f"🎯 {est}m")
        estimate_label.setObjectName("taskProperty")
        details.addWidget(estimate_label)

        worked_label = QLabel(f"✨ {fmt_duration(worked)}")
        worked_label.setObjectName("taskProperty")
        if not compact:
            details.addWidget(worked_label)

        subs = db.get_subtasks(task["id"])
        if subs:
            done = sum(1 for x in subs if x["completed"])
            subbtn = QPushButton(f"▸ {done}/{len(subs)} sub-items")
            subbtn.setObjectName("subtaskToggle")
            subbtn.clicked.connect(self.toggle_subtasks)
            details.addWidget(subbtn)

        details.addStretch()

        progress_label = QLabel(f"{progress}%")
        progress_label.setObjectName("taskProperty")
        details.addWidget(progress_label)

        mini_progress = QProgressBar()
        mini_progress.setRange(0, 100)
        mini_progress.setValue(progress)
        mini_progress.setTextVisible(False)
        mini_progress.setFixedSize(84 if not compact else 58, 6)
        details.addWidget(mini_progress)

        root.addLayout(details)

        self.sub_box = QWidget()
        sub_layout = QVBoxLayout(self.sub_box)
        sub_layout.setContentsMargins(28, 4, 0, 2)
        sub_layout.setSpacing(4)
        for s in subs:
            cb = QCheckBox(s["title"])
            cb.setChecked(bool(s["completed"]))
            cb.stateChanged.connect(lambda _, sid=s["id"]: self.subtaskToggle.emit(sid))
            sub_layout.addWidget(cb)
        self.sub_box.setVisible(False)
        root.addWidget(self.sub_box)

    def toggle_subtasks(self):
        self.expanded = not self.expanded
        self.sub_box.setVisible(self.expanded)

    def mouseDoubleClickEvent(self, event):
        self.editTask.emit(self.task["id"])
        super().mouseDoubleClickEvent(event)


class StatCard(Card):
    def __init__(self, emoji, title, value, subtext, parent=None):
        super().__init__("statCard", parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        t = QLabel(f"{emoji}  {title}")
        t.setObjectName("statTitle")
        self.value = QLabel(value)
        self.value.setObjectName("statValue")
        self.sub = QLabel(subtext)
        self.sub.setObjectName("muted")
        self.sub.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(self.value)
        lay.addWidget(self.sub)







class YouTubeAudioResolver(QThread):
    resolved = Signal(int, str, str, str)
    failed = Signal(int, str)
    progress = Signal(int, int)

    def __init__(self, url, generation, parent=None):
        super().__init__(parent)
        self.url = url
        self.generation = generation

    def run(self):
        download_dir = tempfile.mkdtemp(prefix="nototo-audio-")
        try:
            from yt_dlp import YoutubeDL
            from yt_dlp.utils import DownloadError

            def report_progress(data):
                if self.isInterruptionRequested():
                    raise DownloadError("Audio download cancelled")
                if data.get("status") == "downloading":
                    total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                    downloaded = data.get("downloaded_bytes", 0)
                    percent = int(downloaded * 100 / total) if total else 0
                    self.progress.emit(self.generation, min(99, percent))

            options = {
                "format": "bestaudio[ext=m4a]/bestaudio",
                "outtmpl": os.path.join(download_dir, "audio.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
                "no_color": True,
                "noplaylist": True,
                "http_chunk_size": 10 * 1024 * 1024,
                "socket_timeout": 10,
                "retries": 1,
                "extractor_retries": 1,
                "progress_hooks": [report_progress],
            }
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(self.url, download=True)

            audio_path = ydl.prepare_filename(info) if info else None
            if not audio_path or not os.path.isfile(audio_path):
                raise RuntimeError("The audio download did not produce a playable file.")
            title = info.get("title") or self.url
            self.progress.emit(self.generation, 100)
            self.resolved.emit(self.generation, audio_path, title, download_dir)
        except Exception as exc:
            shutil.rmtree(download_dir, ignore_errors=True)
            self.failed.emit(self.generation, str(exc))


class MusicLinkPanel(Card):
    """Audio-only YouTube/music player using yt-dlp and Qt Multimedia."""
    def __init__(self, parent=None):
        super().__init__("musicCard", parent)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.errorOccurred.connect(self._on_playback_error)

        self.current_url = ""
        self.is_playing = False
        self.loading = False
        self._resolve_generation = 0
        self._resolver_threads = set()
        self._audio_temp_dirs = set()

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(9)

        head = QHBoxLayout()
        title = QLabel("🎵 Music")
        title.setObjectName("sectionTitleSmall")
        head.addWidget(title)
        head.addStretch()
        self.state = QLabel("Ready")
        self.state.setObjectName("muted")
        head.addWidget(self.state)
        root.addLayout(head)

        controls = QHBoxLayout()
        controls.setSpacing(7)

        self.url = QLineEdit()
        self.url.setPlaceholderText("Paste YouTube / audio link…")
        self.url.setText(db.get_setting("music_url", ""))
        self.url.returnPressed.connect(self.play_from_input)
        controls.addWidget(self.url, 1)

        self.play_btn = QPushButton("▶")
        self.play_btn.setObjectName("mediaButton")
        self.play_btn.setFixedSize(38, 34)
        self.play_btn.setToolTip("Play / Pause")
        self.play_btn.clicked.connect(self.toggle)
        controls.addWidget(self.play_btn)

        self.stop_btn = QPushButton("■")
        self.stop_btn.setObjectName("mediaButton")
        self.stop_btn.setFixedSize(38, 34)
        self.stop_btn.setToolTip("Stop")
        self.stop_btn.clicked.connect(self.stop)
        controls.addWidget(self.stop_btn)

        self.loop = QCheckBox("Loop")
        self.loop.setChecked(db.get_setting("music_loop", "1") == "1")
        self.loop.toggled.connect(self.set_loop)
        controls.addWidget(self.loop)

        root.addLayout(controls)

        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel("Volume"))
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(int(float(db.get_setting("music_volume", "0.35") or 0.35) * 100))
        self.volume.valueChanged.connect(self.set_volume)
        volume_row.addWidget(self.volume)
        root.addLayout(volume_row)

        self.track_label = QLabel("No track loaded")
        self.track_label.setObjectName("musicTrack")
        self.track_label.setWordWrap(True)
        root.addWidget(self.track_label)

        self.hint = QLabel(
            "Audio only. yt-dlp downloads audio before playback; no video is downloaded."
        )
        self.hint.setWordWrap(True)
        self.hint.setObjectName("responsiveHint")
        root.addWidget(self.hint)

        self.audio_output.setVolume(self.volume.value() / 100)
        self.set_loop(self.loop.isChecked())

    def play_from_input(self):
        url = self.url.text().strip()
        if not url:
            self.state.setText("Paste a link")
            return

        self._resolve_generation += 1
        generation = self._resolve_generation
        for resolver in self._resolver_threads:
            resolver.requestInterruption()
        self.loading = True
        self.player.stop()
        self.player.setSource(QUrl())
        db.set_setting("music_url", url)
        self.current_url = url
        self.track_label.setText(url)
        self.state.setText("Downloading audio…")
        self.play_btn.setText("…")

        resolver = YouTubeAudioResolver(url, generation, self)
        resolver.resolved.connect(self._on_audio_resolved)
        resolver.failed.connect(self._on_audio_resolve_failed)
        resolver.progress.connect(self._on_download_progress)
        resolver.finished.connect(self._on_resolver_finished)
        self._resolver_threads.add(resolver)
        resolver.start()

    def _on_download_progress(self, generation, percent):
        if generation == self._resolve_generation:
            self.state.setText(f"Downloading audio… {percent}%")

    def _on_audio_resolved(self, generation, audio_path, title, download_dir):
        if generation != self._resolve_generation:
            shutil.rmtree(download_dir, ignore_errors=True)
            return
        self.loading = False
        self._audio_temp_dirs.add(download_dir)
        self.track_label.setText(title)
        self.player.setSource(QUrl.fromLocalFile(audio_path))
        self.player.play()

    def _on_audio_resolve_failed(self, generation, message):
        if generation != self._resolve_generation:
            return
        self.loading = False
        self.current_url = ""
        self.is_playing = False
        self.play_btn.setText("▶")
        self.state.setText("Could not load audio")
        self.hint.setText(message)

    def _on_resolver_finished(self):
        resolver = self.sender()
        if resolver:
            self._resolver_threads.discard(resolver)
            resolver.deleteLater()

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.is_playing = True
            self.play_btn.setText("Ⅱ")
            self.state.setText("Playing audio")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.is_playing = False
            self.play_btn.setText("▶")
            self.state.setText("Paused")
        elif not self.loading:
            self.is_playing = False
            self.play_btn.setText("▶")

    def _on_playback_error(self, _error, message):
        if message:
            self.loading = False
            self.is_playing = False
            self.play_btn.setText("▶")
            self.state.setText("Playback error")
            self.hint.setText(message)

    def toggle(self):
        typed = self.url.text().strip()

        # New / changed link -> load it.
        if not self.current_url or typed != self.current_url:
            self.play_from_input()
            return

        if self.loading:
            return

        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.player.play()
        else:
            self.play_from_input()

    def stop(self):
        self._resolve_generation += 1
        for resolver in self._resolver_threads:
            resolver.requestInterruption()
        self.loading = False
        self.player.stop()
        self.is_playing = False
        self.play_btn.setText("▶")
        self.state.setText("Stopped")

    def set_volume(self, value):
        db.set_setting("music_volume", value / 100)
        self.audio_output.setVolume(value / 100)

    def set_loop(self, enabled):
        db.set_setting("music_loop", "1" if enabled else "0")
        loops = QMediaPlayer.Loops.Infinite if enabled else QMediaPlayer.Loops.Once
        self.player.setLoops(loops)

    def shutdown(self):
        self._resolve_generation += 1
        for resolver in self._resolver_threads:
            resolver.requestInterruption()
        for resolver in list(self._resolver_threads):
            resolver.wait()
        self.player.stop()
        self.player.setSource(QUrl())
        for directory in self._audio_temp_dirs:
            shutil.rmtree(directory, ignore_errors=True)
        self._audio_temp_dirs.clear()

    def set_compact(self, compact):
        self.loop.setText("" if compact else "Loop")
        self.url.setPlaceholderText("Music URL…" if compact else "Paste YouTube / audio link…")
        self.hint.setVisible(not compact)
        self.track_label.setVisible(not compact)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        db.init_db()

        self.theme_key = db.get_setting("theme", "strawberry_night")
        if self.theme_key not in THEMES:
            self.theme_key = "strawberry_night"
        self.muted = db.get_setting("muted", "0") == "1"

        self.mode = "focus"
        self.total_seconds = 25 * 60
        self.remaining = self.total_seconds
        self.running = False
        self.elapsed = 0
        self.started_at = None
        self.active_task_id = None

        self.audio_device = AmbientSoundDevice(self)
        self.audio_format = QAudioFormat()
        self.audio_format.setSampleRate(self.audio_device.sample_rate)
        self.audio_format.setChannelCount(1)
        self.audio_format.setSampleFormat(QAudioFormat.Int16)
        self.audio_sink = QAudioSink(self.audio_format, self)
        self.audio_device.start()
        self.audio_sink.start(self.audio_device)

        self.setWindowTitle("NoToto — Cute Focus Companion")
        self.resize(1280, 860)
        self.setMinimumSize(1000, 720)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.tick)

        self.glow_timer = QTimer(self)
        self.glow_timer.setInterval(40)
        self.glow_timer.timeout.connect(self.animate_glow)
        self.glow_phase = 0.0

        self.build_ui()
        self.apply_theme()
        self.reload_tasks()
        self.refresh_stats()
        self.refresh_timer()
        self.mascot.set_mode(self.mode)
        self.sync_sound_button()

    def build_ui(self):
        # Whole page is scrollable so narrow windows never overlap/clobber widgets.
        shell = QScrollArea()
        shell.setWidgetResizable(True)
        shell.setFrameShape(QFrame.NoFrame)
        shell.setObjectName("pageScroll")
        self.setCentralWidget(shell)

        root = QWidget()
        root.setObjectName("root")
        shell.setWidget(root)

        page = QVBoxLayout(root)
        page.setContentsMargins(20, 16, 20, 20)
        page.setSpacing(14)

        # Header
        self.header = QWidget()
        header = QHBoxLayout(self.header)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        logo = QLabel("🍅")
        logo.setObjectName("logo")
        header.addWidget(logo)

        brand_wrap = QVBoxLayout()
        brand_wrap.setSpacing(0)
        name = QLabel("NoToto  <span style='font-size:9pt;color:#f5a8ca;'>Cute Companion</span>")
        name.setTextFormat(Qt.RichText)
        name.setObjectName("brand")
        brand_wrap.addWidget(name)
        self.brand_sub = QLabel("Focus without making productivity feel like homework.")
        self.brand_sub.setObjectName("muted")
        brand_wrap.addWidget(self.brand_sub)
        header.addLayout(brand_wrap)
        header.addStretch()

        self.sound_btn = QPushButton()
        self.sound_btn.setObjectName("headerButton")
        self.sound_btn.clicked.connect(self.toggle_mute)
        header.addWidget(self.sound_btn)

        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themeSelect")
        for key, t in THEMES.items():
            self.theme_combo.addItem(t["label"], key)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(self.theme_key)))
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        header.addWidget(self.theme_combo)

        self.new_task_btn = QPushButton("＋ New Quest")
        self.new_task_btn.setObjectName("primary")
        self.new_task_btn.clicked.connect(self.add_task)
        header.addWidget(self.new_task_btn)
        page.addWidget(self.header)

        # Stats are reflowed 4x1 -> 2x2 -> hidden detail depending on width.
        self.stats_widget = QWidget()
        self.stats_grid = QGridLayout(self.stats_widget)
        self.stats_grid.setContentsMargins(0, 0, 0, 0)
        self.stats_grid.setHorizontalSpacing(10)
        self.stats_grid.setVerticalSpacing(10)
        self.stat_focus = StatCard("🍅", "Focus", "0m", "Deep-focus time")
        self.stat_done = StatCard("✅", "Done", "0 / 0", "Quest completion")
        self.stat_sessions = StatCard("✨", "Sessions", "0", "Completed rounds")
        self.stat_target = StatCard("🎯", "Progress", "100%", "Overall completion")
        self.stat_cards = [self.stat_focus, self.stat_done, self.stat_sessions, self.stat_target]
        for i, w in enumerate(self.stat_cards):
            self.stats_grid.addWidget(w, 0, i)
        page.addWidget(self.stats_widget)

        # Responsive splitter: side-by-side when wide, stacked when narrow.
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(8)
        page.addWidget(self.main_splitter, 1)

        self.left_panel = QWidget()
        left = QVBoxLayout(self.left_panel)
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(12)

        timer_card = Card("timerCard")
        timer_lay = QVBoxLayout(timer_card)
        timer_lay.setContentsMargins(18, 15, 18, 16)
        timer_lay.setSpacing(9)

        modes = QHBoxLayout()
        modes.setSpacing(7)
        self.mode_group = QButtonGroup(self)
        self.mode_buttons = {}
        for key, label in [
            ("focus", "🍅 Focus 25m"),
            ("short_break", "☕ Break 5m"),
            ("long_break", "🌙 Break 15m"),
        ]:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setObjectName("mode")
            b.clicked.connect(lambda _, k=key: self.set_mode(k))
            self.mode_group.addButton(b)
            self.mode_buttons[key] = b
            modes.addWidget(b)
        self.mode_buttons["focus"].setChecked(True)
        timer_lay.addLayout(modes)

        ringwrap = QWidget()
        ringwrap.setMinimumHeight(330)
        rw = QGridLayout(ringwrap)
        rw.setContentsMargins(0, 0, 0, 0)
        self.ring = TimerRing()
        rw.addWidget(self.ring, 0, 0, Qt.AlignCenter)

        center = QVBoxLayout()
        center.setSpacing(0)
        center.setAlignment(Qt.AlignCenter)
        self.mascot = FruitMascot()
        center.addWidget(self.mascot, 0, Qt.AlignHCenter)
        self.timer_text = QLabel("25:00")
        self.timer_text.setObjectName("timerText")
        self.timer_text.setAlignment(Qt.AlignCenter)
        center.addWidget(self.timer_text)
        self.mode_text = QLabel("FOCUS TIME")
        self.mode_text.setObjectName("modeCaption")
        self.mode_text.setAlignment(Qt.AlignCenter)
        center.addWidget(self.mode_text)
        overlay = QWidget(ringwrap)
        overlay.setLayout(center)
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        rw.addWidget(overlay, 0, 0, Qt.AlignCenter)
        timer_lay.addWidget(ringwrap)

        # One compact action bar. All buttons follow one sizing system.
        self.control_bar = Card("compactControlBar")
        controls = QHBoxLayout(self.control_bar)
        controls.setContentsMargins(8, 7, 8, 7)
        controls.setSpacing(6)

        self.minus_btn = QPushButton("−5")
        self.minus_btn.setObjectName("smallControl")
        self.minus_btn.setToolTip("Subtract 5 minutes")
        self.minus_btn.clicked.connect(lambda: self.adjust_time(-5))
        controls.addWidget(self.minus_btn)

        self.custom_btn = QPushButton("🕒 Custom")
        self.custom_btn.setObjectName("smallControl")
        self.custom_btn.clicked.connect(self.pick_custom_time)
        controls.addWidget(self.custom_btn)

        self.plus_btn = QPushButton("+5")
        self.plus_btn.setObjectName("smallControl")
        self.plus_btn.setToolTip("Add 5 minutes")
        self.plus_btn.clicked.connect(lambda: self.adjust_time(5))
        controls.addWidget(self.plus_btn)

        self.active_combo = QComboBox()
        self.active_combo.setObjectName("compactQuestCombo")
        self.active_combo.currentIndexChanged.connect(self.active_changed)
        controls.addWidget(self.active_combo, 1)

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setObjectName("compactPrimary")
        self.start_btn.clicked.connect(self.toggle_timer)
        controls.addWidget(self.start_btn)

        self.stop_btn = QPushButton("■")
        self.stop_btn.setObjectName("iconControl")
        self.stop_btn.setToolTip("Stop and save")
        self.stop_btn.clicked.connect(lambda: self.finish_session(False))
        controls.addWidget(self.stop_btn)

        self.reset_btn = QPushButton("↻")
        self.reset_btn.setObjectName("iconControl")
        self.reset_btn.setToolTip("Reset timer")
        self.reset_btn.clicked.connect(self.reset_timer)
        controls.addWidget(self.reset_btn)

        timer_lay.addWidget(self.control_bar)

        self.alert = QLabel("")
        self.alert.setAlignment(Qt.AlignCenter)
        self.alert.setObjectName("successText")
        timer_lay.addWidget(self.alert)
        left.addWidget(timer_card)

        self.ambient_panel = AmbientPanel()
        self.ambient_panel.modeChanged.connect(self.set_ambient_mode)
        self.ambient_panel.volumeChanged.connect(self.set_ambient_volume)
        left.addWidget(self.ambient_panel)

        self.music_panel = MusicLinkPanel()
        left.addWidget(self.music_panel)

        self.main_splitter.addWidget(self.left_panel)

        # Notion-inspired task/database side
        self.right_panel = QWidget()
        right = QVBoxLayout(self.right_panel)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(9)

        qhead = QHBoxLayout()
        title = QLabel("Focus Quests")
        title.setObjectName("sectionTitle")
        qhead.addWidget(title)
        qhead.addStretch()
        self.count_label = QLabel("")
        self.count_label.setObjectName("muted")
        qhead.addWidget(self.count_label)
        right.addLayout(qhead)

        toolbar = Card("taskToolbar")
        tools = QHBoxLayout(toolbar)
        tools.setContentsMargins(7, 6, 7, 6)
        tools.setSpacing(5)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search…")
        self.search.textChanged.connect(self.reload_tasks)
        tools.addWidget(self.search, 1)

        self.filter_group = QButtonGroup(self)
        self.filters = {}
        for key, label in (("all", "All"), ("active", "Open"), ("completed", "Done")):
            b = QPushButton(label)
            b.setCheckable(True)
            b.setObjectName("filter")
            b.clicked.connect(self.reload_tasks)
            self.filter_group.addButton(b)
            self.filters[key] = b
            tools.addWidget(b)
        self.filters["all"].setChecked(True)

        quick_new = QPushButton("＋")
        quick_new.setObjectName("rowIconPrimary")
        quick_new.setToolTip("New quest")
        quick_new.setFixedSize(36, 32)
        quick_new.clicked.connect(self.add_task)
        tools.addWidget(quick_new)
        right.addWidget(toolbar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.task_host = QWidget()
        self.task_host.setObjectName("taskHost")
        self.task_layout = QVBoxLayout(self.task_host)
        self.task_layout.setContentsMargins(0, 0, 0, 0)
        self.task_layout.setSpacing(6)
        self.task_layout.addStretch()
        self.scroll.setWidget(self.task_host)
        right.addWidget(self.scroll, 1)

        self.main_splitter.addWidget(self.right_panel)
        self.main_splitter.setStretchFactor(0, 6)
        self.main_splitter.setStretchFactor(1, 5)
        self.main_splitter.setSizes([690, 560])

        self.apply_responsive_layout()

    def sync_sound_button(self):
        self.sound_btn.setText("🔇" if self.muted else "🔊")
        self.sound_btn.setToolTip("Unmute" if self.muted else "Mute")
        self.audio_sink.setVolume(0.0 if self.muted else 1.0)

    def apply_theme(self):
        t = THEMES[self.theme_key]
        self.setStyleSheet(f"""
        #root {{
            background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t['bg1']}, stop:1 {t['bg2']});
        }}
        QWidget {{
            color:{t['text']};
            font-family:"Segoe UI";
            font-size:13px;
        }}
        #brand {{ font-size:22px; font-weight:800; }}
        #logo {{ font-size:27px; }}
        #muted, #taskHost QLabel {{ color:{t['muted']}; }}
        #sectionTitle {{ font-size:18px; font-weight:800; }}
        #statCard, #timerCard, #ambientCard, #musicCard, #wheelBox, #taskToolbar {{
            background:{t['panel']};
            border:1px solid {t['border']};
            border-radius:20px;
        }}
        #statTitle {{ color:{t['muted']}; font-weight:700; }}
        #statValue {{ font-size:24px; font-weight:900; }}
        #timerText {{ font-size:49px; font-weight:900; }}
        #modeCaption {{ color:{t['accent']}; font-weight:900; letter-spacing:2px; }}
        #dialogTitle {{ font-size:20px; font-weight:900; }}
        #tinyTitle {{ color:{t['muted']}; font-size:11px; font-weight:800; }}
        #taskName {{ font-size:15px; font-weight:800; color:{t['text']}; }}
        #taskDone {{ font-size:15px; font-weight:800; color:{t['muted']}; text-decoration:line-through; }}
        #pill {{
            background:{t['badge']}; color:{t['accent_hover']};
            padding:5px 8px; border-radius:9px; font-size:11px;
        }}
        #activeBadge {{
            background:{t['badge']}; color:{t['accent_hover']};
            padding:5px 8px; border-radius:9px; font-weight:800; font-size:10px;
        }}
        #taskRow, #taskRowActive {{
            background:{t['panel']};
            border:1px solid {t['border']};
            border-radius:11px;
        }}
        #taskRowActive {{
            background:{t['panel2']};
            border:1px solid {t['accent']};
        }}
        #propertyChip {{
            background:{t['badge']};
            color:{t['accent_hover']};
            padding:4px 7px;
            border-radius:7px;
            font-size:10px;
            font-weight:700;
        }}
        #taskProperty {{
            color:{t['muted']};
            font-size:11px;
        }}
        #subtaskToggle {{
            background:transparent;
            border:none;
            color:{t['accent_hover']};
            padding:1px 4px;
            min-height:16px;
            font-size:11px;
        }}
        #rowIcon, #rowIconDanger, #rowIconPrimary, #mediaButton {{
            padding:2px;
            min-height:20px;
            border-radius:8px;
            font-weight:800;
        }}
        #rowIconDanger {{
            background:transparent;
            border:none;
            color:{t['danger']};
            font-size:17px;
        }}
        #rowIconPrimary {{
            background:{t['accent']};
            color:#291F28;
            border:none;
        }}
        #compactControlBar {{
            background:{t['field']};
            border:1px solid {t['border']};
            border-radius:13px;
        }}
        #smallControl, #iconControl {{
            padding:6px 9px;
            min-height:18px;
            border-radius:8px;
        }}
        #smallControl {{
            min-width:42px;
        }}
        #iconControl {{
            min-width:34px;
            max-width:38px;
        }}
        #compactPrimary {{
            background:{t['accent']};
            color:#291F28;
            border:none;
            font-weight:900;
            padding:7px 13px;
            min-width:70px;
            border-radius:9px;
        }}
        #compactQuestCombo {{
            min-height:20px;
            padding:6px 9px;
            border-radius:8px;
        }}
        #taskToolbar {{
            background:{t['panel']};
            border:1px solid {t['border']};
            border-radius:12px;
        }}
        #musicCard {{
            background:{t['panel']};
            border:1px solid {t['border']};
            border-radius:16px;
        }}
        #sectionTitleSmall {{
            font-size:14px;
            font-weight:800;
        }}
        #responsiveHint {{
            color:{t['muted']};
            font-size:11px;
        }}
        QSplitter::handle {{
            background:transparent;
        }}
        QPushButton {{
            background:{t['panel2']}; border:1px solid {t['border']};
            border-radius:12px; padding:9px 13px; min-height:20px;
        }}
        QPushButton:hover {{ border-color:{t['accent']}; }}
        #primary, #bigPrimary {{
            background:{t['accent']}; color:#291F28; border:none; font-weight:900;
        }}
        #primary:hover, #bigPrimary:hover {{ background:{t['accent_hover']}; }}
        #bigPrimary {{ font-size:14px; padding:11px 20px; }}
        #mode:checked, #filter:checked {{
            background:{t['badge']}; color:{t['accent_hover']};
            border:1px solid {t['accent']}; font-weight:800;
        }}
        #focusSmall {{ color:{t['accent_hover']}; font-weight:800; }}
        #dangerGhost {{ background:transparent; border:none; color:{t['danger']}; }}
        #linkButton {{ background:transparent; border:none; color:{t['accent_hover']}; padding:4px; }}
        #mini {{ background:transparent; border:none; font-size:18px; }}
        QLineEdit, QComboBox, QSpinBox, #wheelTime {{
            background:{t['field']}; border:1px solid {t['border']};
            border-radius:11px; padding:9px 11px; min-height:22px;
        }}
        #wheelTime {{ text-align:left; }}
        QProgressBar {{ background:{t['progress']}; border:none; border-radius:4px; }}
        QProgressBar::chunk {{ background:{t['accent']}; border-radius:4px; }}
        QScrollArea, #taskHost {{ background:transparent; border:none; }}
        QListWidget#wheel, QListWidget#subtaskEditor {{
            background:{t['field']}; border:1px solid {t['border']}; border-radius:12px; padding:6px;
        }}
        QListWidget#wheel::item {{
            height:34px; border-radius:9px; font-size:17px; font-weight:700;
        }}
        QListWidget#wheel::item:selected {{
            background:{t['accent']}; color:#291F28;
        }}
        QDialog {{ background:{t['panel2']}; }}
        #successText {{ color:{t['accent_hover']}; font-weight:800; }}
        """)
        self.ring.set_values(self.remaining, self.total_seconds, t["accent"])


    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "main_splitter"):
            self.apply_responsive_layout()

    def apply_responsive_layout(self):
        w = self.width()
        narrow = w < 1050
        tiny = w < 790

        # Main content acts like a responsive web layout.
        self.main_splitter.setOrientation(Qt.Vertical if narrow else Qt.Horizontal)
        if narrow:
            self.main_splitter.setSizes([600, 520])
        else:
            self.main_splitter.setSizes([680, 560])

        # Header progressively removes low-priority text.
        self.brand_sub.setVisible(w >= 840)
        self.theme_combo.setVisible(w >= 720)
        self.new_task_btn.setText("＋" if tiny else "＋ New Quest")
        self.new_task_btn.setToolTip("New Quest")

        # Reflow stats like CSS grid.
        for card in self.stat_cards:
            self.stats_grid.removeWidget(card)
            card.sub.setVisible(w >= 900)

        if w >= 1180:
            for i, card in enumerate(self.stat_cards):
                self.stats_grid.addWidget(card, 0, i)
        elif w >= 720:
            for i, card in enumerate(self.stat_cards):
                self.stats_grid.addWidget(card, i // 2, i % 2)
        else:
            # At very small widths show only the two most actionable stats.
            self.stats_grid.addWidget(self.stat_focus, 0, 0)
            self.stats_grid.addWidget(self.stat_done, 0, 1)
            self.stat_sessions.setVisible(False)
            self.stat_target.setVisible(False)

        if w >= 720:
            self.stat_sessions.setVisible(True)
            self.stat_target.setVisible(True)

        # Timer controls shed secondary actions at phone-ish widths.
        self.minus_btn.setVisible(not tiny)
        self.plus_btn.setVisible(not tiny)
        self.custom_btn.setText("🕒" if tiny else "🕒 Custom")
        self.stop_btn.setVisible(w >= 650)
        self.active_combo.setMinimumWidth(110 if tiny else 180)

        self.music_panel.set_compact(tiny)

    def current_filter(self):
        for k, b in self.filters.items():
            if b.isChecked():
                return k
        return "all"

    def reload_tasks(self):
        tasks = db.list_tasks()
        query = self.search.text().lower().strip() if hasattr(self, "search") else ""
        filt = self.current_filter() if hasattr(self, "filters") else "all"

        while self.task_layout.count() > 1:
            item = self.task_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.active_combo.blockSignals(True)
        current = self.active_task_id
        self.active_combo.clear()
        self.active_combo.addItem("🎯 No quest", None)
        restore = 0

        shown = 0
        for task in tasks:
            if not task["completed"]:
                self.active_combo.addItem(task["title"], task["id"])
                if task["id"] == current:
                    restore = self.active_combo.count() - 1

            match = query in task["title"].lower()
            if filt == "active":
                match = match and not task["completed"]
            elif filt == "completed":
                match = match and bool(task["completed"])
            if not match:
                continue

            card = TaskCard(task, task["id"] == self.active_task_id, compact=self.width() < 930)
            card.selectFocus.connect(self.select_focus)
            card.editTask.connect(self.edit_task)
            card.deleteTask.connect(self.delete_task)
            card.completedChanged.connect(self.complete_task)
            card.subtaskToggle.connect(self.toggle_subtask)
            self.task_layout.insertWidget(self.task_layout.count() - 1, card)
            self.fade_in(card, shown * 45)
            shown += 1

        self.active_combo.setCurrentIndex(restore)
        self.active_combo.blockSignals(False)
        self.count_label.setText(f"{shown} shown • {len(tasks)} total")
        if current and restore == 0:
            self.active_task_id = None

        self.refresh_stats()

    def fade_in(self, widget, delay=0):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        effect.setOpacity(0)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(280)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        widget._fade_anim = anim
        QTimer.singleShot(delay, anim.start)

    def refresh_stats(self):
        tasks = db.list_tasks()
        total = sum(int(t["worked_seconds"]) for t in tasks)
        completed = sum(1 for t in tasks if t["completed"])
        sessions = db.session_count("focus")
        percent = round(completed / len(tasks) * 100) if tasks else 100
        self.stat_focus.value.setText(fmt_duration(total))
        self.stat_done.value.setText(f"{completed} / {len(tasks)}")
        self.stat_done.sub.setText(f"{len(tasks) - completed} quests remaining")
        self.stat_sessions.value.setText(str(sessions))
        self.stat_target.value.setText(f"{percent}%")

    def add_task(self):
        d = TaskDialog(self)
        if d.exec():
            v = d.value()
            db.add_task(**v)
            self.reload_tasks()

    def edit_task(self, task_id):
        task = db.get_task(task_id)
        if not task:
            return
        d = TaskDialog(self, task)
        if d.exec():
            v = d.value()
            db.update_task(task_id, **v)
            self.reload_tasks()

    def delete_task(self, task_id):
        if QMessageBox.question(self, APP_TITLE, "Delete this quest?") == QMessageBox.Yes:
            db.delete_task(task_id)
            if self.active_task_id == task_id:
                self.active_task_id = None
            self.reload_tasks()

    def complete_task(self, task_id, completed):
        db.set_task_completed(task_id, completed)
        if completed and self.active_task_id == task_id:
            self.active_task_id = None
        self.reload_tasks()

    def toggle_subtask(self, sid):
        db.toggle_subtask(sid)
        self.reload_tasks()

    def select_focus(self, task_id):
        self.active_task_id = task_id
        if self.mode != "focus":
            self.set_mode("focus")
        self.reload_tasks()
        for i in range(self.active_combo.count()):
            if self.active_combo.itemData(i) == task_id:
                self.active_combo.blockSignals(True)
                self.active_combo.setCurrentIndex(i)
                self.active_combo.blockSignals(False)
                break

    def active_changed(self):
        self.active_task_id = self.active_combo.currentData()
        self.reload_tasks()

    def set_mode(self, mode):
        self.timer.stop()
        self.glow_timer.stop()
        self.running = False
        self.mode = mode
        presets = {"focus": 25 * 60, "short_break": 5 * 60, "long_break": 15 * 60}
        captions = {"focus": "FOCUS TIME", "short_break": "SHORT BREAK", "long_break": "LONG BREAK"}
        self.total_seconds = presets[mode]
        self.remaining = self.total_seconds
        self.elapsed = 0
        self.started_at = None
        for k, b in self.mode_buttons.items():
            b.setChecked(k == mode)
        self.mode_text.setText(captions[mode])
        self.mascot.set_mode(mode)
        self.mascot.set_running(False)
        self.alert.clear()
        self.start_btn.setText("▶ Start" if mode == "focus" else "▶ Start")
        self.refresh_timer()

    def adjust_time(self, delta_minutes):
        self.remaining = max(60, self.remaining + delta_minutes * 60)
        if not self.running:
            self.total_seconds = self.remaining
        self.refresh_timer()

    def pick_custom_time(self):
        h = self.remaining // 3600
        m = (self.remaining % 3600) // 60
        d = WheelPickerDialog(self, h, m, "Pick Custom Time")
        if d.exec():
            h, m = d.value()
            total = h * 3600 + m * 60
            if total <= 0:
                total = 60
            self.timer.stop()
            self.glow_timer.stop()
            self.running = False
            self.mode = "custom"
            self.total_seconds = total
            self.remaining = total
            self.elapsed = 0
            self.started_at = None
            for b in self.mode_buttons.values():
                b.setChecked(False)
            self.mode_text.setText("CUSTOM FOCUS")
            self.mascot.set_mode("custom")
            self.mascot.set_running(False)
            self.start_btn.setText("▶ Start")
            self.refresh_timer()

    def toggle_timer(self):
        if self.running:
            self.timer.stop()
            self.glow_timer.stop()
            self.running = False
            self.mascot.set_running(False)
            self.start_btn.setText("▶ Resume")
            return
        if self.remaining <= 0:
            self.remaining = self.total_seconds
        if self.started_at is None:
            self.started_at = datetime.now()
        self.running = True
        self.timer.start()
        self.glow_timer.start()
        self.mascot.set_running(True)
        self.start_btn.setText("Ⅱ Pause")
        self.alert.clear()

    def tick(self):
        if not self.running:
            return
        if self.remaining > 0:
            self.remaining -= 1
            self.elapsed += 1
            self.refresh_timer()
        if self.remaining <= 0:
            self.finish_session(True)

    def animate_glow(self):
        self.glow_phase += 0.08
        self.ring.set_glow((math.sin(self.glow_phase) + 1) / 2)

    def finish_session(self, auto=False):
        if not self.running and self.elapsed <= 0:
            return
        self.timer.stop()
        self.glow_timer.stop()
        self.running = False
        self.ring.set_glow(0)
        self.mascot.set_running(False)

        if self.elapsed > 0 and self.started_at:
            db.add_session(
                self.active_task_id,
                self.started_at.isoformat(timespec="seconds"),
                datetime.now().isoformat(timespec="seconds"),
                self.elapsed,
                self.mode,
            )
            if self.active_task_id and self.mode in ("focus", "custom"):
                db.add_worked_seconds(self.active_task_id, self.elapsed)

        self.elapsed = 0
        self.started_at = None
        self.remaining = self.total_seconds
        self.start_btn.setText("▶ Start")
        if auto:
            if not self.muted:
                QApplication.beep()
            self.alert.setText("🏆 Quest round cleared! Nice work ✨")
            self.confetti()
        else:
            self.alert.setText("💖 Progress saved.")
        self.refresh_timer()
        self.reload_tasks()

    def reset_timer(self):
        self.timer.stop()
        self.glow_timer.stop()
        self.running = False
        self.ring.set_glow(0)
        self.mascot.set_running(False)
        self.remaining = self.total_seconds
        self.elapsed = 0
        self.started_at = None
        self.start_btn.setText("▶ Start")
        self.alert.clear()
        self.refresh_timer()

    def refresh_timer(self):
        self.timer_text.setText(fmt_timer(self.remaining))
        self.ring.set_values(self.remaining, self.total_seconds, THEMES[self.theme_key]["accent"])

    def toggle_mute(self):
        self.muted = not self.muted
        db.set_setting("muted", "1" if self.muted else "0")
        self.sync_sound_button()

    def set_ambient_mode(self, mode):
        self.audio_device.set_mode(None if self.muted else mode)

    def set_ambient_volume(self, vol):
        self.audio_device.set_volume(vol)

    def change_theme(self):
        key = self.theme_combo.currentData()
        if key:
            self.theme_key = key
            db.set_setting("theme", key)
            self.apply_theme()
            self.reload_tasks()

    def confetti(self):
        colors = ["✨", "🌸", "⭐", "💖", "🍅"]
        for _ in range(18):
            lbl = QLabel(random.choice(colors), self.centralWidget())
            lbl.setStyleSheet("font-size:18px;background:transparent;")
            x = random.randint(40, max(50, self.width() - 70))
            y = random.randint(80, max(90, self.height() // 2))
            lbl.move(x, y)
            lbl.show()
            effect = QGraphicsOpacityEffect(lbl)
            lbl.setGraphicsEffect(effect)
            anim = QPropertyAnimation(effect, b"opacity", lbl)
            anim.setDuration(900 + random.randint(0, 500))
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.finished.connect(lbl.deleteLater)
            anim.start()
            lbl._anim = anim


    def closeEvent(self, event):
        if hasattr(self, "music_panel"):
            self.music_panel.shutdown()
        super().closeEvent(event)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
