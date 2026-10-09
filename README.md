# SPARK Python Lab

An interactive, step-by-step Python workshop app for the Raspberry Pi 4B. Students read
a short lesson, write code in a built-in editor, press **Run** and get a challenge
checked automatically. Lessons start with `print()` and work up to blinking an LED and
detecting movement with a PIR sensor.

- 22 lessons: 13 on Python basics, 8 on Raspberry Pi hardware, and a free-play page
- A colour-coded code editor with line numbers, auto-indent and big-text zoom for projectors
- Friendly error messages ("A quote mark is missing (line 8)") with the bad line marked in red
- A **live GPIO view** that shows the 40-pin header, the wiring for each lesson, and whether the LED is on or the sensor sees motion
- A **simulator** for when there's no Pi (e.g. instructors preparing on a laptop), with a *Wave at sensor* button
- Progress, name and code are saved automatically

## Setup (once per Raspberry Pi)

```bash
git clone <this repo> ~/SPARK_Workshop
cd ~/SPARK_Workshop
./install.sh
```

This installs anything missing (`python3-tk`, `python3-gpiozero` and `python3-lgpio` are
normally already on Raspberry Pi OS). It also puts a **SPARK Python Lab** icon on the desktop
and in the **Education** menu.

## Running it

| Command | What it does |
|---|---|
| `python3 spark_lab.py` | Normal start. Uses real GPIO pins on a Pi, or the simulator anywhere else |
| `python3 spark_lab.py --sim` | Forces the on-screen simulator, even on a Pi |
| `python3 spark_lab.py --reset` | Starts fresh: forgets the name, progress and saved code |

To switch between students during the day, use **Lab → New student** in the menu.

Keyboard shortcuts: **F5** run · **Esc** stop · **Ctrl +/−** text size · **F11** full screen.

## Hardware for each Pi

| Part | Qty | Used from lesson |
|---|---|---|
| LED (any colour) | 1 | 15 |
| 220Ω–330Ω resistor | 1 | 15 |
| HC-SR501 PIR motion sensor | 1 | 19 |
| Breadboard + female-to-male jumper wires | 5 wires | 15 |

### Wiring

```
LED:   pin 11 (GPIO17) ── resistor ── LED long leg (+)
       pin 9  (GND)    ────────────── LED short leg (−)

PIR:   pin 2 (5V)      ── PIR VCC
       pin 7 (GPIO4)   ── PIR OUT
       pin 6 (GND)     ── PIR GND
```

The app shows this on a pin map under each hardware lesson. The HC-SR501 needs
**30–60 seconds to warm up** after power-on. Turning its "time" knob fully anticlockwise
gives the shortest on-time (about 3 s), which makes the lessons snappier.

## Lessons

**Python basics:** 1 Hello, World! · 2 Python is a Calculator · 3 Variables · 4 Types of Data ·
5 Playing with Text · 6 Talking to the Computer (`input`) · 7 if / else ·
8 for loops · 9 while loops & time · 10 Lists · 11 Functions · 12 return · 13 Bug Hunt

**Raspberry Pi hardware:** 14 Meet the GPIO pins · 15 Light up an LED · 16 Blink! ·
17 SOS in Morse code · 18 Dimmer switch (PWM) · 19 Meet the motion sensor ·
20 Motion-activated light · 21 Final project: burglar alarm

**Free play:** 22 Your playground

## For instructors

- **Editing lessons:** everything is in [lessons.py](lessons.py). Each lesson is a plain dict with
  the explanation (simple markdown), starter code, challenge text, hint, solution and a
  small `check()` function. The comment at the top of the file explains the fields.
- **Saved data** lives in `~/.spark_python_lab/progress.json`.
- **Stop always works.** It interrupts forever-loops, `sleep()`, `input()`, `pause()` and
  `wait_for_motion()`. Students' programs run inside the app, so a stuck program never
  freezes the window.
- When a program ends or is stopped, gpiozero devices are closed (the LED goes off), just
  like when a normal Python script finishes.

## Troubleshooting

| Problem | Fix |
|---|---|
| "That pin is already in use" | The code creates `LED(17)` twice. Each part should be created once. |
| LED doesn't light | Check the LED is the right way round (long leg towards GPIO17) and that the wire is on pin 11, not GPIO11. |
| PIR triggers by itself | It's still warming up, or the sensitivity knob is too high. |
| Desktop icon asks "Execute?" | Choose **Execute**, or in File Manager → Preferences tick *Don't ask options on launch executable file*. |
| "Can't reach the GPIO pins" on a laptop | Expected: start with `--sim`. |
