#!/usr/bin/env python3
"""
SPARK Python Lab: an interactive, step-by-step Python and Raspberry Pi workshop.

    python3 spark_lab.py           start (uses the real GPIO pins on a Raspberry Pi)
    python3 spark_lab.py --sim     use the on-screen GPIO simulator instead
    python3 spark_lab.py --reset   forget the saved name and progress first

The lessons live in lessons.py. Edit that file to change them or add more.
"""

import builtins
import difflib
import importlib.util
import io
import json
import keyword
import os
import queue
import random
import re
import signal
import sys
import threading
import time
import traceback
import tkinter as tk
import tkinter.font as tkfont
from textwrap import dedent
from tkinter import filedialog, messagebox, simpledialog, ttk

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lessons import CHAPTERS, LESSONS  # noqa: E402

APP_NAME = "SPARK Python Lab"
USER_FILE = "<your code>"
SAVE_DIR = os.path.join(os.path.expanduser("~"), ".spark_python_lab")
SAVE_FILE = os.path.join(SAVE_DIR, "progress.json")
ICON_FILE = os.path.join(HERE, "assets", "icon.png")
SHORTCUTS = "F5 = Run    Esc = Stop    Ctrl + / Ctrl − = text size    F11 = full screen"

C = {
    "night": "#141933",
    "side": "#1B2140",
    "side_hover": "#262E57",
    "side_fg": "#C3CAEB",
    "side_dim": "#6E78A6",
    "orange": "#FF7A1A",
    "teal": "#14B8A6",
    "green": "#16A34A",
    "red": "#DC3B3B",
    "yellow": "#FFD23F",
    "purple": "#6C5CE7",
    "paper": "#FFFDF8",
    "paper_dim": "#F2EEE4",
    "ink": "#22263A",
    "ink_soft": "#5B6178",
    "ed_bg": "#1E2233",
    "ed_fg": "#E6E9F5",
    "ed_line": "#262B40",
    "ed_sel": "#3B4675",
    "gutter": "#191C2B",
    "gutter_fg": "#596183",
    "toolbar": "#161A2B",
    "tool_btn": "#272C45",
    "con_bg": "#11141F",
    "sash": "#0D1020",
    "disabled": "#2F3448",
    "disabled_fg": "#6B7091",
    "board": "#151D36",
}

SYNTAX = {
    "keyword": "#FF7AB2",
    "builtin": "#6FC3FF",
    "string": "#A5E075",
    "number": "#FFB86B",
    "comment": "#7A83A6",
    "defname": "#FFD23F",
    "const": "#C792EA",
}

_KEYWORDS = [k for k in keyword.kwlist if k not in ("True", "False", "None")]
_BUILTINS = ["print", "input", "int", "float", "str", "bool", "len", "range", "type", "list",
             "dict", "abs", "round", "min", "max", "sum", "sorted", "enumerate", "zip",
             "open", "isinstance", "reversed", "set", "tuple", "help"]
TOKEN_RE = re.compile(
    r"(?P<comment>#[^\n]*)"
    r"|(?P<string>(?<!\w)[rRbBfFuU]{0,2}(?:'''[\s\S]*?(?:'''|$)|\"\"\"[\s\S]*?(?:\"\"\"|$)"
    r"|'(?:\\.|[^'\\\n])*'?|\"(?:\\.|[^\"\\\n])*\"?))"
    r"|(?P<defname>(?<=\bdef )\w+|(?<=\bclass )\w+)"
    r"|(?P<const>\b(?:True|False|None)\b)"
    r"|(?P<keyword>\b(?:" + "|".join(_KEYWORDS) + r")\b)"
    r"|(?P<builtin>\b(?:" + "|".join(_BUILTINS) + r")\b(?=\s*\())"
    r"|(?P<number>\b\d+(?:\.\d+)?\b)"
)
INLINE_RE = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|(?<![\w*])\*[^*\s][^*]*\*(?![\w*]))")

# Physical header pin -> name, for the Raspberry Pi 40-pin header.
HEADER = {
    1: "3V3", 2: "5V", 3: "GPIO2", 4: "5V", 5: "GPIO3", 6: "GND", 7: "GPIO4", 8: "GPIO14",
    9: "GND", 10: "GPIO15", 11: "GPIO17", 12: "GPIO18", 13: "GPIO27", 14: "GND", 15: "GPIO22",
    16: "GPIO23", 17: "3V3", 18: "GPIO24", 19: "GPIO10", 20: "GND", 21: "GPIO9", 22: "GPIO25",
    23: "GPIO11", 24: "GPIO8", 25: "GND", 26: "GPIO7", 27: "ID_SD", 28: "ID_SC", 29: "GPIO5",
    30: "GND", 31: "GPIO6", 32: "GPIO12", 33: "GPIO13", 34: "GND", 35: "GPIO19", 36: "GPIO16",
    37: "GPIO26", 38: "GPIO20", 39: "GND", 40: "GPIO21",
}
BCM_TO_PHYS = {int(n[4:]): p for p, n in HEADER.items() if n.startswith("GPIO")}


def mix(c1, c2, t):
    """Blend two #rrggbb colours; t=0 gives c1, t=1 gives c2."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def apply_syntax(widget, code, start="1.0", prefix=""):
    """Colour Python code that sits in a Text widget starting at `start`."""
    end = f"{start}+{len(code)}c"
    for name in SYNTAX:
        widget.tag_remove(prefix + name, start, end)
    for m in TOKEN_RE.finditer(code):
        if m.end() > m.start():
            widget.tag_add(prefix + m.lastgroup, f"{start}+{m.start()}c", f"{start}+{m.end()}c")


# ---------------------------------------------------------------------------
# Running student code
#
# The student's program runs in a background thread so the window stays alive.
# To make Stop work we (1) trace their code line by line, and (2) swap in
# versions of sleep(), Event.wait() and signal.pause() that wake up when Stop
# is pressed. Everything they print is routed to the Output panel.
# ---------------------------------------------------------------------------

class StopRun(BaseException):
    """Raised inside the student's program when Stop is pressed."""


_real_sleep = time.sleep
_real_event_wait = threading.Event.wait
_real_pause = getattr(signal, "pause", None)
_ABANDONED = set()


class _Active:
    run = None


ACTIVE = _Active()


def _my_run():
    """The Run whose program thread is the current thread, if any."""
    run = ACTIVE.run
    if run is not None and not run.cleaning and run.thread is threading.current_thread():
        return run
    return None


def _lab_sleep(secs):
    run = _my_run()
    if run is None:
        return _real_sleep(secs)
    if secs < 0:
        raise ValueError("sleep length must be non-negative")
    if _real_event_wait(run.stop_flag, secs):
        raise StopRun()


def _lab_event_wait(self, timeout=None):
    run = _my_run()
    if run is None or self is run.stop_flag:
        return _real_event_wait(self, timeout)
    deadline = None if timeout is None else time.monotonic() + timeout
    while True:
        if run.stop_flag.is_set():
            raise StopRun()
        chunk = 0.1
        if deadline is not None:
            chunk = min(chunk, deadline - time.monotonic())
            if chunk <= 0:
                return self.is_set()
        if _real_event_wait(self, chunk):
            return True


def _lab_pause():
    run = _my_run()
    if run is None:
        if _real_pause is not None:
            return _real_pause()
        while True:
            _real_sleep(3600)
    _real_event_wait(run.stop_flag)
    raise StopRun()


class _Router(io.TextIOBase):
    """Stands in for sys.stdout / sys.stderr and sends program output to the Output panel."""

    def __init__(self, real, kind):
        self.real = real
        self.kind = kind

    @property
    def encoding(self):
        return "utf-8"

    def writable(self):
        return True

    def write(self, s):
        s = str(s)
        t = threading.current_thread()
        if t in _ABANDONED:
            return len(s)
        run = ACTIVE.run
        if run is not None and t is not threading.main_thread():
            run.emit(self.kind, s)
            return len(s)
        if self.real is not None:
            try:
                self.real.write(s)
            except Exception:
                pass
        return len(s)

    def flush(self):
        if self.real is not None:
            try:
                self.real.flush()
            except Exception:
                pass


def install_runtime_patches():
    time.sleep = _lab_sleep
    threading.Event.wait = _lab_event_wait
    signal.pause = _lab_pause
    sys.stdout = _Router(sys.stdout, "out")
    sys.stderr = _Router(sys.stderr, "err")


class Run:
    """One press of the Run button: the student's program running in its own thread."""

    _next_id = 0

    def __init__(self, code, outq, lesson_index):
        Run._next_id += 1
        self.id = Run._next_id
        self.code = code
        self.outq = outq
        self.lesson_index = lesson_index
        self.stop_flag = threading.Event()
        self.input_ready = threading.Event()
        self.input_reply = ""
        self.cleaning = False
        self.thread = threading.Thread(target=self._main, name=f"student-program-{self.id}", daemon=True)

    def emit(self, kind, payload=None):
        item = (self.id, kind, payload)
        if kind == "done":
            self.outq.put(item)
            return
        mine = threading.current_thread() is self.thread
        while True:
            try:
                self.outq.put(item, timeout=0.1)
                return
            except queue.Full:
                if self.stop_flag.is_set():
                    if mine and not self.cleaning:
                        raise StopRun()
                    return

    def ask(self, prompt=""):
        """Replacement for input(): asks the window for an answer."""
        prompt = str(prompt)
        if prompt:
            self.emit("out", prompt)
        self.input_ready.clear()
        self.emit("input", prompt)
        while not _real_event_wait(self.input_ready, 0.1):
            if self.stop_flag.is_set():
                raise StopRun()
        return self.input_reply

    def _trace(self, frame, event, arg):
        if frame.f_code.co_filename != USER_FILE:
            return None
        if self.stop_flag.is_set():
            raise StopRun()
        return self._trace_line

    def _trace_line(self, frame, event, arg):
        if event == "line" and self.stop_flag.is_set():
            raise StopRun()
        return self._trace_line

    def _main(self):
        ns = {"__name__": "__main__", "__builtins__": builtins, "input": self.ask}
        status, err = "ok", None
        try:
            compiled = compile(self.code, USER_FILE, "exec")
            sys.settrace(self._trace)
            try:
                exec(compiled, ns)
            finally:
                sys.settrace(None)
        except (StopRun, KeyboardInterrupt):
            status = "stopped"
        except SystemExit:
            pass
        except BaseException as exc:  # noqa: BLE001 - every error is shown to the student
            status, err = "error", explain_error(exc, self.code, ns)
        finally:
            sys.settrace(None)
            self.cleaning = True
            if threading.current_thread() not in _ABANDONED:
                close_gpio_devices()
            self.emit("done", (status, err))


class RunResult:
    """What a lesson's check() function gets to look at."""

    def __init__(self, code, output, status, rises, seen_high, inputs_high):
        self.code = code
        self.output = output
        self.status = status
        self.ok = status in ("ok", "stopped")
        self.rises = rises
        self.blinks = max(rises.values(), default=0)
        self.seen_high = seen_high
        self.inputs_high = inputs_high


# ---------------------------------------------------------------------------
# GPIO helpers (gpiozero is only imported if a program uses it)
# ---------------------------------------------------------------------------

def _pin_number(key, pin):
    if isinstance(key, int):
        return key
    for obj in (key, getattr(pin, "info", None)):
        name = getattr(obj, "name", None)
        if isinstance(name, str) and name.upper().startswith("GPIO"):
            try:
                return int(name[4:])
            except ValueError:
                pass
    number = getattr(pin, "number", None)
    return number if isinstance(number, int) else None


def gpio_snapshot():
    """[(gpio_number, 'in'/'out', device_name, value, device)] for every pin in use."""
    gz = sys.modules.get("gpiozero")
    if gz is None:
        return []
    factory = getattr(gz.Device, "pin_factory", None)
    if factory is None:
        return []
    try:
        reservations = list(factory._reservations.items())
        pins = dict(factory.pins)
    except Exception:
        return []
    result = []
    for key, refs in reservations:
        devices = [d for d in (r() for r in list(refs)) if d is not None]
        if not devices:
            continue
        dev = devices[0]
        pin = pins.get(key)
        bcm = _pin_number(key, pin)
        if bcm is None:
            continue
        try:
            if isinstance(dev, gz.InputDevice):
                kind, value = "in", float(bool(dev.is_active))
            else:
                kind, value = "out", float(dev.value or 0)
        except Exception:
            try:
                kind = "out" if pin.function == "output" else "in"
                value = float(pin.state or 0)
            except Exception:
                continue
        result.append((bcm, kind, type(dev).__name__, max(0.0, min(1.0, value)), dev))
    result.sort(key=lambda item: item[0])
    return result


def close_gpio_devices():
    """Close every gpiozero device, like Python does when a real script ends."""
    gz = sys.modules.get("gpiozero")
    if gz is None:
        return
    factory = getattr(gz.Device, "pin_factory", None)
    if factory is None:
        return
    try:
        groups = list(factory._reservations.values())
    except Exception:
        groups = []
    seen, devices = set(), []
    for refs in groups:
        for ref in list(refs):
            dev = ref()
            if dev is not None and id(dev) not in seen:
                seen.add(id(dev))
                devices.append(dev)
    for dev in devices:
        try:
            dev.close()
        except Exception:
            pass


def detect_mode(argv):
    if "--sim" in argv:
        return "sim"
    if "--real" in argv:
        return "real"
    try:
        with open("/proc/device-tree/model") as f:
            model = f.read()
    except OSError:
        model = ""
    return "real" if "Raspberry Pi" in model else "sim"


# ---------------------------------------------------------------------------
# Friendly error messages
# ---------------------------------------------------------------------------

def explain_error(exc, code, ns):
    lines = code.splitlines()
    name, msg = type(exc).__name__, str(exc)
    lineno = None
    if isinstance(exc, SyntaxError):
        lineno, msg = exc.lineno, exc.msg or msg
    else:
        for frame in traceback.extract_tb(exc.__traceback__):
            if frame.filename == USER_FILE:
                lineno = frame.lineno
    title, detail = _friendly(exc, name, msg, ns)
    source = lines[lineno - 1].strip() if lineno and 0 < lineno <= len(lines) else ""
    return {"type": name, "message": msg, "title": title, "detail": detail,
            "line": lineno, "source": source}


def _friendly(exc, name, msg, ns):
    low = msg.lower()

    # gpiozero errors (checked by name so gpiozero doesn't have to be installed)
    if name == "GPIOPinInUse":
        return ("That pin is already in use",
                "Two parts are trying to use the same GPIO pin. Did you create LED(17) twice? "
                "Create each part only once, near the top of your program.")
    if name in ("BadPinFactory", "PinFactoryFallback") or "pin factory" in low:
        return ("Can't reach the GPIO pins",
                "This computer can't control GPIO pins. On a laptop, start the app with --sim "
                "to use the on-screen simulator.")
    if name == "OutputDeviceBadValue":
        return ("Bad brightness value", "An LED's value must be between 0 (off) and 1 (full brightness).")
    if name.startswith("Pin") or name.startswith("GPIO"):
        return ("GPIO pin problem", f"{msg}. Check the pin number you used, e.g. LED(17).")

    if isinstance(exc, IndentationError):
        if "expected an indented block" in low:
            return ("Indentation needed",
                    "After a line ending with a colon : the next lines must be pushed in "
                    "(indented) with the Tab key or 4 spaces.")
        if "unexpected indent" in low:
            return ("Unexpected indent",
                    "This line is pushed in, but it shouldn't be. Move it back to line up with "
                    "the lines around it.")
        return ("Indentation problem",
                "The spaces at the start of the lines don't line up. Lines in the same block "
                "must start in exactly the same place.")
    if isinstance(exc, SyntaxError):
        if "unterminated" in low or "eol while" in low or "eof while scanning" in low:
            return ("A quote mark is missing",
                    'Text must start AND end with a quote mark, like "hello". One of them is missing.')
        if "expected ':'" in low:
            return ("Missing colon :",
                    "Lines that start with if, elif, else, for, while or def must end with a colon :")
        if "missing parentheses" in low:
            return ("Missing brackets", 'print needs brackets around what it prints: print("hello")')
        if "was never closed" in low:
            return ("Bracket not closed", "You opened a bracket ( [ or { but never closed it. Count your brackets!")
        if "unmatched" in low or "does not match" in low:
            return ("Extra or wrong bracket", "There's a closing bracket without a matching opening bracket.")
        if "invalid character" in low:
            return ("Strange character",
                    'There\'s a character Python doesn\'t understand. Curly quotes like “ ” must be '
                    'plain quotes " instead.')
        if "maybe you meant '=='" in low or "cannot assign" in low:
            return ("= or == ?", "Use = to put a value in a variable. Use == to compare two things, like in an if.")
        if "forgot a comma" in low:
            return ("Missing comma?", 'When you give print() several things, separate them with commas: print("Age", age)')
        if "unexpected eof" in low or "incomplete input" in low:
            return ("Code ends too early", "Something is unfinished. Maybe a missing bracket, or an empty if/for/def?")
        return ("Python can't understand this line",
                "Check the spelling, brackets ( ), quote marks \" \" and colons : on this line, "
                "and on the line just above it.")
    if isinstance(exc, NameError):
        m = re.search(r"name '(\w+)' is not defined", msg)
        bad = m.group(1) if m else "?"
        names = [n for n in list(ns) + dir(builtins) if not n.startswith("_")]
        guess = difflib.get_close_matches(bad, names, n=1, cutoff=0.7)
        extra = f" Did you mean '{guess[0]}'?" if guess else ""
        return (f"Python doesn't know '{bad}'",
                f"Nothing called '{bad}' exists yet.{extra} Check the spelling (capitals matter!), "
                "make sure you created it before using it, and put text inside \"quotes\".")
    if isinstance(exc, ZeroDivisionError):
        return ("Divide by zero!", "You can't divide by 0. Not even a computer can do that!")
    if isinstance(exc, TypeError):
        if "concatenate" in low or ("unsupported operand" in low and "str" in low):
            return ("Mixing text and numbers",
                    "You can't join text and numbers with +. Use str(number) to turn the number "
                    'into text, or use commas: print("Age:", 12)')
        if "required positional argument" in low:
            return ("A function needs more values", f"Something is missing inside the brackets. Python says: {msg}")
        if "positional argument" in low and "given" in low:
            return ("Too many values for a function", f"You gave a function more values than it expects. Python says: {msg}")
        if "not callable" in low:
            return ("That's not a function",
                    "You put brackets ( ) after something that isn't a function. Did you forget a * "
                    "between a number and a bracket?")
        return ("Wrong type of value", msg)
    if isinstance(exc, ValueError):
        if "invalid literal for int" in low:
            return ("That's not a whole number",
                    'int() can only turn number-text like "42" into a number. Did you type letters, '
                    "or a decimal? (Use float() for decimals.)")
        if "could not convert string to float" in low:
            return ("That's not a number", "float() can only turn number-text like \"2.5\" into a number.")
        return ("Bad value", msg)
    if isinstance(exc, IndexError):
        return ("No item at that position",
                "That position doesn't exist in the list. Remember: counting starts at 0, so the "
                "last item of a 3-item list is [2].")
    if isinstance(exc, KeyError):
        return ("Key not found", f"The dictionary has no key {msg}.")
    if isinstance(exc, AttributeError):
        m = re.search(r"has no attribute '(\w+)'", msg)
        attr = m.group(1) if m else "that"
        return ("Unknown command after the dot",
                f"'{attr}' isn't something this can do. Check the spelling and capitals, e.g. led.on() not led.On()")
    if isinstance(exc, ImportError):
        if "cannot import name" in low:
            return ("Can't find that in the module", f"{msg}. Check the spelling and capitals, e.g. from gpiozero import LED")
        if "gpiozero" in low:
            return ("gpiozero isn't installed",
                    "This lesson needs the gpiozero library. It's built into Raspberry Pi OS. "
                    "Elsewhere run:  pip3 install gpiozero")
        return ("Module not found", f"{msg}. Check the spelling of the module name.")
    if isinstance(exc, RecursionError):
        return ("A function called itself forever", "A function kept calling itself and never stopped.")
    return (name, msg)


# ---------------------------------------------------------------------------
# Saved progress
# ---------------------------------------------------------------------------

def fresh_progress():
    return {"name": "", "completed": [], "code": {}, "current": 0, "zoom": 0}


def load_progress():
    data = fresh_progress()
    try:
        with open(SAVE_FILE) as f:
            data.update(json.load(f))
    except (OSError, ValueError):
        pass
    return data


def save_progress(data):
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        tmp = SAVE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=1)
        os.replace(tmp, SAVE_FILE)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class FlatButton(tk.Label):
    """A flat, coloured button that looks the same on every system."""

    def __init__(self, master, text, command, bg, fg="#FFFFFF", font=None, padx=14, pady=6, hover=None):
        super().__init__(master, text=text, bg=bg, fg=fg, font=font, padx=padx, pady=pady,
                         cursor="hand2", bd=0)
        self._bg, self._fg = bg, fg
        self._hover = hover or mix(bg, "#FFFFFF", 0.14)
        self._command = command
        self.enabled = True
        self.bind("<Enter>", lambda e: self.enabled and self.configure(bg=self._hover))
        self.bind("<Leave>", lambda e: self.enabled and self.configure(bg=self._bg))
        self.bind("<ButtonRelease-1>", self._click)

    def _click(self, event):
        if self.enabled and 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            self._command()

    def set_enabled(self, on):
        self.enabled = on
        self.configure(bg=self._bg if on else C["disabled"], fg=self._fg if on else C["disabled_fg"],
                       cursor="hand2" if on else "arrow")


class CodeEditor(tk.Frame):
    """The code box: line numbers, colours, auto-indent and friendly Tab/Backspace."""

    def __init__(self, master, app):
        super().__init__(master, bg=C["ed_bg"])
        self.app = app
        self.error_line = None
        self._hl_job = None
        t = self.text = tk.Text(
            self, wrap="none", undo=True, maxundo=-1, autoseparators=True,
            bg=C["ed_bg"], fg=C["ed_fg"], insertbackground=C["yellow"], insertwidth=2,
            selectbackground=C["ed_sel"], selectforeground=C["ed_fg"], inactiveselectbackground=C["ed_sel"],
            font=app.fonts["editor"], bd=0, highlightthickness=0, padx=10, pady=8, spacing1=2, spacing3=2)
        self.gutter = tk.Canvas(self, width=48, bg=C["gutter"], highlightthickness=0, bd=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=t.yview, style="Dark.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(self, orient="horizontal", command=t.xview, style="Dark.Horizontal.TScrollbar")

        def on_yscroll(first, last):
            vsb.set(first, last)
            self.redraw_gutter()

        t.configure(yscrollcommand=on_yscroll, xscrollcommand=hsb.set)
        self.gutter.grid(row=0, column=0, sticky="ns")
        t.grid(row=0, column=1, sticky="nsew")
        vsb.grid(row=0, column=2, sticky="ns")
        hsb.grid(row=1, column=1, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        for name, color in SYNTAX.items():
            t.tag_configure(name, foreground=color)
        t.tag_configure("comment", font=app.fonts["editor_i"])
        t.tag_configure("curline", background=C["ed_line"])
        t.tag_configure("errline", background="#5A1F2E")
        t.tag_lower("errline")
        t.tag_lower("curline")
        t.tag_raise("sel")
        self.after_zoom()

        t.bind("<Tab>", self._on_tab)
        t.bind("<Shift-Tab>", self._on_untab)
        t.bind("<ISO_Left_Tab>", self._on_untab)
        t.bind("<Return>", self._on_return)
        t.bind("<KP_Enter>", self._on_return)
        t.bind("<BackSpace>", self._on_backspace)
        t.bind("<<Modified>>", self._on_modified)
        for seq in ("<KeyRelease>", "<ButtonRelease-1>", "<FocusIn>"):
            t.bind(seq, lambda e: self._update_curline(), add="+")
        t.bind("<Configure>", lambda e: self.redraw_gutter(), add="+")

    # -- public -----------------------------------------------------------
    def get_code(self):
        return self.text.get("1.0", "end-1c")

    def set_code(self, code):
        """Load new code (e.g. a different lesson), with a fresh undo history."""
        t = self.text
        t.delete("1.0", "end")
        t.insert("1.0", code)
        t.edit_reset()
        t.edit_modified(False)
        t.mark_set("insert", "1.0")
        t.see("1.0")
        self.clear_error()
        self.highlight()
        self._update_curline()

    def replace_code(self, code):
        """Swap the code in a way that Ctrl+Z can undo."""
        t = self.text
        t.edit_separator()
        t.delete("1.0", "end")
        t.insert("1.0", code)
        t.edit_separator()
        t.mark_set("insert", "1.0")
        t.see("1.0")
        self._changed()

    def mark_error(self, line):
        self.clear_error()
        self.error_line = line
        self.text.tag_add("errline", f"{line}.0", f"{line}.0 lineend+1c")
        self.text.see(f"{line}.0")
        self.redraw_gutter()

    def clear_error(self):
        self.error_line = None
        self.text.tag_remove("errline", "1.0", "end")
        self.redraw_gutter()

    def after_zoom(self):
        self.text.configure(tabs=(self.app.fonts["editor"].measure("    "),))
        self.redraw_gutter()

    def highlight(self):
        self._hl_job = None
        apply_syntax(self.text, self.get_code())

    # -- editing helpers --------------------------------------------------
    def _selected_lines(self):
        t = self.text
        if not t.tag_ranges("sel"):
            line = int(t.index("insert").split(".")[0])
            return line, line
        first = int(t.index("sel.first").split(".")[0])
        last_index = t.index("sel.last")
        last = int(last_index.split(".")[0])
        if last_index.endswith(".0") and last > first:
            last -= 1
        return first, last

    def _on_tab(self, event):
        t = self.text
        if t.tag_ranges("sel"):
            first, last = self._selected_lines()
            for line in range(first, last + 1):
                t.insert(f"{line}.0", "    ")
        else:
            t.insert("insert", "    ")
        self._changed()
        return "break"

    def _on_untab(self, event):
        t = self.text
        first, last = self._selected_lines()
        for line in range(first, last + 1):
            lead = t.get(f"{line}.0", f"{line}.4")
            n = len(lead) - len(lead.lstrip(" "))
            if n:
                t.delete(f"{line}.0", f"{line}.{n}")
        self._changed()
        return "break"

    def _on_return(self, event):
        t = self.text
        if t.tag_ranges("sel"):
            t.delete("sel.first", "sel.last")
        line = t.get("insert linestart", "insert")
        indent = re.match(r"[ \t]*", line).group(0)
        if line.rstrip().endswith(":"):
            indent += "    "
        elif re.match(r"\s*(return|break|continue|pass)\b", line):
            indent = indent[:-4]
        t.insert("insert", "\n" + indent)
        t.see("insert")
        self._changed()
        return "break"

    def _on_backspace(self, event):
        t = self.text
        if t.tag_ranges("sel"):
            return None
        before = t.get("insert linestart", "insert")
        if before and not before.strip(" "):
            n = len(before) % 4 or 4
            t.delete(f"insert-{n}c", "insert")
            self._changed()
            return "break"
        return None

    def _on_modified(self, event=None):
        if not self.text.edit_modified():
            return
        self.text.edit_modified(False)
        self._changed()

    def _changed(self):
        if self.error_line:
            self.clear_error()
        if self._hl_job:
            self.after_cancel(self._hl_job)
        self._hl_job = self.after(80, self.highlight)
        self._update_curline()

    def _update_curline(self):
        t = self.text
        t.tag_remove("curline", "1.0", "end")
        t.tag_add("curline", "insert linestart", "insert lineend+1c")
        self.redraw_gutter()

    def redraw_gutter(self):
        g, t = self.gutter, self.text
        font = self.app.fonts["gutter"]
        width = font.measure("000") + 24
        if int(g.cget("width")) != width:
            g.configure(width=width)
        g.delete("all")
        current = t.index("insert").split(".")[0]
        index = t.index("@0,0")
        while True:
            info = t.dlineinfo(index)
            if info is None:
                break
            line = index.split(".")[0]
            y = info[1] + info[3] / 2
            color = C["ed_fg"] if line == current else C["gutter_fg"]
            if self.error_line and int(line) == self.error_line:
                g.create_oval(5, y - 4, 13, y + 4, fill="#FF5C5C", outline="")
                color = "#FF8A8A"
            g.create_text(width - 10, y, anchor="e", text=line, fill=color, font=font)
            nxt = t.index(f"{index}+1line")
            if nxt == index:
                break
            index = nxt


class Console(tk.Frame):
    """The Output panel, with an answer box for input()."""

    def __init__(self, master, app):
        super().__init__(master, bg=C["con_bg"])
        self.app = app
        self.waiting = False
        f = app.fonts

        head = tk.Frame(self, bg=C["toolbar"])
        head.pack(side="top", fill="x")
        tk.Label(head, text="OUTPUT", font=f["small_b"], fg=C["side_dim"], bg=C["toolbar"],
                 padx=14, pady=7).pack(side="left")
        self.state_lbl = tk.Label(head, text="", font=f["small_b"], fg=C["teal"], bg=C["toolbar"])
        self.state_lbl.pack(side="left")
        FlatButton(head, "Clear", self.clear, bg=C["toolbar"], fg=C["side_dim"], font=f["small"],
                   padx=12, pady=3, hover=C["tool_btn"]).pack(side="right", padx=6)

        self.in_bar = tk.Frame(self, bg=C["toolbar"])
        self.in_bar.pack(side="bottom", fill="x")
        self.in_label = tk.Label(self.in_bar, font=f["small_b"], bg=C["toolbar"], padx=12)
        self.in_label.pack(side="left")
        self.entry = tk.Entry(self.in_bar, width=1, font=f["console"], bg="#1A1F33", fg=C["ed_fg"],
                              insertbackground=C["yellow"], relief="flat", bd=4,
                              highlightthickness=2, highlightbackground=C["toolbar"],
                              highlightcolor=C["yellow"], disabledbackground="#151927")
        self.entry.pack(side="left", fill="x", expand=True, pady=6)
        self.send_btn = FlatButton(self.in_bar, "Send", self._send, bg=C["purple"], font=f["small_b"],
                                   padx=14, pady=5)
        self.send_btn.pack(side="left", padx=8)
        self.entry.bind("<Return>", self._send)
        self.entry.bind("<KP_Enter>", self._send)

        body = tk.Frame(self, bg=C["con_bg"])
        body.pack(side="top", fill="both", expand=True)
        t = self.text = tk.Text(body, wrap="word", bg=C["con_bg"], fg=C["ed_fg"], font=f["console"],
                                bd=0, highlightthickness=0, padx=14, pady=10, state="disabled",
                                cursor="arrow", spacing1=1, spacing3=1, insertwidth=0)
        sb = ttk.Scrollbar(body, orient="vertical", command=t.yview, style="Dark.Vertical.TScrollbar")
        t.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        t.pack(side="left", fill="both", expand=True)

        t.tag_configure("out", foreground=C["ed_fg"])
        t.tag_configure("stderr", foreground="#FFB86B")
        t.tag_configure("info", foreground="#7A83A6")
        t.tag_configure("info_b", foreground="#AEB6DA", font=f["console_b"])
        t.tag_configure("success", foreground="#4ADE80", font=f["console_b"])
        t.tag_configure("warn", foreground=C["yellow"])
        t.tag_configure("input", foreground="#6FC3FF", font=f["console_b"])
        t.tag_configure("err_title", foreground="#FF6B6B", font=f["console_b"])
        t.tag_configure("err_code", foreground="#FFD7D7", background="#2A1620")
        t.tag_configure("err_detail", foreground="#FFC9C9")
        t.tag_configure("hint", foreground="#FFE7A3", background="#272412", lmargin1=12, lmargin2=12)
        t.tag_configure("hint_title", foreground=C["yellow"], font=f["console_b"])
        self.cancel_input()

    def write(self, s, tag="out"):
        if not s:
            return
        t = self.text
        at_end = t.yview()[1] > 0.999
        t.configure(state="normal")
        t.insert("end", s, tag)
        lines = int(t.index("end-1c").split(".")[0])
        if lines > 3000:
            t.delete("1.0", f"{lines - 2500}.0")
        t.configure(state="disabled")
        if at_end or tag != "out":
            t.see("end")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def ask_input(self):
        self.waiting = True
        self.entry.configure(state="normal")
        self.entry.delete(0, "end")
        self.entry.focus_set()
        self.in_label.configure(text="Your answer ›", fg=C["yellow"])
        self.in_bar.configure(bg="#2A2614")
        self.in_label.configure(bg="#2A2614")
        self.send_btn.set_enabled(True)

    def cancel_input(self):
        self.waiting = False
        self.entry.delete(0, "end")
        self.entry.configure(state="disabled")
        self.in_label.configure(text="Answer box (lights up when your program asks a question)",
                                fg=C["side_dim"], bg=C["toolbar"])
        self.in_bar.configure(bg=C["toolbar"])
        self.send_btn.set_enabled(False)

    def _send(self, event=None):
        if not self.waiting:
            return "break"
        answer = self.entry.get()
        self.write(answer + "\n", "input")
        self.cancel_input()
        self.app.answer_input(answer)
        self.app.editor.text.focus_set()
        return "break"


class BoardPanel(tk.Frame):
    """The GPIO view under hardware lessons: header map, live parts and wiring guide."""

    def __init__(self, master, app):
        super().__init__(master, bg=C["board"])
        self.app = app
        self.wiring = []
        self.devices = {}
        self._sig = None
        self._wave_job = None
        self.collapsed = False
        f = app.fonts
        head = tk.Frame(self, bg=C["board"])
        head.pack(fill="x", padx=14, pady=(8, 0))
        sim = app.mode == "sim"
        tk.Label(head, text="VIRTUAL PI BOARD" if sim else "LIVE GPIO VIEW", font=f["small_b"],
                 fg=C["yellow"], bg=C["board"]).pack(side="left")
        tk.Label(head, text="simulator: no wires needed" if sim else "your real Raspberry Pi pins",
                 font=f["small"], fg=C["side_dim"], bg=C["board"]).pack(side="left", padx=8)
        self.toggle_btn = FlatButton(head, "Hide", self.toggle, bg=C["board"], fg=C["side_dim"],
                                     font=f["small"], padx=8, pady=2, hover=C["side_hover"])
        self.toggle_btn.pack(side="right")
        self.wave_btn = None
        if sim:
            self.wave_btn = FlatButton(head, "Wave at sensor", self.wave, bg=C["purple"],
                                       font=f["small_b"], padx=10, pady=3)
            self.wave_btn.pack(side="right", padx=6)
        self.canvas = tk.Canvas(self, bg=C["board"], highlightthickness=0, bd=0, height=200)
        self.canvas.pack(fill="x", padx=6, pady=(2, 6))
        self.canvas.bind("<Configure>", lambda e: self.redraw())

    def toggle(self):
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.canvas.pack_forget()
        else:
            self.canvas.pack(fill="x", padx=6, pady=(2, 6))
        self.toggle_btn.configure(text="Show" if self.collapsed else "Hide")

    def set_lesson(self, lesson):
        self.wiring = lesson.get("wiring") or []
        self.devices = {}
        self._sig = None
        self.redraw()

    def reset_for_run(self):
        self.devices = {}
        self._sig = None
        self.redraw()

    def update_pins(self, snapshot):
        live = set()
        for bcm, kind, name, value, _dev in snapshot:
            live.add(bcm)
            self.devices[bcm] = {"kind": kind, "name": name, "value": value, "live": True}
        for bcm, d in self.devices.items():
            if bcm not in live and d["live"]:
                d["live"], d["value"] = False, 0.0
        sig = tuple((b, d["kind"], d["name"], round(d["value"], 2), d["live"])
                    for b, d in sorted(self.devices.items()))
        if sig != self._sig:
            self._sig = sig
            self.redraw()

    def wave(self):
        if not self.app.sim_drive_inputs(True):
            self.app.status_msg("No sensor yet. Run code that creates a MotionSensor first, then wave!")
            return
        self.wave_btn.configure(text="Waving...")
        if self._wave_job:
            self.after_cancel(self._wave_job)
        self._wave_job = self.after(2500, self._wave_end)

    def _wave_end(self):
        self._wave_job = None
        self.app.sim_drive_inputs(False)
        self.wave_btn.configure(text="Wave at sensor")

    @staticmethod
    def _pin_color(name):
        if name == "5V":
            return "#E5484D"
        if name == "3V3":
            return "#F59E0B"
        if name == "GND":
            return "#3B4252"
        if name.startswith("ID_"):
            return "#5B6178"
        return "#2FA36B"

    def redraw(self):
        c = self.canvas
        c.delete("all")
        f = self.app.fonts
        W = max(c.winfo_width(), 320)
        pitch = max(12.0, min(24.0, (W - 40) / 20))
        r = pitch * 0.3
        x0 = (W - pitch * 20) / 2
        y0 = 22
        wired = {pin: color for pin, _text, color in self.wiring}
        live_phys = {BCM_TO_PHYS[b]: d for b, d in self.devices.items() if b in BCM_TO_PHYS and d["live"]}

        round_rect(c, x0 - 8, y0 - 6, x0 + pitch * 20 + 8, y0 + pitch * 2 + 6, 6,
                   fill="#0A0E1A", outline="#2A3358")
        for phys in range(1, 41):
            col, top = (phys - 1) // 2, phys % 2 == 0
            cx = x0 + pitch * col + pitch / 2
            cy = y0 + (pitch * 0.5 if top else pitch * 1.5)
            fill = self._pin_color(HEADER[phys])
            dev = live_phys.get(phys)
            if dev and dev["value"] > 0.5:
                fill = C["yellow"]
                c.create_oval(cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5, fill=mix(C["board"], C["yellow"], 0.35), outline="")
            if phys in wired:
                c.create_oval(cx - r - 3.5, cy - r - 3.5, cx + r + 3.5, cy + r + 3.5, outline=wired[phys], width=2.5)
            shape = c.create_rectangle if phys == 1 else c.create_oval
            shape(cx - r, cy - r, cx + r, cy + r, fill=fill, outline="")
            if phys in wired or dev:
                color = wired.get(phys, C["yellow"])
                if top:
                    c.create_text(cx, cy - r - 5, text=str(phys), anchor="s", fill=color, font=f["tiny"])
                else:
                    c.create_text(cx, cy + r + 5, text=str(phys), anchor="n", fill=color, font=f["tiny"])
        y = y0 + pitch * 2 + 22
        c.create_text(x0 - 6, y - 4, text="◀ pin 1 end", anchor="w", fill=C["side_dim"], font=f["tiny"])
        c.create_text(x0 + pitch * 20 + 6, y - 4, text="USB-port end ▶", anchor="e", fill=C["side_dim"], font=f["tiny"])
        legend = [("#E5484D", "5V"), ("#F59E0B", "3V3"), ("#3B4252", "GND"), ("#2FA36B", "GPIO")]
        lx = W / 2 - 110
        for color, label in legend:
            c.create_oval(lx, y - 9, lx + 9, y, fill=color, outline="#59627F")
            c.create_text(lx + 13, y - 4, text=label, anchor="w", fill=C["side_dim"], font=f["tiny"])
            lx += 56
        y += 14

        # parts in use
        if self.devices:
            per_row = max(1, int((W - 20) // 150))
            items = sorted(self.devices.items())
            for i, (bcm, d) in enumerate(items):
                row, col = divmod(i, per_row)
                cx = 20 + 150 * col + 40
                cy = y + 28 + row * 72
                self._draw_device(c, cx, cy, bcm, d)
            y += 74 + (len(items) - 1) // per_row * 72
        else:
            c.create_text(W / 2, y + 22, fill=C["side_dim"], font=f["small"],
                          text="Run your code. The LEDs and sensors you use will appear here.")
            y += 48

        # wiring guide
        if self.wiring:
            c.create_text(16, y, text="WIRING", anchor="w", fill=C["yellow"], font=f["tiny"])
            y += 16
            for pin, text, color in self.wiring:
                c.create_oval(18, y - 5, 28, y + 5, fill=color, outline="")
                c.create_text(36, y, text=text, anchor="w", fill="#DDE2F5", font=f["small"])
                y += 19
        c.configure(height=int(y + 4))

    def _draw_device(self, c, cx, cy, bcm, d):
        f = self.app.fonts
        v = d["value"] if d["live"] else 0.0
        if d["kind"] == "out":
            body = mix("#4A1820", "#FF3B30", v)
            if v > 0.02:
                g = 18 + 10 * v
                c.create_oval(cx - g, cy - g - 2, cx + g, cy + g - 2, fill=mix(C["board"], "#FF3B30", 0.4 * v), outline="")
            c.create_line(cx - 6, cy + 12, cx - 6, cy + 32, fill="#9CA3AF", width=2)
            c.create_line(cx + 6, cy + 12, cx + 6, cy + 27, fill="#9CA3AF", width=2)
            c.create_oval(cx - 13, cy - 17, cx + 13, cy + 9, fill=body, outline=mix(body, "#FFFFFF", 0.25))
            c.create_rectangle(cx - 13, cy - 4, cx + 13, cy + 9, fill=body, outline="")
            c.create_rectangle(cx - 15, cy + 8, cx + 15, cy + 13, fill=mix(body, "#000000", 0.2), outline="")
            if v > 0.3:
                c.create_oval(cx - 7, cy - 12, cx - 2, cy - 5, fill=mix(body, "#FFFFFF", 0.7), outline="")
            state = ("ON" if v > 0.99 else f"{round(v * 100)}%") if v > 0.01 else "OFF"
            state_color = "#FF8A80" if v > 0.01 else C["side_dim"]
        else:
            on = v > 0.5
            if on:
                for k, rad in enumerate((30, 40)):
                    c.create_arc(cx - rad, cy - rad, cx + rad, cy + rad, start=40, extent=100, style="arc",
                                 outline=mix(C["board"], C["yellow"], 0.9 - 0.3 * k), width=2)
            c.create_rectangle(cx - 20, cy + 4, cx + 20, cy + 22, fill="#1F7A4A", outline="")
            dome = C["yellow"] if on else "#E8EAF0"
            c.create_arc(cx - 16, cy - 14, cx + 16, cy + 18, start=0, extent=180, style="pieslice",
                         fill=dome, outline="#9CA3AF")
            for dx in (-8, 0, 8):
                c.create_line(cx + dx, cy - 10 + abs(dx) * 0.4, cx + dx, cy + 2, fill=mix(dome, "#000000", 0.2))
            state = "MOTION!" if on else "still"
            state_color = C["yellow"] if on else C["side_dim"]
        c.create_text(cx + 34, cy - 8, anchor="w", text=d["name"], fill="#FFFFFF", font=f["small_b"])
        c.create_text(cx + 34, cy + 8, anchor="w", text=f"GPIO{bcm}", fill=C["side_dim"], font=f["tiny"])
        c.create_text(cx + 34, cy + 24, anchor="w", text=state if d["live"] else "(program ended)",
                      fill=state_color if d["live"] else C["side_dim"], font=f["small_b"])


# ---------------------------------------------------------------------------
# The app
# ---------------------------------------------------------------------------

ZOOMABLE = ("title", "h2", "body", "body_b", "body_i", "code", "code_i", "editor", "editor_i",
            "gutter", "console", "console_b")


class SparkLab:
    def __init__(self, root, mode):
        self.root = root
        self.mode = mode
        self.gpio_ok = importlib.util.find_spec("gpiozero") is not None
        self.progress = load_progress()
        self.outq = queue.Queue(maxsize=3000)
        self.run = None
        self.lesson_index = None
        self.main_built = False
        self.board_visible = False
        self.overlay = None
        self.run_output = []
        self.run_rises, self.run_seen_high, self.run_inputs_high, self._pin_prev = {}, set(), set(), {}
        self._status_job = None

        self._setup_fonts()
        self._setup_styles()
        root.title(APP_NAME)
        root.configure(bg=C["side"])
        try:
            self._icon = tk.PhotoImage(file=ICON_FILE)
            root.iconphoto(True, self._icon)
        except tk.TclError:
            pass
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_welcome()
        root.after(30, self.poll)

    # -- look & feel -------------------------------------------------------
    def _setup_fonts(self):
        families = set(tkfont.families(self.root))

        def pick(options, fallback):
            return next((name for name in options if name in families), fallback)

        ui = pick(["Noto Sans", "DejaVu Sans", "Ubuntu", "Segoe UI", "Helvetica Neue", "Arial"], "Helvetica")
        mono = pick(["DejaVu Sans Mono", "Noto Sans Mono", "Ubuntu Mono", "Consolas", "Menlo", "Courier New"], "Courier")
        spec = {
            "tiny": (ui, 8), "small": (ui, 9), "small_b": (ui, 9, "bold"),
            "ui": (ui, 11), "ui_b": (ui, 11, "bold"), "lead": (ui, 13), "entry": (ui, 16),
            "button_big": (ui, 14, "bold"), "logo": (ui, 17, "bold"), "big": (ui, 30, "bold"),
            "huge": (ui, 60, "bold"),
            "title": (ui, 21, "bold"), "h2": (ui, 15, "bold"), "body": (ui, 13), "body_b": (ui, 13, "bold"), "body_i": (ui, 13, "normal", "italic"),
            "code": (mono, 12), "code_i": (mono, 12, "normal", "italic"),
            "editor": (mono, 14), "editor_i": (mono, 14, "normal", "italic"), "gutter": (mono, 11),
            "console": (mono, 12), "console_b": (mono, 12, "bold"), "pad": (ui, 5),
        }
        self.fonts, self.base_sizes = {}, {}
        for name, s in spec.items():
            weight = s[2] if len(s) > 2 else "normal"
            slant = s[3] if len(s) > 3 else "roman"
            self.fonts[name] = tkfont.Font(self.root, family=s[0], size=s[1], weight=weight, slant=slant)
            self.base_sizes[name] = s[1]
        self.apply_zoom()

    def apply_zoom(self):
        z = self.progress.get("zoom", 0)
        for name in ZOOMABLE:
            self.fonts[name].configure(size=max(7, self.base_sizes[name] + z))
        if self.main_built:
            self.editor.after_zoom()

    def _setup_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        for name, trough, thumb in (("Dark", C["ed_bg"], "#3A4163"), ("Light", C["paper"], "#D6D1C2"),
                                    ("Side", C["side"], "#323B6B")):
            for orient in ("Vertical", "Horizontal"):
                style.configure(f"{name}.{orient}.TScrollbar", background=thumb, troughcolor=trough,
                                bordercolor=trough, lightcolor=thumb, darkcolor=thumb,
                                arrowcolor=mix(thumb, "#FFFFFF", 0.5), relief="flat", gripcount=0, arrowsize=12)
                style.map(f"{name}.{orient}.TScrollbar", background=[("active", mix(thumb, "#FFFFFF", 0.2))])

    def mode_badge(self):
        if not self.gpio_ok:
            return "● GPIO not installed", "#9CA3AF"
        if self.mode == "real":
            return "● Raspberry Pi GPIO", "#4ADE80"
        return "● GPIO Simulator", C["yellow"]

    # -- welcome screen ----------------------------------------------------
    def show_welcome(self):
        f = self.fonts
        w = self.welcome = tk.Frame(self.root, bg=C["side"])
        w.place(x=0, y=0, relwidth=1, relheight=1)
        card = tk.Frame(w, bg=C["side"])
        card.place(relx=0.5, rely=0.46, anchor="center")

        art = tk.Canvas(card, width=460, height=200, bg=C["side"], highlightthickness=0)
        art.pack(pady=(0, 6))
        self._draw_welcome_art(art)

        title = tk.Frame(card, bg=C["side"])
        title.pack()
        tk.Label(title, text="SPARK", font=f["big"], fg=C["orange"], bg=C["side"]).pack(side="left")
        tk.Label(title, text=" Python Lab", font=f["big"], fg="#FFFFFF", bg=C["side"]).pack(side="left")
        tk.Label(card, text="Learn Python step by step, then use it to blink LEDs\n"
                            "and detect movement with a Raspberry Pi!",
                 font=f["lead"], fg=C["side_fg"], bg=C["side"], justify="center").pack(pady=(6, 26))

        name = self.progress.get("name", "")
        tk.Label(card, text="What's your name?", font=f["ui_b"], fg="#FFFFFF", bg=C["side"]).pack()
        self.name_var = tk.StringVar(value=name)
        entry = tk.Entry(card, textvariable=self.name_var, font=f["entry"], width=20, justify="center",
                         bg="#262E57", fg="#FFFFFF", insertbackground=C["yellow"], relief="flat",
                         highlightthickness=2, highlightbackground="#323B6B", highlightcolor=C["orange"])
        entry.pack(pady=(8, 18), ipady=7)
        FlatButton(card, "Continue  ▶" if name else "Let's go!  ▶", self._start_from_welcome,
                   bg=C["orange"], font=f["button_big"], padx=30, pady=10).pack()
        done = self.completed_count()
        if name and done:
            tk.Label(card, text=f"Welcome back! You've finished {done} of {len(LESSONS)} lessons.",
                     font=f["ui"], fg=C["teal"], bg=C["side"]).pack(pady=(14, 0))

        badge, color = self.mode_badge()
        tk.Label(w, text=f"{len(LESSONS)} lessons   ·   {badge}", font=f["small"], fg=C["side_dim"],
                 bg=C["side"]).place(relx=0.5, rely=0.97, anchor="s")
        entry.bind("<Return>", lambda e: self._start_from_welcome())
        entry.focus_set()
        entry.icursor("end")

    def _draw_welcome_art(self, c):
        # A little Raspberry Pi with a wire to a blinking LED.
        round_rect(c, 30, 40, 300, 185, 14, fill="#1E8A4C", outline="#28A85E", width=2)
        for x, y in ((44, 54), (286, 54), (44, 171), (286, 171)):
            c.create_oval(x - 6, y - 6, x + 6, y + 6, fill="#1E8A4C", outline="#D4AF37", width=2)
        c.create_rectangle(68, 46, 270, 66, fill="#111111", outline="")
        for i in range(20):
            for j in range(2):
                x, y = 74 + i * 10, 51 + j * 10
                c.create_rectangle(x - 2, y - 2, x + 2, y + 2, fill="#D4AF37", outline="")
        c.create_rectangle(120, 95, 180, 150, fill="#2B2B2B", outline="#444444")
        c.create_text(150, 122, text="Pi", fill="#9CA3AF", font=self.fonts["ui_b"])
        c.create_rectangle(205, 100, 240, 122, fill="#3A3A3A", outline="")
        for y in (78, 120, 160):
            c.create_rectangle(288, y, 312, y + 30 if y != 160 else y + 18, fill="#B8BCC6", outline="#8A8F9C")
        c.create_text(150, 172, text="print('Hello!')", fill="#B9F6CA", font=self.fonts["code"])
        pin_x = 74 + 5 * 10
        c.create_line(pin_x, 51, pin_x, 22, 330, 14, 400, 60, fill=C["orange"], width=3, smooth=True)
        c.create_line(220, 61, 240, 30, 360, 28, 412, 60, fill="#94A3B8", width=3, smooth=True)
        c.create_line(400, 60, 400, 108, fill="#9CA3AF", width=2)
        c.create_line(412, 60, 412, 100, fill="#9CA3AF", width=2)
        c.create_oval(376, 92, 436, 152, fill=C["side"], outline="", tags="glow")
        c.create_oval(392, 104, 420, 132, fill="#5A1A1A", outline="", tags="led")
        c.create_rectangle(392, 118, 420, 138, fill="#5A1A1A", outline="", tags="led")
        c.create_rectangle(389, 136, 423, 141, fill="#3D1212", outline="", tags="ledrim")
        state = {"on": False}

        def blink():
            if not c.winfo_exists():
                return
            state["on"] = not state["on"]
            on = state["on"]
            c.itemconfigure("led", fill="#FF3B30" if on else "#5A1A1A")
            c.itemconfigure("ledrim", fill="#C22A20" if on else "#3D1212")
            c.itemconfigure("glow", fill=mix(C["side"], "#FF3B30", 0.35) if on else C["side"])
            c.after(600, blink)

        blink()

    def _start_from_welcome(self):
        name = self.name_var.get().strip()[:30] or "Coder"
        self.progress["name"] = name
        save_progress(self.progress)
        self.welcome.destroy()
        self.build_main()
        self.open_lesson(self.progress.get("current", 0))

    # -- main window -------------------------------------------------------
    def build_main(self):
        root, f = self.root, self.fonts
        top = tk.Frame(root, bg=C["night"], height=54)
        top.pack(side="top", fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="SPARK", font=f["logo"], fg=C["orange"], bg=C["night"]).pack(side="left", padx=(18, 0))
        tk.Label(top, text="Python Lab", font=f["logo"], fg="#FFFFFF", bg=C["night"]).pack(side="left", padx=(7, 28))
        self.prog_canvas = tk.Canvas(top, width=200, height=12, bg=C["night"], highlightthickness=0)
        self.prog_canvas.pack(side="left")
        self.prog_label = tk.Label(top, font=f["small_b"], fg=C["side_fg"], bg=C["night"])
        self.prog_label.pack(side="left", padx=10)
        badge, color = self.mode_badge()
        tk.Label(top, text=badge, font=f["small_b"], fg=color, bg=mix(C["night"], color, 0.13),
                 padx=10, pady=4).pack(side="right", padx=(8, 16))
        self.name_label = tk.Label(top, font=f["ui_b"], fg="#FFFFFF", bg=C["night"])
        self.name_label.pack(side="right", padx=8)

        bottom = tk.Frame(root, bg=C["night"])
        bottom.pack(side="bottom", fill="x")
        self.status = tk.Label(bottom, text=SHORTCUTS, font=f["small"], fg=C["side_dim"], bg=C["night"],
                               anchor="w", padx=14, pady=3)
        self.status.pack(side="left", fill="x", expand=True)

        self.paned = tk.PanedWindow(root, orient="horizontal", bg=C["sash"], sashwidth=5, bd=0,
                                    opaqueresize=True)
        self.paned.pack(side="top", fill="both", expand=True)
        self.paned.add(self.build_sidebar(self.paned), minsize=190, stretch="never")
        self.paned.add(self.build_lesson_panel(self.paned), minsize=340, stretch="always")
        self.paned.add(self.build_workspace(self.paned), minsize=430, stretch="always")
        self.build_menu()

        root.bind_all("<F5>", lambda e: self.run_code())
        root.bind_all("<Escape>", lambda e: self.stop_code())
        root.bind_all("<Shift-F5>", lambda e: self.stop_code())
        root.bind_all("<F11>", lambda e: self.toggle_fullscreen())
        root.bind_all("<Control-s>", lambda e: self.manual_save())
        for seq in ("<Control-plus>", "<Control-equal>", "<Control-KP_Add>"):
            root.bind_all(seq, lambda e: self.zoom(1))
        for seq in ("<Control-minus>", "<Control-KP_Subtract>"):
            root.bind_all(seq, lambda e: self.zoom(-1))
        root.bind_all("<Control-0>", lambda e: self.zoom(0, reset=True))
        self.editor.text.bind("<Control-Return>", lambda e: (self.run_code(), "break")[1])
        self.main_built = True
        self.update_header()
        root.after(60, self._place_sashes)

    def _place_sashes(self):
        self.root.update_idletasks()
        w = self.paned.winfo_width()
        side = 230 if w < 1500 else 260
        self.paned.sash_place(0, side, 0)
        self.paned.sash_place(1, side + int((w - side) * 0.46), 0)
        h = self.vpaned.winfo_height()
        self.vpaned.sash_place(0, 0, int(h * 0.58))

    def build_menu(self):
        bar = tk.Menu(self.root)
        lab = tk.Menu(bar, tearoff=0)
        lab.add_command(label="Run code", accelerator="F5", command=self.run_code)
        lab.add_command(label="Stop", accelerator="Esc", command=self.stop_code)
        lab.add_separator()
        lab.add_command(label="Save my code to a file…", command=self.export_code)
        lab.add_separator()
        lab.add_command(label="Bigger text", accelerator="Ctrl +", command=lambda: self.zoom(1))
        lab.add_command(label="Smaller text", accelerator="Ctrl -", command=lambda: self.zoom(-1))
        lab.add_command(label="Full screen", accelerator="F11", command=self.toggle_fullscreen)
        lab.add_separator()
        lab.add_command(label="New student (reset progress)…", command=self.new_student)
        lab.add_separator()
        lab.add_command(label="Quit", command=self.on_close)
        bar.add_cascade(label="Lab", menu=lab)
        helpm = tk.Menu(bar, tearoff=0)
        helpm.add_command(label="Keyboard shortcuts", command=lambda: messagebox.showinfo(
            "Keyboard shortcuts",
            "F5 or Ctrl+Enter: run your code\nEsc: stop your program\nCtrl + / Ctrl -: bigger / smaller text\n"
            "Ctrl+Z: undo\nTab / Shift+Tab: indent / unindent\nF11: full screen"))
        helpm.add_command(label="About", command=lambda: messagebox.showinfo(
            APP_NAME, f"{APP_NAME}\nAn interactive Python and Raspberry Pi workshop.\n\n"
                      f"Mode: {self.mode_badge()[0][2:]}\nProgress is saved in {SAVE_FILE}"))
        bar.add_cascade(label="Help", menu=helpm)
        self.root.configure(menu=bar)

    def build_sidebar(self, parent):
        f = self.fonts
        frame = tk.Frame(parent, bg=C["side"])
        tk.Label(frame, text="LESSONS", font=f["small_b"], fg=C["side_dim"], bg=C["side"],
                 anchor="w").pack(fill="x", padx=18, pady=(16, 6))
        canvas = tk.Canvas(frame, bg=C["side"], highlightthickness=0, bd=0, yscrollincrement=24)
        sb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview, style="Side.Vertical.TScrollbar")
        inner = tk.Frame(canvas, bg=C["side"])
        win = canvas.create_window(0, 0, window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def on_resize(event):
            canvas.itemconfigure(win, width=event.width)
            for item in self.side_items:
                item["title"].configure(wraplength=max(100, event.width - 70))

        canvas.bind("<Configure>", on_resize)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.side_canvas = canvas
        self.side_items = []
        chapter = None
        for i, lesson in enumerate(LESSONS):
            if lesson["chapter"] != chapter:
                chapter = lesson["chapter"]
                tk.Label(inner, text=chapter.upper(), font=f["small_b"], fg=C["orange"], bg=C["side"],
                         anchor="w").pack(fill="x", padx=16, pady=(14 if i else 2, 4))
            row = tk.Frame(inner, bg=C["side"], cursor="hand2")
            row.pack(fill="x", padx=8, pady=1)
            badge = tk.Label(row, text=str(i + 1), width=3, font=f["small_b"], bg=C["side"], fg=C["side_dim"])
            badge.pack(side="left", padx=(4, 2), pady=6)
            title = tk.Label(row, text=lesson["title"], font=f["ui"], bg=C["side"], fg=C["side_fg"],
                             anchor="w", justify="left", wraplength=170)
            title.pack(side="left", fill="x", expand=True, pady=6)
            item = {"row": row, "badge": badge, "title": title, "hover": False}
            self.side_items.append(item)
            for w in (row, badge, title):
                w.bind("<Button-1>", lambda e, idx=i: self.open_lesson(idx))
                w.bind("<Enter>", lambda e, it=item: self._side_hover(it, True))
                w.bind("<Leave>", lambda e, it=item: self._side_hover(it, False))
        self._bind_wheel(frame, canvas)
        return frame

    def _bind_wheel(self, widget, target):
        def on_wheel(event):
            up = getattr(event, "num", 0) == 4 or getattr(event, "delta", 0) > 0
            target.yview_scroll(-2 if up else 2, "units")
            return "break"

        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            widget.bind(seq, on_wheel, add="+")
        for child in widget.winfo_children():
            self._bind_wheel(child, target)

    def _side_hover(self, item, on):
        item["hover"] = on
        self.refresh_sidebar()

    def refresh_sidebar(self):
        done = set(self.progress["completed"])
        for i, item in enumerate(self.side_items):
            current = i == self.lesson_index
            finished = LESSONS[i]["id"] in done
            bg = C["orange"] if current else (C["side_hover"] if item["hover"] else C["side"])
            fg = "#FFFFFF" if current else C["side_fg"]
            badge_fg = "#FFFFFF" if current else (C["teal"] if finished else C["side_dim"])
            for w in (item["row"], item["badge"], item["title"]):
                w.configure(bg=bg)
            item["title"].configure(fg=fg, font=self.fonts["ui_b"] if current else self.fonts["ui"])
            item["badge"].configure(text="✓" if finished else str(i + 1), fg=badge_fg)

    def _scroll_sidebar_to(self, idx):
        self.root.update_idletasks()
        row = self.side_items[idx]["row"]
        total = max(1, self.side_canvas.bbox("all")[3])
        y, h = row.winfo_y(), self.side_canvas.winfo_height()
        top, bottom = self.side_canvas.canvasy(0), self.side_canvas.canvasy(h)
        if y < top or y + row.winfo_height() > bottom:
            self.side_canvas.yview_moveto(max(0, (y - h / 3) / total))

    def build_lesson_panel(self, parent):
        f = self.fonts
        frame = tk.Frame(parent, bg=C["paper"])
        head = tk.Frame(frame, bg=C["paper"])
        head.pack(side="top", fill="x", padx=26, pady=(18, 2))
        self.kicker = tk.Label(head, font=f["small_b"], fg=C["purple"], bg=C["paper"], anchor="w")
        self.kicker.pack(fill="x")
        self.title_lbl = tk.Label(head, font=f["title"], fg=C["ink"], bg=C["paper"], anchor="w", justify="left")
        self.title_lbl.pack(fill="x")
        head.bind("<Configure>", lambda e: self.title_lbl.configure(wraplength=max(200, e.width - 10)))

        foot = tk.Frame(frame, bg=C["paper_dim"])
        foot.pack(side="bottom", fill="x")
        self.challenge_lbl = tk.Label(foot, font=f["ui_b"], bg=C["paper_dim"], anchor="w", padx=20, pady=12)
        self.challenge_lbl.pack(side="left")
        self.next_btn = FlatButton(foot, "Next  ▶", lambda: self.open_lesson(self.lesson_index + 1),
                                   bg=C["orange"], font=f["ui_b"], padx=18, pady=7)
        self.next_btn.pack(side="right", padx=(4, 14), pady=8)
        self.back_btn = FlatButton(foot, "◀  Back", lambda: self.open_lesson(self.lesson_index - 1),
                                   bg="#DCD6C8", fg=C["ink"], font=f["ui_b"], padx=16, pady=7)
        self.back_btn.pack(side="right", pady=8)

        self.board = BoardPanel(frame, self)

        body = self.lesson_body = tk.Frame(frame, bg=C["paper"])
        body.pack(side="top", fill="both", expand=True)
        t = self.lesson_text = tk.Text(body, wrap="word", bg=C["paper"], fg=C["ink"], font=f["body"], bd=0,
                                       highlightthickness=0, padx=26, pady=6, cursor="arrow",
                                       spacing1=2, spacing2=0, spacing3=2, insertwidth=0, takefocus=0)
        sb = ttk.Scrollbar(body, orient="vertical", command=t.yview, style="Light.Vertical.TScrollbar")
        t.configure(yscrollcommand=sb.set, state="disabled")
        sb.pack(side="right", fill="y")
        t.pack(side="left", fill="both", expand=True)
        self._config_lesson_tags()
        return frame

    def _config_lesson_tags(self):
        t, f = self.lesson_text, self.fonts

        def box(tag, bg, fg, **extra):
            opts = dict(background=bg, foreground=fg, lmargin1=16, lmargin2=16, rmargin=12, **extra)
            try:
                t.tag_configure(tag, lmargincolor=bg, rmargincolor=bg, **opts)
            except tk.TclError:  # Tk older than 8.6.6
                t.tag_configure(tag, **opts)

        box("tip", "#FFF3D1", "#5C4400")
        box("task", "#DDF7F2", "#0B4F48")
        box("codeblock", C["ed_bg"], C["ed_fg"], font=f["code"], spacing1=1, spacing3=1)
        t.tag_configure("h2", font=f["h2"], foreground=C["purple"], spacing1=12, spacing3=4)
        t.tag_configure("bullet", lmargin1=8, lmargin2=26)
        t.tag_configure("bold", font=f["body_b"])
        t.tag_configure("italic", font=f["body_i"])
        t.tag_configure("icode", font=f["code"], background="#EFEBFF", foreground="#5B3CC4")
        t.tag_configure("tasklabel", font=f["small_b"], foreground="#0E8C7F")
        t.tag_configure("pad", font=f["pad"], spacing1=0, spacing3=0)
        for name, color in SYNTAX.items():
            t.tag_configure("ls_" + name, foreground=color)
        t.tag_configure("ls_comment", font=f["code_i"])
        t.tag_raise("sel")

    def build_workspace(self, parent):
        f = self.fonts
        frame = self.work_frame = tk.Frame(parent, bg=C["ed_bg"])
        bar = tk.Frame(frame, bg=C["toolbar"])
        bar.pack(side="top", fill="x")
        self.run_btn = FlatButton(bar, "▶  Run", self.run_code, bg=C["green"], font=f["ui_b"], padx=20, pady=7)
        self.run_btn.pack(side="left", padx=(10, 6), pady=8)
        self.stop_btn = FlatButton(bar, "■  Stop", self.stop_code, bg=C["red"], font=f["ui_b"], padx=16, pady=7)
        self.stop_btn.pack(side="left", pady=8)
        small = dict(bg=C["tool_btn"], fg=C["side_fg"], font=f["small_b"], padx=10, pady=5)
        FlatButton(bar, "A+", lambda: self.zoom(1), **small).pack(side="right", padx=(2, 10))
        FlatButton(bar, "A−", lambda: self.zoom(-1), **small).pack(side="right", padx=2)
        self.solution_btn = FlatButton(bar, "Solution", self.show_solution, **small)
        self.solution_btn.pack(side="right", padx=(2, 12))
        self.reset_btn = FlatButton(bar, "Reset", self.reset_code, **small)
        self.reset_btn.pack(side="right", padx=2)
        self.hint_btn = FlatButton(bar, "Hint", self.show_hint, bg=C["purple"], fg="#FFFFFF",
                                   font=f["small_b"], padx=12, pady=5)
        self.hint_btn.pack(side="right", padx=2)

        vp = self.vpaned = tk.PanedWindow(frame, orient="vertical", bg=C["sash"], sashwidth=5, bd=0,
                                          opaqueresize=True)
        vp.pack(side="top", fill="both", expand=True)
        self.editor = CodeEditor(vp, self)
        self.console = Console(vp, self)
        vp.add(self.editor, minsize=140, stretch="always")
        vp.add(self.console, minsize=120, stretch="always")
        self.stop_btn.set_enabled(False)
        return frame

    # -- lessons -----------------------------------------------------------
    def completed_count(self):
        ids = {lesson["id"] for lesson in LESSONS}
        return len(ids & set(self.progress["completed"]))

    def update_header(self):
        c = self.prog_canvas
        c.delete("all")
        w, h = int(c.cget("width")), int(c.cget("height"))
        done, total = self.completed_count(), len(LESSONS)
        round_rect(c, 0, 0, w, h, h / 2, fill="#2A3158", outline="")
        if done:
            round_rect(c, 0, 0, max(h, w * done / total), h, h / 2, fill=C["teal"], outline="")
        self.prog_label.configure(text=f"{done} / {total} challenges")
        self.name_label.configure(text=f"Hi, {self.progress.get('name') or 'Coder'}!")

    def update_challenge_label(self):
        lesson = LESSONS[self.lesson_index]
        if lesson.get("check") is None:
            text, color = "★  Free play: no challenge, just have fun!", C["purple"]
        elif lesson["id"] in self.progress["completed"]:
            text, color = "✓  Challenge complete!", "#0E8C7F"
        else:
            text, color = "◆  Challenge not done yet", "#C2630E"
        self.challenge_lbl.configure(text=text, fg=color)

    def open_lesson(self, idx):
        idx = max(0, min(len(LESSONS) - 1, idx))
        if self.run is not None:
            self.stop_code(quiet=True)
        self.close_overlay()
        self.save_code()
        self.lesson_index = idx
        self.progress["current"] = idx
        lesson = LESSONS[idx]
        self.kicker.configure(text=f"LESSON {idx + 1} OF {len(LESSONS)}   ·   {lesson['chapter'].upper()}")
        self.title_lbl.configure(text=lesson["title"])
        self.render_lesson(lesson)
        self.editor.set_code(self.progress["code"].get(lesson["id"], lesson["code"]))
        if lesson.get("hardware"):
            self.board.set_lesson(lesson)
            self.board.pack(side="bottom", fill="x", before=self.lesson_body)
            self.board_visible = True
        else:
            self.board.pack_forget()
            self.board_visible = False
        self.hint_btn.set_enabled(bool(lesson.get("hint")))
        self.solution_btn.set_enabled(bool(lesson.get("solution")))
        self.back_btn.set_enabled(idx > 0)
        self.next_btn.set_enabled(idx < len(LESSONS) - 1)
        self.update_challenge_label()
        self.refresh_sidebar()
        self._scroll_sidebar_to(idx)
        self.console.clear()
        self.console.write(f"Lesson {idx + 1}: {lesson['title']}\n", "info_b")
        self.console.write("Read the lesson, then press ▶ Run (or F5) to run the code.\n", "info")
        self.editor.text.focus_set()
        save_progress(self.progress)

    def render_lesson(self, lesson):
        t = self.lesson_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        self._render(lesson["body"])
        if lesson.get("task"):
            t.insert("end", "\n", ("pad",))
            t.insert("end", "\n", ("task", "pad"))
            t.insert("end", "★  YOUR CHALLENGE\n", ("task", "tasklabel"))
            self._render(lesson["task"], extra=("task",))
            t.insert("end", "\n", ("task", "pad"))
        t.insert("end", "\n\n", ("pad",))
        t.configure(state="disabled")
        t.yview_moveto(0)

    def _render(self, md, extra=()):
        """Turn the lessons' tiny markdown into tagged text."""
        t = self.lesson_text
        lines = dedent(md).strip("\n").splitlines()
        para = []

        def flush():
            if para:
                self._inline(" ".join(para), extra)
                t.insert("end", "\n", extra)
                t.insert("end", "\n", ("pad",) + extra)
                para.clear()

        i = 0
        while i < len(lines):
            line = lines[i]
            s = line.strip()
            if s.startswith("```"):
                flush()
                code = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code.append(lines[i])
                    i += 1
                i += 1
                self._code_block(dedent("\n".join(code)), extra)
            elif not s:
                flush()
                i += 1
            elif s.startswith("## "):
                flush()
                t.insert("end", s[3:] + "\n", ("h2",) + extra)
                i += 1
            elif s.startswith("- "):
                flush()
                while i < len(lines) and lines[i].strip().startswith("- "):
                    self._inline("•   " + lines[i].strip()[2:], ("bullet",) + extra)
                    t.insert("end", "\n", ("bullet",) + extra)
                    i += 1
                t.insert("end", "\n", ("pad",) + extra)
            elif s.startswith(">"):
                flush()
                tip = []
                while i < len(lines) and lines[i].strip().startswith(">"):
                    tip.append(lines[i].strip()[1:].strip())
                    i += 1
                t.insert("end", "\n", ("tip", "pad"))
                self._inline(" ".join(tip), ("tip",))
                t.insert("end", "\n", ("tip",))
                t.insert("end", "\n", ("tip", "pad"))
                t.insert("end", "\n", ("pad",))
            else:
                para.append(s)
                i += 1
        flush()

    def _code_block(self, code, extra):
        t = self.lesson_text
        t.insert("end", "\n", ("codeblock", "pad") + extra)
        start = t.index("end-1c")
        t.insert("end", code + "\n", ("codeblock",) + extra)
        apply_syntax(t, code, start, prefix="ls_")
        t.insert("end", "\n", ("codeblock", "pad") + extra)
        t.insert("end", "\n", ("pad",) + extra)

    def _inline(self, text, tags):
        t = self.lesson_text
        for part in INLINE_RE.split(text):
            if not part:
                continue
            if len(part) > 2 and part.startswith("`") and part.endswith("`"):
                t.insert("end", part[1:-1], tuple(tags) + ("icode",))
            elif len(part) > 4 and part.startswith("**") and part.endswith("**"):
                t.insert("end", part[2:-2], tuple(tags) + ("bold",))
            elif len(part) > 2 and part.startswith("*") and part.endswith("*"):
                t.insert("end", part[1:-1], tuple(tags) + ("italic",))
            else:
                t.insert("end", part, tuple(tags))

    # -- toolbar actions ---------------------------------------------------
    def save_code(self):
        if not self.main_built or self.lesson_index is None:
            return
        lesson = LESSONS[self.lesson_index]
        code = self.editor.get_code()
        if code.strip() and code != lesson["code"]:
            self.progress["code"][lesson["id"]] = code
        else:
            self.progress["code"].pop(lesson["id"], None)

    def manual_save(self):
        self.save_code()
        save_progress(self.progress)
        self.status_msg("Saved! Your code is also saved automatically.")
        return "break"

    def show_hint(self):
        hint = LESSONS[self.lesson_index].get("hint")
        if hint:
            self.console.write("\nHINT\n", "hint_title")
            self.console.write(hint.rstrip() + "\n", "hint")

    def show_solution(self):
        solution = LESSONS[self.lesson_index].get("solution")
        if not solution:
            return
        if messagebox.askyesno("Peek at the answer?",
                               "Have you had a good try yourself first?\n\n"
                               "The solution will replace your code. (Ctrl+Z brings yours back.)"):
            self.editor.replace_code(solution)

    def reset_code(self):
        if messagebox.askyesno("Start this lesson's code again?",
                               "This puts the lesson's starting code back in the editor.\n"
                               "(Ctrl+Z brings your code back.)"):
            self.editor.replace_code(LESSONS[self.lesson_index]["code"])

    def export_code(self):
        if not self.main_built:
            return
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = filedialog.asksaveasfilename(
            title="Save my code", defaultextension=".py", filetypes=[("Python files", "*.py")],
            initialdir=desktop if os.path.isdir(desktop) else os.path.expanduser("~"),
            initialfile=f"lesson{self.lesson_index + 1:02d}_{LESSONS[self.lesson_index]['id']}.py")
        if path:
            try:
                with open(path, "w") as fh:
                    fh.write(self.editor.get_code())
                self.status_msg(f"Saved to {path}")
            except OSError as exc:
                messagebox.showerror("Couldn't save", str(exc))

    def zoom(self, delta, reset=False):
        z = 0 if reset else max(-4, min(14, self.progress.get("zoom", 0) + delta))
        self.progress["zoom"] = z
        self.apply_zoom()
        if self.board_visible:
            self.board.redraw()
        save_progress(self.progress)
        return "break"

    def toggle_fullscreen(self):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def new_student(self):
        name = simpledialog.askstring("New student", "This clears all saved progress and code.\n\n"
                                                     "What's the new student's name?", parent=self.root)
        if name is None:
            return
        if self.run is not None:
            self.stop_code(quiet=True)
        zoom = self.progress.get("zoom", 0)
        self.progress = fresh_progress()
        self.progress.update(name=name.strip()[:30] or "Coder", zoom=zoom)
        self.lesson_index = None
        save_progress(self.progress)
        self.update_header()
        self.open_lesson(0)

    def status_msg(self, text, ms=5000):
        if not self.main_built:
            return
        self.status.configure(text=text, fg=C["yellow"])
        if self._status_job:
            self.root.after_cancel(self._status_job)
        self._status_job = self.root.after(ms, lambda: self.status.configure(text=SHORTCUTS, fg=C["side_dim"]))

    # -- running code ------------------------------------------------------
    def prepare_gpio(self, code):
        """In simulator mode, give each run a fresh set of virtual pins."""
        if self.mode != "sim" or not self.gpio_ok or "gpiozero" not in code:
            return
        try:
            from gpiozero import Device
            from gpiozero.pins.mock import MockFactory, MockPWMPin
            old = Device.pin_factory
            Device.pin_factory = MockFactory(pin_class=MockPWMPin)
            if old is not None:
                try:
                    old.close()
                except Exception:
                    pass
        except Exception as exc:
            self.console.write(f"(Couldn't start the GPIO simulator: {exc})\n", "stderr")

    def run_code(self):
        if not self.main_built or self.run is not None:
            return "break"
        self.close_overlay()
        code = self.editor.get_code()
        self.save_code()
        save_progress(self.progress)
        self.editor.clear_error()
        self.console.clear()
        if not code.strip():
            self.console.write("Your code box is empty! Type some code first.\n", "warn")
            return "break"
        self.console.write(f"▶ Running lesson {self.lesson_index + 1}...\n", "info")
        self.prepare_gpio(code)
        self.run_output = []
        self.run_rises, self.run_seen_high, self.run_inputs_high, self._pin_prev = {}, set(), set(), {}
        if self.board_visible:
            self.board.reset_for_run()
        run = Run(code, self.outq, self.lesson_index)
        self.run = run
        ACTIVE.run = run
        self.set_running(True)
        run.thread.start()
        return "break"

    def stop_code(self, quiet=False):
        run = self.run
        if run is None or run.stop_flag.is_set():
            return "break"
        run.stop_flag.set()
        self.console.cancel_input()
        if not quiet:
            self.console.write("\n■ Stopping...\n", "info")
        self.root.after(2500, lambda: self._force_stop(run))
        return "break"

    def _force_stop(self, run):
        """If the program is stuck somewhere Stop can't reach, give up on it."""
        if self.run is run and run.thread.is_alive():
            _ABANDONED.add(run.thread)
            close_gpio_devices()
            self.finish_run("stopped", None, forced=True)

    def answer_input(self, text):
        run = self.run
        if run is not None:
            run.input_reply = text
            run.input_ready.set()

    def set_running(self, on):
        self.run_btn.set_enabled(not on)
        self.stop_btn.set_enabled(on)
        self.console.state_lbl.configure(text="●  RUNNING" if on else "")

    def poll(self):
        try:
            self._drain_output()
            if "gpiozero" in sys.modules:
                self.track_pins()
        except Exception:
            traceback.print_exc(file=sys.__stderr__)
        self.root.after(30, self.poll)

    def _drain_output(self):
        pending = []

        def flush():
            for kind, text in pending:
                self.console.write(text, "out" if kind == "out" else "stderr")
            pending.clear()

        for _ in range(500):
            try:
                rid, kind, payload = self.outq.get_nowait()
            except queue.Empty:
                break
            if self.run is None or rid != self.run.id:
                continue
            if kind in ("out", "err"):
                if kind == "out":
                    self.run_output.append(payload)
                if pending and pending[-1][0] == kind:
                    pending[-1][1] += payload
                else:
                    pending.append([kind, payload])
            elif kind == "input":
                flush()
                self.console.ask_input()
            elif kind == "done":
                flush()
                self.finish_run(*payload)
        flush()

    def track_pins(self):
        snapshot = gpio_snapshot()
        if self.run is not None:
            for bcm, kind, _name, value, _dev in snapshot:
                high = value > 0.5
                if kind == "out":
                    if high and not self._pin_prev.get(bcm, False):
                        self.run_rises[bcm] = self.run_rises.get(bcm, 0) + 1
                    if high:
                        self.run_seen_high.add(bcm)
                elif high:
                    self.run_inputs_high.add(bcm)
                self._pin_prev[bcm] = high
        if self.board_visible:
            self.board.update_pins(snapshot)

    def sim_drive_inputs(self, active):
        """Simulator only: make every sensor in use see (or stop seeing) movement."""
        gz = sys.modules.get("gpiozero")
        if self.mode != "sim" or gz is None or gz.Device.pin_factory is None:
            return []
        driven = []
        for bcm, kind, _name, _value, dev in gpio_snapshot():
            if kind != "in":
                continue
            try:
                pin = gz.Device.pin_factory.pin(bcm)
                high = active != bool(getattr(dev, "pull_up", False))
                (pin.drive_high if high else pin.drive_low)()
                driven.append(bcm)
            except Exception:
                pass
        return driven

    def finish_run(self, status, err, forced=False):
        run = self.run
        if run is None:
            return
        self.run = None
        ACTIVE.run = None
        self.console.cancel_input()
        self.set_running(False)
        if "gpiozero" in sys.modules and self.board_visible:
            self.board.update_pins(gpio_snapshot())
        output = "".join(self.run_output)
        if output and not output.endswith("\n"):
            self.console.write("\n")
        if status == "error":
            self.show_error(err)
        elif status == "stopped":
            note = " (It was stuck, so it was force-stopped.)" if forced else ""
            self.console.write(f"■ Program stopped.{note}\n", "info")
        else:
            self.console.write("✓ Program finished.\n", "info")
        if run.lesson_index == self.lesson_index:
            result = RunResult(run.code, output, status, dict(self.run_rises),
                               set(self.run_seen_high), set(self.run_inputs_high))
            self.evaluate(result)

    def show_error(self, err):
        if not err:
            return
        where = f"   (line {err['line']})" if err.get("line") else ""
        self.console.write(f"\n✗ Oops! {err['title']}{where}\n", "err_title")
        if err.get("source"):
            self.console.write(f"  {err['line']} │ {err['source']}\n", "err_code")
        self.console.write(f"{err['detail']}\n", "err_detail")
        self.console.write(f"Python says: {err['type']}: {err['message']}\n", "info")
        if err.get("line"):
            self.editor.mark_error(err["line"])

    def evaluate(self, result):
        lesson = LESSONS[self.lesson_index]
        if result.status == "error":
            return
        check = lesson.get("check")
        if check is None:
            if result.status == "ok":
                self.complete_lesson(celebrate=False)
            return
        try:
            passed, message = check(result)
        except Exception as exc:
            passed, message = False, f"(the lesson checker had a problem: {exc})"
        if passed:
            self.console.write(f"\n★ Challenge complete! {message}\n", "success")
            self.complete_lesson(celebrate=True, message=message)
        else:
            self.console.write(f"\n◆ Not quite yet: {message}\n", "warn")

    def complete_lesson(self, celebrate, message=""):
        lesson = LESSONS[self.lesson_index]
        if lesson["id"] in self.progress["completed"]:
            return
        self.progress["completed"].append(lesson["id"])
        save_progress(self.progress)
        self.update_header()
        self.update_challenge_label()
        self.refresh_sidebar()
        if celebrate:
            self.celebrate(message)

    # -- celebration ---------------------------------------------------------
    def close_overlay(self):
        if self.overlay is not None:
            self.overlay.destroy()
            self.overlay = None

    def celebrate(self, message):
        self.close_overlay()
        f = self.fonts
        host = self.editor
        w, h = max(host.winfo_width(), 300), max(host.winfo_height(), 260)
        c = self.overlay = tk.Canvas(host, bg=C["ed_bg"], highlightthickness=0, bd=0)
        c.place(x=0, y=0, relwidth=1, relheight=1)
        colors = [C["orange"], C["yellow"], C["teal"], C["purple"], "#FF5C8A", "#6FC3FF", "#4ADE80"]
        bits = []
        for _ in range(110):
            x, y, s = random.uniform(0, w), random.uniform(-h, 0), random.uniform(6, 12)
            item = c.create_rectangle(x, y, x + s, y + s * 0.6, fill=random.choice(colors), outline="")
            bits.append((item, random.uniform(-1.2, 1.2), random.uniform(4, 8)))
        done, total = self.completed_count(), len(LESSONS)
        cy = max(60, (h - 250) / 2 + 50)
        c.create_text(w / 2, cy, text="★", font=f["huge"], fill=C["yellow"])
        c.create_text(w / 2, cy + 74, text="CHALLENGE COMPLETE!", font=f["title"], fill="#FFFFFF")
        c.create_text(w / 2, cy + 112, text=message, font=f["lead"], fill=C["side_fg"], width=w - 80,
                      justify="center")
        c.create_text(w / 2, cy + 150, text=f"Great job, {self.progress.get('name') or 'Coder'}!   "
                                            f"{done} of {total} done", font=f["ui_b"], fill=C["teal"])
        buttons = tk.Frame(c, bg=C["ed_bg"])
        FlatButton(buttons, "Stay here", self.close_overlay, bg=C["tool_btn"], fg=C["side_fg"],
                   font=f["ui_b"], padx=16, pady=8).pack(side="left", padx=6)
        if self.lesson_index < len(LESSONS) - 1:
            FlatButton(buttons, "Next lesson  ▶", lambda: self.open_lesson(self.lesson_index + 1),
                       bg=C["orange"], font=f["ui_b"], padx=18, pady=8).pack(side="left", padx=6)
        c.create_window(w / 2, cy + 200, window=buttons)
        c.bind("<Button-1>", lambda e: self.close_overlay())
        frames = {"n": 0}

        def fall():
            if self.overlay is not c:
                return
            for item, vx, vy in bits:
                c.move(item, vx, vy)
            frames["n"] += 1
            if frames["n"] < 140:
                c.after(30, fall)

        fall()

    # -- shutting down -------------------------------------------------------
    def on_close(self):
        if self.run is not None:
            self.run.stop_flag.set()
        self.save_code()
        save_progress(self.progress)
        self.root.destroy()


def main():
    if "--reset" in sys.argv:
        try:
            os.remove(SAVE_FILE)
        except OSError:
            pass
    mode = detect_mode(sys.argv)
    if mode == "sim":
        # Belt and braces: any gpiozero device made outside a run also uses fake pins.
        os.environ.setdefault("GPIOZERO_PIN_FACTORY", "mock")
        os.environ.setdefault("GPIOZERO_MOCK_PIN_CLASS", "mockpwmpin")
    install_runtime_patches()

    root = tk.Tk(className="SparkLab")
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    width, height = min(1440, sw - 40), min(900, sh - 80)
    root.geometry(f"{width}x{height}+{(sw - width) // 2}+{max(0, (sh - height) // 3)}")
    root.minsize(min(1000, sw - 40), min(640, sh - 80))
    if sw <= 1920 and sys.platform.startswith("linux"):
        try:
            root.attributes("-zoomed", True)
        except tk.TclError:
            pass
    SparkLab(root, mode)
    root.mainloop()


if __name__ == "__main__":
    main()
