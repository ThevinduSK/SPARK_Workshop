"""
Lessons for SPARK Python Lab.

Each lesson is a dict:
    id        unique short name, used to save progress (don't rename once students start)
    chapter   the sidebar heading it sits under
    title     shown in the sidebar and at the top of the lesson
    body      the explanation, written in a tiny markdown:
                  ## heading        - bullet point        > tip box (every line starts with >)
                  ```code block```  `inline code`        **bold**
    code      starter code placed in the editor
    task      the challenge (same markdown), shown in a green box
    hint      shown when the student presses Hint
    solution  shown (after a warning) when the student presses Solution
    check     function(result) -> (passed, message). `result` has:
                  .code         the student's code
                  .output       everything the program printed
                  .ok           True if it finished or was stopped without an error
                  .blinks       most times any output pin (LED) switched on
                  .seen_high    set of GPIO numbers that were switched on
                  .inputs_high  set of GPIO numbers whose sensor became active
    hardware  True to show the GPIO board panel under the lesson
    wiring    [(physical_pin, description, colour), ...] highlighted on that board
"""

import re

CHAPTERS = ["Python Basics", "Raspberry Pi Hardware", "Free Play"]

# Wire colours used on the GPIO map.
SIGNAL = "#FF7A1A"
GROUND = "#94A3B8"
POWER = "#EF4444"
SENSOR = "#FFD23F"


# ---------------------------------------------------------------------------
# Little helpers for the checks
# ---------------------------------------------------------------------------

def _lines(r):
    return [line.strip() for line in r.output.splitlines() if line.strip()]


def _out(r):
    """Output in lower case with runs of spaces squashed, for forgiving comparisons."""
    return re.sub(r"[ \t]+", " ", r.output.lower())


def _count_lines(r, word):
    return sum(1 for line in _lines(r) if word in line.lower())


def _code(r):
    """The code with comments removed, so commented-out lines don't count."""
    return "\n".join(line.split("#", 1)[0] for line in r.code.splitlines())


# ---------------------------------------------------------------------------
# Chapter 1 - Python Basics
# ---------------------------------------------------------------------------

def check_hello(r):
    lines = _lines(r)
    if len(lines) < 2:
        return False, "Add a second print() line so that two messages appear."
    if all(line == "Hello, World!" for line in lines):
        return False, "Change the message so it says hello to you."
    return True, "Two messages printed. You're officially a programmer!"


def check_maths(r):
    if "86400" not in r.output:
        return False, "The answer should be 86400. Multiply 60, 60 and 24 together."
    if "*" not in _code(r):
        return False, "Let Python do the maths! Use * to multiply instead of typing the answer."
    return True, "86400 seconds in a day. Python is a speedy calculator!"


def check_variables(r):
    code = _code(r)
    for name in ("slices", "friends", "each"):
        if not re.search(r"\b%s\s*=" % name, code):
            return False, f"Create a variable called {name} using =."
    if "2" not in r.output:
        return False, "Print the variable each. It should show 2 (or 2.0)."
    return True, "Each friend gets 2 slices. Fair sharing!"


def check_types(r):
    out = r.output
    if "<class 'str'>" not in out:
        return False, 'Print the type of "42" (with quotes). It should say <class \'str\'>.'
    if "<class 'int'>" not in out:
        return False, "Print the type of 42 (no quotes). It should say <class 'int'>."
    if not re.search(r"\b50\b", out):
        return False, 'Use int("42") to turn the text into a number, then add 8 to get 50.'
    return True, "You can tell text and numbers apart, and convert between them."


def check_strings(r):
    code = _code(r)
    if not re.search(r"\bf[\"']", code):
        return False, 'Use an f-string: put f before the quote, like f"My name is {name}".'
    if "love" not in _out(r):
        return False, "Print a sentence like: My name is Sam and I love football!"
    if not any(line.isupper() for line in _lines(r)):
        return False, "Also print your name in CAPITAL letters with .upper()"
    return True, "Strings mastered, f-strings and all!"


def check_input(r):
    code = _code(r)
    if code.count("input(") < 2:
        return False, "Ask for two numbers, which means two input() calls."
    if "int(" not in code and "float(" not in code:
        return False, "input() gives text. Wrap it in int() so Python can add the numbers."
    if not r.ok:
        return False, "Run your program and answer both questions."
    return True, "You built a calculator that talks to people!"


def check_if(r):
    code = _code(r)
    for word in ("if ", "elif ", "else"):
        if word not in code:
            return False, f"Your game needs if, elif AND else. {word.strip()} is missing."
    if "input(" not in code:
        return False, "Ask the player for their guess with input()."
    if not any(word in _out(r) for word in ("got it", "too low", "too high")):
        return False, 'Print "You got it!", "Too low!" or "Too high!" depending on the guess.'
    return True, "Your program can make decisions now!"


def check_for(r):
    out = _out(r)
    if "for " not in _code(r):
        return False, "Use a for loop instead of writing ten print lines."
    if "5 x 1 = 5" not in out or "5 x 10 = 50" not in out:
        return False, "Print every line from 5 x 1 = 5 to 5 x 10 = 50 (hint: range(1, 11))."
    return True, "Ten lines from one loop. That's the power of loops!"


def check_while(r):
    if "while" not in _code(r):
        return False, "Use a while loop for the countdown."
    if "10" not in _lines(r):
        return False, "Start the countdown at 10."
    if "blast off" not in _out(r):
        return False, 'Finish by printing "Blast off!"'
    return True, "3... 2... 1... Lift-off!"


def check_lists(r):
    code = _code(r)
    if ".append(" not in code:
        return False, "Add your own name to the list with team.append(...)"
    if "for " not in code:
        return False, "Use a for loop to go through the list."
    if _count_lines(r, "welcome") < 4:
        return False, "Print a welcome message for all 4 people on the team."
    return True, "Everyone is welcome on your team!"


def check_functions(r):
    if not re.search(r"def\s+birthday\s*\(", _code(r)):
        return False, "Create a function with def birthday(name, age):"
    if _count_lines(r, "happy birthday") < 2:
        return False, "Call birthday(...) twice with different names and ages."
    return True, "Party time! Your function works."


def check_return(r):
    code = _code(r)
    if not re.search(r"def\s+area\s*\(", code):
        return False, "Create a function with def area(width, height):"
    if "return" not in code:
        return False, "Use return to give the answer back from your function."
    if not (re.search(r"\b15\b", r.output) and re.search(r"\b56\b", r.output)):
        return False, "Print area(5, 3) and area(7, 8). The answers are 15 and 56."
    return True, "Your function gives answers back with return."


def check_bugs(r):
    out = _out(r)
    for who, score in (("ada", 10), ("alan", 7), ("grace", 12)):
        if f"{who} scored {score} points" not in out:
            return False, f"{who.title()}'s score isn't printing yet. Keep hunting!"
    return True, "All three bugs squashed. You're a real debugger!"


# ---------------------------------------------------------------------------
# Chapter 2 - Raspberry Pi Hardware
# ---------------------------------------------------------------------------

def check_gpio_ready(r):
    if "all good" not in _out(r):
        return False, "Run the code until you see All good."
    return True, "gpiozero is ready. Time to build circuits!"


def check_led_on(r):
    if r.blinks >= 3 or _code(r).count(".on()") >= 3:
        return True, "On, off, on, off, on, off. You're controlling real electricity!"
    return False, "Switch the LED on 3 separate times, with sleep(1) between each change."


def check_blink(r):
    code = _code(r)
    if "for " not in code:
        return False, "Use a for loop (for i in range(10):) instead of while True."
    if "done" not in _out(r):
        return False, 'Print "Done!" after the loop finishes (not indented).'
    if r.blinks < 10 and "range(10)" not in code:
        return False, "Make the LED blink exactly 10 times."
    return True, "10 blinks and done. Loops plus hardware!"


def check_sos(r):
    code = _code(r)
    if r.blinks >= 9 or (code.count("letter_s()") >= 3 and code.count("letter_o()") >= 2):
        return True, "... --- ... You're sending Morse code!"
    return False, "Call letter_s(), then letter_o(), then letter_s() to flash S-O-S."


def check_fade(r):
    code = _code(r)
    if "PWMLED" not in code:
        return False, "Use PWMLED so you can change the brightness."
    if code.count("for ") < 2:
        return False, "Add a second for loop that fades the LED out."
    if not r.ok:
        return False, "Run your code and watch the LED fade in and out."
    return True, "Smooth! You're using PWM like a pro."


def check_pir(r):
    if "MotionSensor" not in _code(r):
        return False, "Create the sensor with pir = MotionSensor(4)"
    if not re.search(r"motion\D*3", r.output, re.IGNORECASE):
        return False, "Use a for loop so it detects motion 3 times: Motion 1, Motion 2, Motion 3."
    return True, "Your Pi can sense movement now!"


def check_visitors(r):
    if "visitors" not in _code(r):
        return False, "Make a variable called visitors to count with."
    if not re.search(r"visitor\D*\d", r.output, re.IGNORECASE):
        return False, "Each time someone moves, print Visitor number 1, Visitor number 2..."
    return True, "Your smart doorbell is counting visitors!"


def check_alarm(r):
    code = _code(r)
    if "intruder" not in _out(r):
        return False, "Trigger the sensor so your alarm goes off."
    if not re.search(r"def\s+alarm\s*\(", code):
        return False, "Keep your alarm() function."
    if r.blinks < 5 and "blink(" not in code and code.count("for ") < 2:
        return False, "Make the LED flash 10 times quickly inside alarm()."
    return True, "Burglar alarm complete! You've built a real gadget."


# ---------------------------------------------------------------------------
# The lessons
# ---------------------------------------------------------------------------

LESSONS = [
    # ------------------------------------------------------------------ 1
    dict(
        id="hello",
        chapter="Python Basics",
        title="Hello, World!",
        body="""
            Welcome, coder! A **program** is a list of instructions for a computer.
            Today you'll write your own in a language called **Python**. It's used
            by NASA, YouTube and Minecraft modders, and by you from now on!

            ## Your first instruction
            The `print()` command shows a message on the screen. Whatever you put
            inside the brackets, in quote marks, gets printed:

            ```
            print("Hello, World!")
            ```

            This code is already in the **code box** on the right. Press the green
            **▶ Run** button (or the **F5** key) and look at the **Output** box below it.

            ## Rules Python cares about
            - Text must go inside quote marks: `"like this"`
            - Brackets come in pairs: `(` and `)`
            - Python reads your code from **top to bottom**, one line at a time

            > **Tip:** Made a mistake? No problem! Python tells you what went wrong and
            > the line turns red. Fix it and run again. Real programmers make
            > mistakes all day long.
        """,
        code='print("Hello, World!")\n',
        task="""
            Change the message so it says hello to **you**, for example
            `print("Hello, Sam!")`. Then add a **second** `print()` line that tells
            the computer your favourite food.
        """,
        hint='Each print() goes on its own line:\n\nprint("Hello, Sam!")\nprint("My favourite food is pizza")',
        solution='print("Hello, Sam!")\nprint("My favourite food is pizza")\n',
        check=check_hello,
    ),
    # ------------------------------------------------------------------ 2
    dict(
        id="maths",
        chapter="Python Basics",
        title="Python is a Calculator",
        body="""
            Computers are very fast at maths. Python uses these symbols:

            - `+` add          `-` subtract
            - `*` multiply (a star, not an x)
            - `/` divide
            - `**` power, so `2 ** 3` is 2 × 2 × 2
            - `%` remainder, so `7 % 2` is 1

            ```
            print(2 + 3)
            print(6 * 7)
            print(20 / 4)
            print(2 ** 10)
            ```

            ## Numbers vs text
            `print(2 + 3)` shows `5`, but `print("2 + 3")` shows `2 + 3`.
            Quote marks mean *"this is text, don't calculate it"*.

            ## Brackets go first
            Just like in maths class: `(2 + 3) * 4` is 20, but `2 + 3 * 4` is 14.

            > **Tip:** Dividing with `/` always gives a decimal answer, so `20 / 4` is `5.0`.
        """,
        code=(
            "print(2 + 3)\n"
            "print(10 - 4)\n"
            "print(6 * 7)\n"
            "print(20 / 4)\n"
            "print(2 ** 10)\n"
            "\n"
            "# Quotes mean text, so this is NOT calculated:\n"
            'print("2 + 3")\n'
        ),
        task="""
            How many **seconds** are there in one day? There are 60 seconds in a
            minute, 60 minutes in an hour and 24 hours in a day. Make Python
            work it out with a single `print()`.
        """,
        hint="Multiply all three numbers together inside print():\n\nprint(60 * 60 * 24)",
        solution="print(60 * 60 * 24)\n",
        check=check_maths,
    ),
    # ------------------------------------------------------------------ 3
    dict(
        id="variables",
        chapter="Python Basics",
        title="Variables: Labelled Boxes",
        body="""
            A **variable** is like a box with a label on it. You put a value inside,
            and later you can use the label to get it back.

            ```
            name = "Ada"
            age = 12
            print(name)
            print(age)
            ```

            The `=` sign means *"put this value into the box"*. It does **not**
            mean "equals" like in maths.

            ## Changing what's in the box
            ```
            score = 10
            score = score + 5
            print("Score:", score)
            ```
            Commas in `print()` let you print several things at once, with spaces between them.

            ## Naming rules
            - Use letters, numbers and `_`, like `high_score`
            - No spaces, and you can't start with a number
            - Capitals matter! `Age` and `age` are different boxes
        """,
        code=(
            'name = "Ada"\n'
            "age = 12\n"
            'print(name, "is", age, "years old")\n'
            "\n"
            "score = 10\n"
            "score = score + 5\n"
            'print("Score:", score)\n'
        ),
        task="""
            A pizza has 8 slices and 4 friends share it. Make a variable `slices`
            holding 8 and a variable `friends` holding 4. Then make a variable
            `each` that works out how many slices each friend gets, and print it.
        """,
        hint="Divide one variable by the other:\n\neach = slices / friends\nprint(\"Each friend gets\", each)",
        solution=(
            "slices = 8\n"
            "friends = 4\n"
            "each = slices / friends\n"
            'print("Each friend gets", each, "slices")\n'
        ),
        check=check_variables,
    ),
    # ------------------------------------------------------------------ 4
    dict(
        id="types",
        chapter="Python Basics",
        title="Types of Data",
        body="""
            Every value in Python has a **type**. These are the four you'll use most:

            - `int` is a whole number: `7`, `-3`, `2024`
            - `float` is a decimal number: `3.14`, `0.5`
            - `str` is text (a "string" of letters): `"hello"`, `"42"`
            - `bool` is either `True` or `False`

            The `type()` command tells you what type something is:
            ```
            print(type(7))
            print(type(3.14))
            print(type("hello"))
            print(type(10 > 3))
            ```

            ## Why does it matter?
            `5 + 5` is `10`, but `"5" + "5"` is `"55"`, because text gets *joined*!
            You can convert between types:

            - `int("5")` turns text into a whole number
            - `float("2.5")` turns text into a decimal
            - `str(5)` turns a number into text
        """,
        code=(
            "print(type(7))\n"
            "print(type(3.14))\n"
            'print(type("hello"))\n'
            "print(type(True))\n"
            "\n"
            "print(5 + 5)\n"
            'print("5" + "5")\n'
        ),
        task="""
            Print the type of `"42"` (with quotes) and the type of `42` (without).
            Then use `int()` to turn the text `"42"` into a number and print it **plus 8**.
            You should see `50`.
        """,
        hint='print(type("42"))\nprint(type(42))\nprint(int("42") + 8)',
        solution='print(type("42"))\nprint(type(42))\nprint(int("42") + 8)\n',
        check=check_types,
    ),
    # ------------------------------------------------------------------ 5
    dict(
        id="strings",
        chapter="Python Basics",
        title="Playing with Text",
        body="""
            Text in Python is called a **string**. Here are some fun things you can do with it:

            ```
            first = "Ada"
            last = "Lovelace"
            full = first + " " + last     # join with +
            print(full)
            print(full.upper())           # CAPITALS
            print("Ha" * 5)               # repeat
            print(len(full))              # how many letters?
            ```

            ## f-strings: the easy way to mix text and variables
            Put an `f` before the quote mark, then put variables inside `{ }`:
            ```
            age = 12
            print(f"{first} is {age} years old")
            ```

            > **Watch out:** `"Age: " + 12` causes an error, because Python won't
            > join text and a number with `+`. Use an f-string or `str(12)` instead.

            Anything after a `#` is a **comment**. Python ignores it, so it's
            a note for humans.
        """,
        code=(
            'first = "Ada"\n'
            'last = "Lovelace"\n'
            'full = first + " " + last\n'
            "print(full)\n"
            "print(full.upper())\n"
            'print("Ha" * 5)\n'
            "print(len(full))\n"
            "\n"
            "age = 12\n"
            'print(f"{first} is {age} years old")\n'
        ),
        task="""
            Make variables for your `name` and your favourite `hobby`. Use an
            f-string to print a sentence like `My name is Sam and I love football!`
            Then print your name in CAPITAL letters.
        """,
        hint='name = "Sam"\nhobby = "football"\nprint(f"My name is {name} and I love {hobby}!")\nprint(name.upper())',
        solution=(
            'name = "Sam"\n'
            'hobby = "football"\n'
            'print(f"My name is {name} and I love {hobby}!")\n'
            "print(name.upper())\n"
        ),
        check=check_strings,
    ),
    # ------------------------------------------------------------------ 6
    dict(
        id="input",
        chapter="Python Basics",
        title="Talking to the Computer",
        body="""
            Programs are more fun when they talk with you! `input()` asks a question
            and **waits** for an answer.

            ```
            name = input("What is your name? ")
            print("Nice to meet you,", name)
            ```

            When your program asks a question, the **answer box** at the bottom of
            the Output panel lights up. Type your answer and press **Enter**.

            ## Numbers from input
            `input()` always gives you **text**, even if you type a number. To do
            maths with it, wrap it in `int()`:
            ```
            age = int(input("How old are you? "))
            print("In 10 years you will be", age + 10)
            ```
        """,
        code=(
            'name = input("What is your name? ")\n'
            'print("Nice to meet you,", name)\n'
            "\n"
            'age = int(input("How old are you? "))\n'
            'print("In 10 years you will be", age + 10)\n'
        ),
        task="""
            Make a mini calculator. Ask for **two numbers**, add them together and
            print the answer, like `The total is 12`.
        """,
        hint='a = int(input("First number? "))\nb = int(input("Second number? "))\nprint("The total is", a + b)',
        solution=(
            'a = int(input("First number? "))\n'
            'b = int(input("Second number? "))\n'
            'print("The total is", a + b)\n'
        ),
        check=check_input,
    ),
    # ------------------------------------------------------------------ 7
    dict(
        id="if",
        chapter="Python Basics",
        title="Making Decisions: if / else",
        body="""
            Programs can make choices with `if`:

            ```
            temperature = int(input("What's the temperature? "))

            if temperature > 25:
                print("It's hot! Wear a hat.")
            else:
                print("Not too hot today.")
            ```

            - The `if` line ends with a **colon** `:`
            - The lines that belong to it are **indented** (pushed right by 4 spaces). The editor does this for you after a colon!
            - `else:` runs when the `if` was **not** true

            ## Comparing things
            - `==` equal to          `!=` not equal to
            - `>` bigger than        `<` smaller than
            - `>=` bigger or equal   `<=` smaller or equal

            ## More choices with elif
            ```
            if score >= 90:
                print("Gold medal!")
            elif score >= 50:
                print("Silver medal!")
            else:
                print("Keep practising!")
            ```

            > **Remember:** one `=` puts a value in a box. Two `==` compares two things.
        """,
        code=(
            'temperature = int(input("What\'s the temperature? "))\n'
            "\n"
            "if temperature > 25:\n"
            '    print("It\'s hot! Wear a hat.")\n'
            "else:\n"
            '    print("Not too hot today.")\n'
        ),
        task="""
            Make a **guess-the-number** game. Set `secret = 7`, then ask the player
            for a guess. Print `You got it!` if they're right, `Too low!` if the
            guess is smaller and `Too high!` if it's bigger. Use `if`, `elif` and `else`.
        """,
        hint=(
            "secret = 7\n"
            'guess = int(input("Guess my number: "))\n'
            "if guess == secret:\n"
            "    ...\n"
            "elif guess < secret:\n"
            "    ...\n"
            "else:\n"
            "    ..."
        ),
        solution=(
            "secret = 7\n"
            'guess = int(input("Guess my number (1-10): "))\n'
            "\n"
            "if guess == secret:\n"
            '    print("You got it!")\n'
            "elif guess < secret:\n"
            '    print("Too low!")\n'
            "else:\n"
            '    print("Too high!")\n'
        ),
        check=check_if,
    ),
    # ------------------------------------------------------------------ 8
    dict(
        id="for",
        chapter="Python Basics",
        title="Loops: Repeat with for",
        body="""
            A **loop** repeats code so you don't have to write it again and again.

            ```
            for i in range(5):
                print("Hello number", i)
            ```

            - `range(5)` gives the numbers 0, 1, 2, 3, 4. That's five numbers, **starting at 0**
            - `range(1, 11)` gives 1 up to 10 (it stops *before* 11)
            - The indented lines are the ones that get repeated
            - `i` is a variable that holds the current number each time round

            ```
            for i in range(1, 4):
                print(i, "x 2 =", i * 2)
            ```

            You can loop over the letters in text too:
            ```
            for letter in "PYTHON":
                print(letter)
            ```
        """,
        code=(
            "for i in range(5):\n"
            '    print("Hello number", i)\n'
            "\n"
            'for letter in "PYTHON":\n'
            "    print(letter)\n"
        ),
        task="""
            Print the whole **5 times table**, from `5 x 1 = 5` all the way to
            `5 x 10 = 50`, using a `for` loop.
        """,
        hint='Loop from 1 to 10 and print the sum each time:\n\nfor i in range(1, 11):\n    print(5, "x", i, "=", 5 * i)',
        solution='for i in range(1, 11):\n    print(5, "x", i, "=", 5 * i)\n',
        check=check_for,
    ),
    # ------------------------------------------------------------------ 9
    dict(
        id="while",
        chapter="Python Basics",
        title="While Loops & Time",
        body="""
            A `while` loop keeps going **while** something is true:

            ```
            import time

            count = 5
            while count > 0:
                print(count)
                time.sleep(1)
                count = count - 1

            print("Blast off!")
            ```

            - `import time` loads Python's **time** toolbox (called a *module*)
            - `time.sleep(1)` pauses for 1 second. You can use `0.5` for half a second
            - `count = count - 1` makes the number smaller each time, so the loop ends

            ## Loops that never end
            `while True:` repeats **forever**. That sounds silly, but LED and sensor
            programs use it all the time! To end a forever loop, press the
            red **■ Stop** button (or the **Esc** key).
        """,
        code=(
            "import time\n"
            "\n"
            "count = 5\n"
            "while count > 0:\n"
            "    print(count)\n"
            "    time.sleep(1)\n"
            "    count = count - 1\n"
            "\n"
            'print("Blast off!")\n'
        ),
        task="""
            Make the rocket countdown start at **10** and print `Blast off!` at the end.
            Bonus: make it count down twice as fast.
        """,
        hint="Change the starting value of count to 10.\nFor double speed use time.sleep(0.5)",
        solution=(
            "import time\n"
            "\n"
            "count = 10\n"
            "while count > 0:\n"
            "    print(count)\n"
            "    time.sleep(0.5)\n"
            "    count = count - 1\n"
            "\n"
            'print("Blast off!")\n'
        ),
        check=check_while,
    ),
    # ------------------------------------------------------------------ 10
    dict(
        id="lists",
        chapter="Python Basics",
        title="Lists: Many Things in One",
        body="""
            A **list** keeps lots of values together, in order, inside square brackets:

            ```
            snacks = ["apple", "crisps", "chocolate"]
            print(snacks[0])        # the FIRST item
            print(len(snacks))      # how many items
            snacks.append("banana") # add to the end
            ```

            > **Important:** counting starts at **0**! `snacks[0]` is the first item,
            > `snacks[1]` is the second, and so on.

            ## Loop through a list
            A `for` loop can visit every item in turn:
            ```
            for snack in snacks:
                print("Yum,", snack)
            ```
        """,
        code=(
            'snacks = ["apple", "crisps", "chocolate"]\n'
            "print(snacks)\n"
            'print("The first snack is", snacks[0])\n'
            'print("I have", len(snacks), "snacks")\n'
            "\n"
            'snacks.append("banana")\n'
            "\n"
            "for snack in snacks:\n"
            '    print("Yum,", snack)\n'
        ),
        task="""
            Make a list called `team` with the names of **3 friends**. Add your own
            name with `.append()`. Then use a `for` loop to print
            `Welcome, NAME!` for everyone on the team.
        """,
        hint='team = ["Ada", "Alan", "Grace"]\nteam.append("Sam")\nfor person in team:\n    print(f"Welcome, {person}!")',
        solution=(
            'team = ["Ada", "Alan", "Grace"]\n'
            'team.append("Sam")\n'
            "\n"
            "for person in team:\n"
            '    print(f"Welcome, {person}!")\n'
        ),
        check=check_lists,
    ),
    # ------------------------------------------------------------------ 11
    dict(
        id="functions",
        chapter="Python Basics",
        title="Functions: Your Own Commands",
        body="""
            A **function** is a set of instructions with a name. You make it once
            with `def`, then **call** it whenever you like.

            ```
            def cheer():
                print("Hip hip...")
                print("HOORAY!")

            cheer()
            cheer()
            ```

            - `def` means *define*: "here's a new command"
            - The name is followed by `()` and a colon `:`
            - The indented lines are what the function does
            - Nothing happens until you **call** it: `cheer()`

            ## Giving a function information
            Values inside the brackets are called **parameters**:
            ```
            def greet(name):
                print("Hello,", name, "welcome to the workshop!")

            greet("Ada")
            greet("Alan")
            ```
            You've been using functions all along: `print()`, `input()` and `len()` are functions!
        """,
        code=(
            "def cheer():\n"
            '    print("Hip hip...")\n'
            '    print("HOORAY!")\n'
            "\n"
            "cheer()\n"
            "cheer()\n"
            "\n"
            "def greet(name):\n"
            '    print("Hello,", name, "welcome to the workshop!")\n'
            "\n"
            'greet("Ada")\n'
            'greet("Alan")\n'
        ),
        task="""
            Write a function `birthday(name, age)` that prints something like
            `Happy birthday Sam! You are 13 today!`. Call it **twice** with
            different names and ages.
        """,
        hint='def birthday(name, age):\n    print(f"Happy birthday {name}! You are {age} today!")\n\nbirthday("Sam", 13)',
        solution=(
            "def birthday(name, age):\n"
            '    print(f"Happy birthday {name}! You are {age} today!")\n'
            "\n"
            'birthday("Sam", 13)\n'
            'birthday("Priya", 12)\n'
        ),
        check=check_functions,
    ),
    # ------------------------------------------------------------------ 12
    dict(
        id="return",
        chapter="Python Basics",
        title="Functions that Give Back",
        body="""
            Some functions work something out and **give the answer back** with `return`:

            ```
            def add(a, b):
                return a + b

            total = add(3, 4)
            print("3 + 4 =", total)
            ```

            `return` sends a value back to wherever the function was called.
            You can store it in a variable or print it straight away:
            ```
            print(add(10, 20))
            ```

            > **print vs return:** `print` shows something on the screen.
            > `return` hands a value back to your program so it can use it.
        """,
        code=(
            "def add(a, b):\n"
            "    return a + b\n"
            "\n"
            "total = add(3, 4)\n"
            'print("3 + 4 =", total)\n'
            'print("10 + 20 =", add(10, 20))\n'
        ),
        task="""
            Write a function `area(width, height)` that **returns** the area of a
            rectangle (width × height). Print `area(5, 3)` and `area(7, 8)`.
            You should see 15 and 56.
        """,
        hint="def area(width, height):\n    return width * height\n\nprint(area(5, 3))",
        solution=(
            "def area(width, height):\n"
            "    return width * height\n"
            "\n"
            "print(area(5, 3))\n"
            "print(area(7, 8))\n"
        ),
        check=check_return,
    ),
    # ------------------------------------------------------------------ 13
    dict(
        id="bugs",
        chapter="Python Basics",
        title="Bug Hunt!",
        body="""
            Mistakes in code are called **bugs**, and fixing them is called
            **debugging**. Error messages aren't failures. They're **clues**!

            ## Errors you'll meet
            - **SyntaxError**: Python can't read the line, like a spelling or grammar mistake. Look for missing quotes `"`, brackets `)` or colons `:`
            - **NameError**: Python doesn't know a name. Check the spelling, because capitals matter!
            - **TypeError**: mixing things that don't go together, like text + number
            - **IndentationError**: the spaces at the start of the lines don't line up

            ## How to debug
            - **Read** the red error message. Which line? What's wrong?
            - **Look** at that line, and the one just above it
            - **Fix one thing**, then run again
        """,
        code=(
            "# This program has 3 bugs! Can you find and fix them?\n"
            "# Run it, read the error, fix ONE bug, then run again.\n"
            "\n"
            "def show_score(player, score)\n"
            '    print(player, "scored", score, "points")\n'
            "\n"
            'show_score("Ada", 10)\n'
            'show_score("Alan, 7)\n'
            'Show_score("Grace", 12)\n'
        ),
        task="""
            Fix all **3 bugs** so the program prints the scores for Ada, Alan and Grace.
        """,
        hint="Bug 1: a line starting with def must end with a colon.\nBug 2: count the quote marks around Alan.\nBug 3: capitals matter in names!",
        solution=(
            "def show_score(player, score):\n"
            '    print(player, "scored", score, "points")\n'
            "\n"
            'show_score("Ada", 10)\n'
            'show_score("Alan", 7)\n'
            'show_score("Grace", 12)\n'
        ),
        check=check_bugs,
    ),
    # ------------------------------------------------------------------ 14
    dict(
        id="gpio",
        chapter="Raspberry Pi Hardware",
        title="Meet the GPIO Pins",
        hardware=True,
        body="""
            Your Raspberry Pi has a row of **40 metal pins** along one edge. This is the
            **GPIO header** (General Purpose Input/Output). With Python you can:

            - **Output:** switch a pin **on or off** to control LEDs, buzzers and motors
            - **Input:** **read** a pin to find out what a button or sensor is doing

            ## Two kinds of pin numbers
            - **Physical number:** count along the header, 1 to 40 (see the map below)
            - **GPIO number:** the name Python uses. *GPIO17* is physical pin 11

            In code we always use the **GPIO number**, like `LED(17)`.

            ## Special pins
            - **3V3** and **5V** supply power (orange and red on the map)
            - **GND** (ground) is the "minus" side. Every circuit needs a GND wire

            > **Safety first:** Never connect a 5V or 3V3 pin straight to GND or to a
            > GPIO pin. Always use a resistor with an LED. Ask your instructor to
            > check your wiring before you run your code.

            ## gpiozero
            `gpiozero` is a Python toolbox that makes controlling pins easy. The code
            on the right checks it's ready to go.

            > **No Raspberry Pi?** The app runs in **Simulator** mode and the virtual
            > board below shows what your pins are doing.
        """,
        code=(
            "from gpiozero import LED\n"
            "\n"
            'print("gpiozero is ready!")\n'
            "\n"
            "led = LED(17)\n"
            'print("Created an LED on", led.pin)\n'
            "led.close()\n"
            "\n"
            'print("All good. Let\'s build something!")\n'
        ),
        task="""
            Press **▶ Run**. If you see `All good`, your Pi is ready for real hardware!
            Then find **pin 11 (GPIO17)** and a **GND** pin on the map below.
        """,
        hint="Just press Run (or F5). If you get an error, ask your instructor.",
        solution=None,
        check=check_gpio_ready,
        wiring=[
            (1, "Pin 1 = 3V3 power", "#F59E0B"),
            (2, "Pin 2 = 5V power", POWER),
            (6, "Pin 6 = GND (ground)", GROUND),
            (11, "Pin 11 = GPIO17. We'll plug the LED in here", SIGNAL),
        ],
    ),
    # ------------------------------------------------------------------ 15
    dict(
        id="led",
        chapter="Raspberry Pi Hardware",
        title="Light Up an LED",
        hardware=True,
        body="""
            Time to control something real!

            ## You need
            - 1 × LED (any colour)
            - 1 × resistor (220Ω to 330Ω)
            - 2 × jumper wires and a breadboard

            ## Build the circuit
            An LED only works **one way round**. The **long leg** is **+** and the short leg is **−**.

            - **Pin 11 (GPIO17)** → resistor → LED **long leg**
            - LED **short leg** → **pin 9 (GND)**

            The resistor protects the LED, and your Pi, from too much electricity.

            ## The code, line by line
            - `from gpiozero import LED` gets the LED tool from the toolbox
            - `led = LED(17)` means "there's an LED connected to GPIO17"
            - `led.on()` and `led.off()` switch it on and off
            - `sleep(2)` waits 2 seconds

            > **Note:** when your program ends, gpiozero switches the LED off automatically.
        """,
        code=(
            "from gpiozero import LED\n"
            "from time import sleep\n"
            "\n"
            "led = LED(17)\n"
            "\n"
            "led.on()\n"
            'print("LED is ON")\n'
            "sleep(2)\n"
            "\n"
            "led.off()\n"
            'print("LED is OFF")\n'
        ),
        task="""
            Make the LED switch on **3 separate times** (on, off, on, off, on, off)
            with a 1 second pause after each change.
        """,
        hint="Copy the on / sleep / off / sleep lines and paste them so they appear 3 times.\nRemember a sleep(1) after led.off() too!",
        solution=(
            "from gpiozero import LED\n"
            "from time import sleep\n"
            "\n"
            "led = LED(17)\n"
            "\n"
            "led.on()\n"
            "sleep(1)\n"
            "led.off()\n"
            "sleep(1)\n"
            "\n"
            "led.on()\n"
            "sleep(1)\n"
            "led.off()\n"
            "sleep(1)\n"
            "\n"
            "led.on()\n"
            "sleep(1)\n"
            "led.off()\n"
        ),
        check=check_led_on,
        wiring=[
            (11, "Pin 11 · GPIO17 → resistor → LED long leg (+)", SIGNAL),
            (9, "Pin 9 · GND → LED short leg (−)", GROUND),
        ],
    ),
    # ------------------------------------------------------------------ 16
    dict(
        id="blink",
        chapter="Raspberry Pi Hardware",
        title="Blink!",
        hardware=True,
        body="""
            On, wait, off, wait, again and again. Put the LED inside a **loop** and it blinks!

            `while True:` repeats **forever**, so this LED will blink until you press
            **■ Stop** (or **Esc**).

            - Change the `sleep()` numbers to change the speed
            - `0.1` is super fast and `2` is slow
            - On and off times don't have to match. Try `led.on()` for 0.1 and `led.off()` for 1

            Same circuit as before: **GPIO17 → resistor → LED → GND**.

            > **Shortcut:** gpiozero can also blink by itself:
            > `led.blink(on_time=0.5, off_time=0.5)`. It keeps blinking in the
            > background while your program does other things.
        """,
        code=(
            "from gpiozero import LED\n"
            "from time import sleep\n"
            "\n"
            "led = LED(17)\n"
            "\n"
            "while True:\n"
            "    led.on()\n"
            "    sleep(0.5)\n"
            "    led.off()\n"
            "    sleep(0.5)\n"
        ),
        task="""
            Instead of blinking forever, use a `for` loop to blink **exactly 10
            times**, then print `Done!`
        """,
        hint="Replace  while True:  with  for i in range(10):\nThen add print(\"Done!\") at the end, NOT indented.",
        solution=(
            "from gpiozero import LED\n"
            "from time import sleep\n"
            "\n"
            "led = LED(17)\n"
            "\n"
            "for i in range(10):\n"
            "    led.on()\n"
            "    sleep(0.3)\n"
            "    led.off()\n"
            "    sleep(0.3)\n"
            "\n"
            'print("Done!")\n'
        ),
        check=check_blink,
        wiring=[
            (11, "Pin 11 · GPIO17 → resistor → LED long leg (+)", SIGNAL),
            (9, "Pin 9 · GND → LED short leg (−)", GROUND),
        ],
    ),
    # ------------------------------------------------------------------ 17
    dict(
        id="sos",
        chapter="Raspberry Pi Hardware",
        title="SOS in Morse Code",
        hardware=True,
        body="""
            **Morse code** sends letters as short flashes (**dots**) and long flashes
            (**dashes**). The famous emergency signal **SOS** is:

            ```
            S = dot dot dot      O = dash dash dash      S = dot dot dot
            ```

            Writing `led.on()`, `sleep()` and `led.off()` over and over gets messy. Let's
            use **functions** to give each flash pattern a name, then reuse it!

            - `flash(seconds)` lights the LED for that long
            - `dot()` is a short flash and `dash()` is a long one
            - `letter_s()` flashes 3 dots, and `letter_o()` should flash 3 dashes

            Functions can call other functions. That's how big programs are built
            from small pieces.
        """,
        code=(
            "from gpiozero import LED\n"
            "from time import sleep\n"
            "\n"
            "led = LED(17)\n"
            "\n"
            "def flash(seconds):\n"
            "    led.on()\n"
            "    sleep(seconds)\n"
            "    led.off()\n"
            "    sleep(0.2)\n"
            "\n"
            "def dot():\n"
            "    flash(0.2)\n"
            "\n"
            "def dash():\n"
            "    flash(0.6)\n"
            "\n"
            "def letter_s():\n"
            "    for i in range(3):\n"
            "        dot()\n"
            "\n"
            "def letter_o():\n"
            "    for i in range(3):\n"
            "        dash()\n"
            "\n"
            'print("S")\n'
            "letter_s()\n"
        ),
        task="""
            Finish the signal so the LED flashes **S, O, S**, and print each letter
            as it flashes. Bonus: repeat the whole SOS 3 times with a 1 second pause between.
        """,
        hint='After letter_s() add:\n\nprint("O")\nletter_o()\nprint("S")\nletter_s()',
        solution=(
            "from gpiozero import LED\n"
            "from time import sleep\n"
            "\n"
            "led = LED(17)\n"
            "\n"
            "def flash(seconds):\n"
            "    led.on()\n"
            "    sleep(seconds)\n"
            "    led.off()\n"
            "    sleep(0.2)\n"
            "\n"
            "def dot():\n"
            "    flash(0.2)\n"
            "\n"
            "def dash():\n"
            "    flash(0.6)\n"
            "\n"
            "def letter_s():\n"
            "    for i in range(3):\n"
            "        dot()\n"
            "\n"
            "def letter_o():\n"
            "    for i in range(3):\n"
            "        dash()\n"
            "\n"
            "for repeat in range(3):\n"
            '    print("S")\n'
            "    letter_s()\n"
            '    print("O")\n'
            "    letter_o()\n"
            '    print("S")\n'
            "    letter_s()\n"
            "    sleep(1)\n"
        ),
        check=check_sos,
        wiring=[
            (11, "Pin 11 · GPIO17 → resistor → LED long leg (+)", SIGNAL),
            (9, "Pin 9 · GND → LED short leg (−)", GROUND),
        ],
    ),
    # ------------------------------------------------------------------ 18
    dict(
        id="pwm",
        chapter="Raspberry Pi Hardware",
        title="Dimmer Switch (PWM)",
        hardware=True,
        body="""
            A pin can only be **on or off**, so how do we make an LED *dim*? We switch
            it on and off **hundreds of times a second**! Your eyes can't see the
            flicker, so the LED just looks dimmer. This trick is called **PWM**.

            gpiozero does it for you with `PWMLED`. Set `led.value` to a number
            from **0** (off) to **1** (full brightness):

            ```
            led.value = 0.1    # very dim
            led.value = 0.5    # half brightness
            led.value = 1      # full power
            ```

            A `for` loop can change the brightness a little at a time to make a
            smooth **fade**. `step / 100` turns 0 to 100 into 0.0 to 1.0.

            > **Bonus:** `led.pulse()` makes the LED "breathe" in and out by itself.

            Same circuit as before: **GPIO17 → resistor → LED → GND**.
        """,
        code=(
            "from gpiozero import PWMLED\n"
            "from time import sleep\n"
            "\n"
            "led = PWMLED(17)\n"
            "\n"
            "led.value = 0.1\n"
            "sleep(1)\n"
            "led.value = 0.5\n"
            "sleep(1)\n"
            "led.value = 1\n"
            "sleep(1)\n"
            "\n"
            "# Fade in smoothly\n"
            "for step in range(101):\n"
            "    led.value = step / 100\n"
            "    sleep(0.02)\n"
        ),
        task="""
            After the fade-in, add another `for` loop that fades the LED **out**
            smoothly, from full brightness back to off.
        """,
        hint="range can count backwards!\n\nfor step in range(100, -1, -1):\n    led.value = step / 100\n    sleep(0.02)",
        solution=(
            "from gpiozero import PWMLED\n"
            "from time import sleep\n"
            "\n"
            "led = PWMLED(17)\n"
            "\n"
            "# Fade in smoothly\n"
            "for step in range(101):\n"
            "    led.value = step / 100\n"
            "    sleep(0.02)\n"
            "\n"
            "# Fade out smoothly\n"
            "for step in range(100, -1, -1):\n"
            "    led.value = step / 100\n"
            "    sleep(0.02)\n"
        ),
        check=check_fade,
        wiring=[
            (11, "Pin 11 · GPIO17 → resistor → LED long leg (+)", SIGNAL),
            (9, "Pin 9 · GND → LED short leg (−)", GROUND),
        ],
    ),
    # ------------------------------------------------------------------ 19
    dict(
        id="pir",
        chapter="Raspberry Pi Hardware",
        title="Meet the Motion Sensor",
        hardware=True,
        body="""
            A **PIR sensor** (Passive InfraRed) can sense the warmth of people and
            animals **moving** in front of it. When it sees movement, its OUT pin
            switches **on**.

            ## Build the circuit
            - PIR **VCC** → **pin 2 (5V)**
            - PIR **OUT** → **pin 7 (GPIO4)**
            - PIR **GND** → **pin 6 (GND)**

            (Check the labels on your sensor. On most boards the pins are printed under the white dome.)

            > **PIR tips:** after you power it on, the sensor needs about **30 to 60
            > seconds to warm up**, and it may trigger by itself at first. The two
            > orange knobs change the sensitivity and how long it stays on.

            ## The code
            - `pir = MotionSensor(4)` means "a motion sensor is on GPIO4"
            - `pir.wait_for_motion()` **pauses** your program until something moves
            - `pir.wait_for_no_motion()` waits until everything is still again

            > **Simulator:** press **Wave at sensor** on the board below to pretend to move.
        """,
        code=(
            "from gpiozero import MotionSensor\n"
            "\n"
            "pir = MotionSensor(4)\n"
            "\n"
            'print("Keep still...")\n'
            "pir.wait_for_no_motion()\n"
            'print("Ready! Wave your hand in front of the sensor.")\n'
            "\n"
            "pir.wait_for_motion()\n"
            'print("Motion detected!")\n'
            "\n"
            "pir.wait_for_no_motion()\n"
            'print("Everything is still again.")\n'
        ),
        task="""
            Use a `for` loop to detect motion **3 times**, printing `Motion 1`,
            `Motion 2` and `Motion 3`.
        """,
        hint='for i in range(1, 4):\n    pir.wait_for_motion()\n    print("Motion", i)\n    pir.wait_for_no_motion()',
        solution=(
            "from gpiozero import MotionSensor\n"
            "\n"
            "pir = MotionSensor(4)\n"
            "\n"
            'print("Wave at the sensor 3 times!")\n'
            "\n"
            "for i in range(1, 4):\n"
            "    pir.wait_for_motion()\n"
            '    print("Motion", i)\n'
            "    pir.wait_for_no_motion()\n"
            "\n"
            'print("All done!")\n'
        ),
        check=check_pir,
        wiring=[
            (2, "Pin 2 · 5V → PIR VCC", POWER),
            (7, "Pin 7 · GPIO4 → PIR OUT", SENSOR),
            (6, "Pin 6 · GND → PIR GND", GROUND),
        ],
    ),
    # ------------------------------------------------------------------ 20
    dict(
        id="motion_light",
        chapter="Raspberry Pi Hardware",
        title="Motion-Activated Light",
        hardware=True,
        body="""
            Let's use the **LED and the sensor together**, like a real security light!

            Instead of waiting, we can tell gpiozero **what to do when something
            happens**. These are called **events**:

            ```
            pir.when_motion = intruder
            pir.when_no_motion = all_clear
            ```

            - There are **no brackets** after `intruder`. You're *handing over* the function for later, not running it now
            - `pause()` keeps your program running so it can react. Press **■ Stop** to end it

            ## Wiring: keep both circuits
            - LED: **GPIO17 (pin 11)** → resistor → LED → **GND (pin 9)**
            - PIR: **5V (pin 2)**, **OUT → GPIO4 (pin 7)**, **GND (pin 6)**
        """,
        code=(
            "from gpiozero import MotionSensor, LED\n"
            "from signal import pause\n"
            "\n"
            "pir = MotionSensor(4)\n"
            "led = LED(17)\n"
            "\n"
            "def intruder():\n"
            '    print("Movement! Light ON")\n'
            "    led.on()\n"
            "\n"
            "def all_clear():\n"
            '    print("All clear. Light OFF")\n'
            "    led.off()\n"
            "\n"
            "pir.when_motion = intruder\n"
            "pir.when_no_motion = all_clear\n"
            "\n"
            'print("Motion light is running. Press Stop to end.")\n'
            "pause()\n"
        ),
        task="""
            Make a **visitor counter** doorbell. Create `visitors = 0`, then use a
            `while True:` loop that waits for motion, adds 1 to `visitors`, prints
            `Visitor number 1`, `Visitor number 2` and so on, blinks the LED with
            `led.blink(0.1, 0.1, n=3)` and then waits for no motion.
        """,
        hint=(
            "visitors = 0\n"
            "while True:\n"
            "    pir.wait_for_motion()\n"
            "    visitors = visitors + 1\n"
            '    print("Visitor number", visitors)\n'
            "    led.blink(0.1, 0.1, n=3)\n"
            "    pir.wait_for_no_motion()"
        ),
        solution=(
            "from gpiozero import MotionSensor, LED\n"
            "\n"
            "pir = MotionSensor(4)\n"
            "led = LED(17)\n"
            "\n"
            "visitors = 0\n"
            'print("Doorbell ready!")\n'
            "\n"
            "while True:\n"
            "    pir.wait_for_motion()\n"
            "    visitors = visitors + 1\n"
            '    print("Visitor number", visitors)\n'
            "    led.blink(0.1, 0.1, n=3)\n"
            "    pir.wait_for_no_motion()\n"
        ),
        check=check_visitors,
        wiring=[
            (11, "Pin 11 · GPIO17 → resistor → LED long leg (+)", SIGNAL),
            (9, "Pin 9 · GND → LED short leg (−)", GROUND),
            (2, "Pin 2 · 5V → PIR VCC", POWER),
            (7, "Pin 7 · GPIO4 → PIR OUT", SENSOR),
            (6, "Pin 6 · GND → PIR GND", GROUND),
        ],
    ),
    # ------------------------------------------------------------------ 21
    dict(
        id="alarm",
        chapter="Raspberry Pi Hardware",
        title="Final Project: Burglar Alarm",
        hardware=True,
        body="""
            Time to put **everything** together: variables, loops, functions, `if`,
            an LED and a sensor. You're building a **burglar alarm**!

            ## How it works
            - A countdown gives you time to leave the room
            - The alarm waits for movement
            - When it sees an intruder, it prints the time and flashes the LED

            `strftime("%H:%M:%S")` gives the current time as text, like `14:05:33`.

            ## Make it your own
            - Got a **buzzer**? `from gpiozero import Buzzer` then `buzzer = Buzzer(22)` and `buzzer.beep()`
            - Got a **button**? `Button(2)` and `button.wait_for_press()` could switch the alarm off
            - Count intruders and print a report at the end

            > **Same wiring as the last lesson:** LED on GPIO17, PIR on GPIO4.
        """,
        code=(
            "from gpiozero import MotionSensor, LED\n"
            "from time import sleep, strftime\n"
            "\n"
            "pir = MotionSensor(4)\n"
            "led = LED(17)\n"
            "\n"
            "def countdown(seconds):\n"
            "    for s in range(seconds, 0, -1):\n"
            '        print("Alarm arming in", s)\n'
            "        sleep(1)\n"
            '    print("ALARM ARMED!")\n'
            "\n"
            "def alarm():\n"
            '    print("INTRUDER at", strftime("%H:%M:%S"))\n'
            "    # TODO: make the LED flash 10 times quickly here\n"
            "\n"
            "countdown(5)\n"
            "\n"
            "while True:\n"
            "    pir.wait_for_motion()\n"
            "    alarm()\n"
            "    pir.wait_for_no_motion()\n"
        ),
        task="""
            - **Step 1:** finish `alarm()` so the LED flashes **10 times** quickly
            - **Step 2:** count the intruders. After **3**, print `Too many intruders!` and end the loop with `break`
        """,
        hint=(
            "Flash with a loop inside alarm():\n"
            "    for i in range(10):\n"
            "        led.on()\n"
            "        sleep(0.1)\n"
            "        led.off()\n"
            "        sleep(0.1)\n"
            "\n"
            "Count with a variable before the loop: intruders = 0\n"
            "and inside it: intruders = intruders + 1\n"
            "then:  if intruders == 3:  print(...)  and  break"
        ),
        solution=(
            "from gpiozero import MotionSensor, LED\n"
            "from time import sleep, strftime\n"
            "\n"
            "pir = MotionSensor(4)\n"
            "led = LED(17)\n"
            "\n"
            "def countdown(seconds):\n"
            "    for s in range(seconds, 0, -1):\n"
            '        print("Alarm arming in", s)\n'
            "        sleep(1)\n"
            '    print("ALARM ARMED!")\n'
            "\n"
            "def alarm():\n"
            '    print("INTRUDER at", strftime("%H:%M:%S"))\n'
            "    for i in range(10):\n"
            "        led.on()\n"
            "        sleep(0.1)\n"
            "        led.off()\n"
            "        sleep(0.1)\n"
            "\n"
            "countdown(5)\n"
            "intruders = 0\n"
            "\n"
            "while True:\n"
            "    pir.wait_for_motion()\n"
            "    intruders = intruders + 1\n"
            "    alarm()\n"
            "    if intruders == 3:\n"
            '        print("Too many intruders!")\n'
            "        break\n"
            "    pir.wait_for_no_motion()\n"
        ),
        check=check_alarm,
        wiring=[
            (11, "Pin 11 · GPIO17 → resistor → LED long leg (+)", SIGNAL),
            (9, "Pin 9 · GND → LED short leg (−)", GROUND),
            (2, "Pin 2 · 5V → PIR VCC", POWER),
            (7, "Pin 7 · GPIO4 → PIR OUT", SENSOR),
            (6, "Pin 6 · GND → PIR GND", GROUND),
        ],
    ),
    # ------------------------------------------------------------------ 22
    dict(
        id="playground",
        chapter="Free Play",
        title="Your Playground",
        hardware=True,
        body="""
            You've finished the workshop. Amazing work! This page is yours: write
            **anything you like** and run it. Here are some ideas to try:

            ## Dice roller
            ```
            import random
            print("You rolled a", random.randint(1, 6))
            ```

            ## Traffic lights (3 LEDs on GPIO 17, 27 and 22)
            ```
            from gpiozero import TrafficLights
            from time import sleep
            lights = TrafficLights(17, 27, 22)
            lights.green.on()
            sleep(2)
            lights.amber.on()
            ```

            ## Button (between GPIO2 and GND)
            ```
            from gpiozero import Button
            button = Button(2)
            button.wait_for_press()
            print("Pressed!")
            ```

            > **Keep going at home:** Python is free! Try **Thonny** on the Raspberry Pi,
            > or search for *"gpiozero recipes"* for lots more projects.
        """,
        code=(
            "import random\n"
            "import time\n"
            "\n"
            'print("Rolling the dice...")\n'
            "time.sleep(1)\n"
            'print("You rolled a", random.randint(1, 6))\n'
        ),
        task="""
            Make anything you like! Change the dice into a **magic 8-ball** that
            answers questions, build a **quiz**, or invent your own gadget.
        """,
        hint='A magic 8-ball picks a random answer from a list:\n\nanswers = ["Yes!", "No way", "Ask again later"]\nquestion = input("Ask me a question: ")\nprint(random.choice(answers))',
        solution=None,
        check=None,
    ),
]
