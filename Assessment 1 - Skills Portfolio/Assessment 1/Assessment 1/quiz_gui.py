import tkinter as tk
from tkinter import ttk, messagebox
import random
import threading
import importlib
from pathlib import Path

mixer = None
PYGAME_AUDIO_AVAILABLE = False

try:  # pragma: no cover - optional dependency
    mixer = importlib.import_module("pygame.mixer")
    PYGAME_AUDIO_AVAILABLE = True
except ImportError:
    mixer = None

try:  # pragma: no cover - winsound is Windows-only
    import winsound

    WINSOUND_AVAILABLE = True
except ImportError:
    winsound = None
    WINSOUND_AVAILABLE = False

# --- basic settings for the quiz ---
TOTAL_QUESTIONS = 10

BG_COLOR = "#edf1f8"
CARD_BG = "#ffffff"
SHADOW_COLOR = "#dbe4f4"
ACCENT_COLOR = "#ccdbff"
BTN_COLOR = "#2574cf"
BTN_HOVER = "#005bb9"
BTN_TEXT = "white"
PROBLEM_COLOR = "#184173"
FONT = "Segoe UI"

# WAV placeholders – drop your own files into the assets/ directory
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ASSETS_DIR.mkdir(exist_ok=True)
SOUND_FILES = {
    "timer": ASSETS_DIR / "timer.wav",
    "check": ASSETS_DIR / "check.wav",
    "wrong": ASSETS_DIR / "wrong.wav",
    "button": ASSETS_DIR / "button.wav",
}

AUDIO_READY = False
_sound_cache = {}
_sound_lock = threading.Lock()


def init_audio():
    """Try to initialize the audio backend once."""
    global AUDIO_READY
    if AUDIO_READY or not PYGAME_AUDIO_AVAILABLE:
        return
    try:
        mixer.init()
        AUDIO_READY = True
    except Exception:
        AUDIO_READY = False


def play_sound(name):
    """Play a short UI sound if a WAV placeholder exists."""
    path = SOUND_FILES.get(name)
    if not path or not path.exists():
        return

    def _play_with_pygame():
        if not PYGAME_AUDIO_AVAILABLE:
            return
        if not AUDIO_READY:
            init_audio()
        if not AUDIO_READY:
            return
        try:
            with _sound_lock:
                sound = _sound_cache.get(name)
                if sound is None:
                    sound = mixer.Sound(str(path))
                    _sound_cache[name] = sound
        except Exception:
            return
        try:
            channel = mixer.find_channel()
            if channel:
                channel.play(sound)
            else:
                sound.play()
        except Exception:
            pass

    def _play_with_winsound():
        if not WINSOUND_AVAILABLE:
            return
        try:
            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except RuntimeError:
            pass

    if PYGAME_AUDIO_AVAILABLE:
        threading.Thread(target=_play_with_pygame, daemon=True).start()
    elif WINSOUND_AVAILABLE:
        threading.Thread(target=_play_with_winsound, daemon=True).start()


def init_styles():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "Quiz.Horizontal.TProgressbar",
        troughcolor=CARD_BG,
        background=BTN_COLOR,
        bordercolor=CARD_BG,
        lightcolor=BTN_COLOR,
        darkcolor=BTN_COLOR,
        thickness=12,
    )

# --- create the main window once and reuse it ---
root = tk.Tk()
root.title("Arithmetic Quiz")

# Set a more universally fitting geometry and minsize to help with sizing and fitting
WINDOW_WIDTH, WINDOW_HEIGHT = 600, 540
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
root.maxsize(WINDOW_WIDTH, WINDOW_HEIGHT)
root.configure(bg=BG_COLOR)
root.resizable(False, False)

content_frame = tk.Frame(root, bg=BG_COLOR)
content_frame.pack(fill="both", expand=True)

init_styles()
init_audio()

# --- variables that change while the quiz runs ---
score = 0
question_index = 0
current_answer = 0
attempts_left = 2
digits_setting = 1

answer_entry = None
feedback_label = None
submit_btn = None
progressbar = None

# Short feedback messages
good_words = ["Nice!", "Sweet!", "Good work!", "Boom!", "Way to go!"]
try_again_words = ["Almost!", "Close one!", "Keep at it!", "You got this!"]
done_words = ["Next time!", "You'll nail it!", "Shake it off!", "No worries!"]
tip_lines = [
    "Double check the operation before solving.",
    "Estimate the answer in your head first.",
    "Keep track of your attempts so you pace yourself.",
    "If subtraction is tough, swap the numbers to avoid negatives.",
]

def clearWindow():
    for w in content_frame.winfo_children():
        w.destroy()

def bind_button_action(widget, command):
    def handle_click(_event):
        play_sound("button")
        command()
    widget.bind("<Button-1>", handle_click)

def makeButton(text, command, parent=None, width=19):
    if parent is None:
        parent = content_frame
    btn = tk.Label(
        parent,
        text=text,
        font=(FONT, 13, "bold"),
        bg=BTN_COLOR,
        fg=BTN_TEXT,
        width=width,
        pady=8,
        bd=0,
        cursor="hand2",
    )
    btn.default_bg = BTN_COLOR
    btn.bind("<Enter>", lambda e: btn.config(bg=BTN_HOVER))
    btn.bind("<Leave>", lambda e: btn.config(bg=btn.default_bg))
    bind_button_action(btn, command)
    return btn

def create_card(title, subtitle=None):
    # use side and fill/expand for packing so frame always fills the content_frame
    shadow = tk.Frame(content_frame, bg=SHADOW_COLOR, bd=0)
    shadow.pack(fill="both", expand=True, padx=20, pady=18)

    card = tk.Frame(shadow, bg=CARD_BG, bd=0, highlightbackground="#c8d6f2", highlightthickness=1)
    card.pack(fill="both", expand=True, padx=2, pady=2)

    accent = tk.Frame(card, bg=ACCENT_COLOR, height=6, bd=0)
    accent.pack(fill="x", side="top")

    header = tk.Frame(card, bg=CARD_BG)
    header.pack(pady=(12, 3), anchor="n")

    tk.Label(header, text=title, font=(FONT, 25, "bold"), bg=CARD_BG, fg=PROBLEM_COLOR).pack()
    if subtitle:
        tk.Label(header, text=subtitle, font=(FONT, 12), bg=CARD_BG, fg=PROBLEM_COLOR).pack(pady=(3, 0))

    body = tk.Frame(card, bg=CARD_BG)
    body.pack(expand=1, fill="both", padx=20, pady=(0,10))

    return shadow, body

def displayMenu():
    clearWindow()
    _, body = create_card("Arithmetic Quiz", "Sharpen your mental math skills.")
    badge = tk.Label(
        body,
        text="Pick your difficulty",
        font=(FONT, 12, "bold"),
        bg="#eaf1ff",
        fg=PROBLEM_COLOR,
        padx=12,
        pady=4,
    )
    badge.pack(pady=(6, 18))
    buttons_frame = tk.Frame(body, bg=CARD_BG)
    buttons_frame.pack(pady=(0, 12))
    makeButton("Easy (1 digit)", lambda: startQuiz(1), parent=buttons_frame, width=22).pack(pady=6)
    makeButton("Moderate (2 digits)", lambda: startQuiz(2), parent=buttons_frame, width=22).pack(pady=6)
    makeButton("Advanced (4 digits)", lambda: startQuiz(4), parent=buttons_frame, width=22).pack(pady=6)
    makeButton("How to Play", showInstructions, parent=buttons_frame, width=22).pack(pady=(12, 0))
    info = tk.Label(
        body,
        text="Each round has 10 questions. You get two tries per problem.",
        font=(FONT, 11),
        bg=CARD_BG,
        fg=PROBLEM_COLOR,
        wraplength=530,
        justify="center"
    )
    info.pack(pady=(15, 6), fill="x")

def randomInt(digits):
    if digits == 1:
        start = 0
    else:
        start = 10 ** (digits - 1)
    end = 10 ** digits - 1
    return random.randint(start, end)

def decideOperation():
    return random.choice(["+", "-"])

def startQuiz(digits):
    global digits_setting, score, question_index
    digits_setting = digits
    score = 0
    question_index = 0
    displayProblem()

def displayProblem():
    global attempts_left, current_answer, answer_entry, feedback_label, submit_btn, progressbar

    if question_index >= TOTAL_QUESTIONS:
        displayResults()
        return

    clearWindow()
    attempts_left = 2

    num1 = randomInt(digits_setting)
    num2 = randomInt(digits_setting)
    op = decideOperation()
    if op == "-" and num1 < num2:
        num1, num2 = num2, num1

    if op == "+":
        current_answer = num1 + num2
    else:
        current_answer = num1 - num2

    question_title = f"Question {question_index + 1} of {TOTAL_QUESTIONS}"
    _, body = create_card("Solve the Problem", question_title)

    top_strip = tk.Frame(body, bg=CARD_BG)
    top_strip.pack(fill="x", pady=(0, 4))
    score_badge = tk.Label(
        top_strip,
        text=f"Score: {score}",
        font=(FONT, 11, "bold"),
        bg="#eaf1ff",
        fg=PROBLEM_COLOR,
        padx=12,
        pady=4,
    )
    score_badge.pack(side="left", padx=(0,4))
    attempts_badge = tk.Label(
        top_strip,
        text="2 tries per question",
        font=(FONT, 9),
        bg=CARD_BG,
        fg="#506a92",
    )
    attempts_badge.pack(side="right", padx=(4,0))

    progressbar_container = tk.Frame(body, bg=CARD_BG)
    progressbar_container.pack(pady=(0, 4), fill="x")
    progress_str = f"Progress {question_index + 1}/{TOTAL_QUESTIONS}"
    tk.Label(
        progressbar_container,
        text=progress_str,
        font=(FONT, 10),
        bg=CARD_BG,
        fg=PROBLEM_COLOR,
        anchor="center"
    ).pack(fill="x")
    progressbar = ttk.Progressbar(
        progressbar_container,
        length=320,
        maximum=TOTAL_QUESTIONS,
        value=question_index + 1,
        mode="determinate",
        style="Quiz.Horizontal.TProgressbar",
    )
    progressbar.pack(pady=(6, 0), padx=38, fill="x")

    # Place main question
    question_lbl = tk.Label(
        body,
        text=f"What is {num1} {op} {num2}?",
        font=(FONT, 23, "bold"),
        bg=CARD_BG,
        fg=PROBLEM_COLOR,
        wraplength=520,
        justify="center"
    )
    question_lbl.pack(pady=10)
    
    # Entry
    entry_frame = tk.Frame(body, bg=CARD_BG)
    entry_frame.pack(pady=(3, 6), fill="x")
    answer_entry = tk.Entry(
        entry_frame,
        font=(FONT, 18),
        justify="center",
        bd=0,
        relief="flat",
        width=9,
        highlightthickness=2,
        highlightbackground=ACCENT_COLOR,
        highlightcolor=BTN_COLOR,
    )
    answer_entry.pack(ipady=8, padx=4, fill="x", expand=True)
    answer_entry.focus()

    # Submit Button
    submit_btn = tk.Label(
        body,
        text="Check Answer",
        font=(FONT, 13, "bold"),
        width=16,
        bg=BTN_COLOR,
        fg="white",
        pady=7,
        cursor="hand2",
        bd=0
    )
    submit_btn.default_bg = BTN_COLOR
    submit_btn.pack(pady=6)
    submit_btn.bind("<Enter>", lambda e: submit_btn.config(bg=BTN_HOVER))
    submit_btn.bind("<Leave>", lambda e: submit_btn.config(bg=submit_btn.default_bg))
    bind_button_action(submit_btn, submitAnswer)

    feedback_label = tk.Label(
        body,
        text="You get two shots.",
        font=(FONT, 11),
        bg=CARD_BG,
        fg=PROBLEM_COLOR,
        anchor="center",
        wraplength=540,
        pady=6,
    )
    feedback_label.pack(pady=(6,4), fill="x")

    # navigation row
    nav_frame = tk.Frame(body, bg=CARD_BG)
    nav_frame.pack(pady=(4,0))
    tip_btn = tk.Label(
        nav_frame,
        text="Tip",
        font=(FONT, 11, "bold"),
        width=9,
        bg=BTN_COLOR,
        fg=BTN_TEXT,
        pady=5,
        cursor="hand2",
    )
    tip_btn.default_bg = BTN_COLOR
    tip_btn.grid(row=0, column=0, padx=7)
    tip_btn.bind("<Enter>", lambda e: tip_btn.config(bg=BTN_HOVER))
    tip_btn.bind("<Leave>", lambda e: tip_btn.config(bg=tip_btn.default_bg))
    bind_button_action(tip_btn, showTip)

    back_btn = tk.Label(
        nav_frame,
        text="Back",
        font=(FONT, 11, "bold"),
        width=9,
        bg=BTN_COLOR,
        fg=BTN_TEXT,
        pady=5,
        cursor="hand2",
    )
    back_btn.default_bg = BTN_COLOR
    back_btn.grid(row=0, column=1, padx=7)
    back_btn.bind("<Enter>", lambda e: back_btn.config(bg=BTN_HOVER))
    back_btn.bind("<Leave>", lambda e: back_btn.config(bg=back_btn.default_bg))
    bind_button_action(back_btn, displayMenu)

    root.after(80, lambda: play_sound("timer"))

def isCorrect(user_answer):
    return user_answer == current_answer

def submitAnswer():
    global attempts_left, score, question_index
    guess = answer_entry.get().strip()
    if guess == "":
        feedback_label.config(text="Type something in.")
        return
    try:
        user_value = int(guess)
    except ValueError:
        feedback_label.config(text="Numbers only please.")
        answer_entry.delete(0, tk.END)
        return
    if isCorrect(user_value):
        play_sound("check")
        answer_entry.config(state="disabled")
        submit_btn.config(bg="#4bb543")
        submit_btn.config(state="disabled")
        if attempts_left == 2:
            score += 10
            feedback_label.config(text=random.choice(good_words) + " +10 points.")
        else:
            score += 5
            feedback_label.config(text=random.choice(good_words) + " +5 points.")
        question_index += 1
        root.after(950, displayProblem)
    else:
        play_sound("wrong")
        attempts_left -= 1
        if attempts_left > 0:
            tries_text = "try" if attempts_left == 1 else "tries"
            feedback_label.config(
                text=f"{random.choice(try_again_words)} {attempts_left} {tries_text} left."
            )
            answer_entry.delete(0, tk.END)
            submit_btn.config(bg=BTN_COLOR)
        else:
            answer_entry.config(state="disabled")
            submit_btn.config(bg="#cf1b1b")
            submit_btn.config(state="disabled")
            feedback_label.config(
                text=f"Answer: {current_answer}. {random.choice(done_words)}"
            )
            question_index += 1
            root.after(1200, displayProblem)

def showTip():
    messagebox.showinfo("Quiz Tip", random.choice(tip_lines))

def showInstructions():
    message = (
        "1. Pick a difficulty level to set the number size.\n"
        "2. Answer 10 random addition or subtraction questions.\n"
        "3. You get two tries per question: 10 points first try, 5 points second try.\n"
        "4. If you miss twice, the correct answer pops up and you move on.\n"
        "5. Your final score and grade show at the end, and you can play again."
    )
    messagebox.showinfo("How to Play", message)

def getGrade(total):
    if total >= 95:
        return "A+"
    if total >= 85:
        return "A"
    if total >= 75:
        return "B"
    if total >= 65:
        return "C"
    if total >= 55:
        return "D"
    return "F"

def displayResults():
    clearWindow()
    grade = getGrade(score)
    _, body = create_card("Quiz Complete", "Here's how you did.")
    score_label = tk.Label(
        body,
        text=f"Final Score: {score} / 100",
        font=(FONT, 16, "bold"),
        bg=CARD_BG,
        fg=PROBLEM_COLOR,
    )
    score_label.pack(pady=(12, 8))
    grade_badge = tk.Label(
        body,
        text=f"Grade: {grade}",
        font=(FONT, 14, "bold"),
        bg="#eaf1ff",
        fg=PROBLEM_COLOR,
        padx=18,
        pady=6,
    )
    grade_badge.pack(pady=(0, 11))
    extra = ""
    if grade == "A+" or grade == "A":
        extra = "Amazing job!"
    elif grade in ["B", "C"]:
        extra = "Not bad! Try again for a higher score?"
    else:
        extra = "Give it another shot!"
    tk.Label(
        body,
        text=extra,
        font=(FONT, 12),
        bg=CARD_BG,
        fg=PROBLEM_COLOR,
    ).pack(pady=(8, 15))
    tk.Label(
        body,
        text="Ready for another round?",
        font=(FONT, 12),
        bg=CARD_BG,
        fg=PROBLEM_COLOR,
    ).pack(pady=(4, 12))
    button_holder = tk.Frame(body, bg=CARD_BG)
    button_holder.pack()
    play_again = tk.Label(
        button_holder,
        text="Play Again",
        font=(FONT, 13, "bold"),
        width=13,
        bg=BTN_COLOR,
        fg=BTN_TEXT,
        pady=7,
        cursor="hand2",
    )
    play_again.default_bg = BTN_COLOR
    play_again.grid(row=0, column=0, padx=8)
    play_again.bind("<Enter>", lambda e: play_again.config(bg=BTN_HOVER))
    play_again.bind("<Leave>", lambda e: play_again.config(bg=play_again.default_bg))
    bind_button_action(play_again, displayMenu)
    quit_btn = tk.Label(
        button_holder,
        text="Quit",
        font=(FONT, 13, "bold"),
        width=13,
        bg=BTN_COLOR,
        fg=BTN_TEXT,
        pady=7,
        cursor="hand2",
    )
    quit_btn.default_bg = BTN_COLOR
    quit_btn.grid(row=0, column=1, padx=8)
    quit_btn.bind("<Enter>", lambda e: quit_btn.config(bg=BTN_HOVER))
    quit_btn.bind("<Leave>", lambda e: quit_btn.config(bg=quit_btn.default_bg))
    bind_button_action(quit_btn, root.destroy)

displayMenu()
root.mainloop()