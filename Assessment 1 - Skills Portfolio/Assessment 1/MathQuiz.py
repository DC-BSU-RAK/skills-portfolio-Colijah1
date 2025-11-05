import tkinter as tk
from tkinter import ttk, messagebox
import random

# Code for Display Settings
TOTAL_QUESTIONS = 10

BG_COLOR = "#f2f3f5"        # light grey
BTN_COLOR = "#2574cf"       # blue
BTN_HOVER = "#005bb9"
BTN_TEXT = "white"
PROBLEM_COLOR = "#184173"
FONT = "Segoe UI"

# Code for reusing main window
root = tk.Tk()
root.title("Arithmetic Quiz")
root.geometry("520x580")
root.configure(bg=BG_COLOR)
root.resizable(False, False)

# Variables
score = 0
question_index = 0
current_answer = 0
attempts_left = 2
digits_setting = 1

answer_entry = None
feedback_label = None
submit_btn = None
progressbar = None

# Feedback Messages 
good_words = ["Nice!", "Sweet!", "Good work!", "Boom!", "Way to go!"]
try_again_words = ["Almost!", "Close one!", "Keep at it!", "You got this!"]
done_words = ["Next time!", "You'll nail it!", "Shake it off!", "No worries!"]
tip_lines = [
    "Double check the operation before solving.",
    "Estimate the answer in your head first.",
    "Keep track of your attempts so you pace yourself.",
    "If subtraction is tough, swap the numbers to avoid negatives.",
]

# Clears window before making new one
def clearWindow():
    # To remove widget
    for w in root.winfo_children():
        w.destroy()

# Reusable code created for button design
def makeButton(text, command):
    btn = tk.Label(root, text=text, font=(FONT, 12, "bold"), 
                   bg=BTN_COLOR, fg=BTN_TEXT, width=19, pady=8, bd=0, cursor="hand2")
    btn.default_bg = BTN_COLOR
    btn.bind("<Enter>", lambda e: btn.config(bg=BTN_HOVER))
    btn.bind("<Leave>", lambda e: btn.config(bg=btn.default_bg))
    btn.bind("<Button-1>", lambda e: command())
    return btn

def displayMenu():
    """Show the home screen where the player picks a difficulty."""
    clearWindow()
    # Title
    tk.Label(root, text="Arithmetic Quiz", font=(FONT, 25, "bold"), bg=BG_COLOR, fg=PROBLEM_COLOR).pack(pady=38)
    # Subtext
    tk.Label(root, text="Pick your difficulty", font=(FONT, 13), bg=BG_COLOR, fg=PROBLEM_COLOR).pack(pady=(0,15))

    # Difficulty buttons set to the middle
    makeButton("Easy (1 digit)", lambda: startQuiz(1)).pack(pady=9)
    makeButton("Moderate (2 digits)", lambda: startQuiz(2)).pack(pady=9)
    makeButton("Advanced (4 digits)", lambda: startQuiz(4)).pack(pady=9)
    makeButton("How to Play", showInstructions).pack(pady=9)

    # Instructions
    tk.Label(root, text="Each question can be + or -. Two tries for each.\n10 questions total.",
             font=(FONT, 10), bg=BG_COLOR, fg=PROBLEM_COLOR, justify="center").pack(pady=45)

def randomInt(digits):
    """Return a random number that matches the difficulty choice."""
    # Random int generator
    if digits == 1:
        start = 0
    else:
        start = 10 ** (digits - 1)
    end = 10 ** digits - 1
    return random.randint(start, end)

def decideOperation():
    """Randomly choose either + or -."""
    return random.choice(["+", "-"])

def startQuiz(digits):
    """Reset everything and load the first problem."""
    global digits_setting, score, question_index
    digits_setting = digits
    score = 0
    question_index = 0
    displayProblem()

def displayProblem():
    """Problem Displayer"""
    global attempts_left, current_answer, answer_entry, feedback_label, submit_btn, progressbar

    if question_index >= TOTAL_QUESTIONS:
        displayResults()
        return

    clearWindow()
    attempts_left = 2

    # Number & operation picker
    num1 = randomInt(digits_setting)
    num2 = randomInt(digits_setting)
    op = decideOperation()
    if op == "-" and num1 < num2:
        num1, num2 = num2, num1  # ensure no negative answers

    if op == "+":
        current_answer = num1 + num2
    else:
        current_answer = num1 - num2

    # Centered frame to hold the main stuff
    mainframe = tk.Frame(root, bg=BG_COLOR)
    mainframe.pack(expand=1)

    # Progress indicator and bar
    progress_str = f"{question_index + 1} / {TOTAL_QUESTIONS}"
    tk.Label(mainframe, text=progress_str, font=(FONT, 12), bg=BG_COLOR, fg=PROBLEM_COLOR).pack(pady=(25, 7))
    # Progress bar (ttk)
    progressbar = ttk.Progressbar(mainframe, length=250, maximum=TOTAL_QUESTIONS, value=question_index+1)
    progressbar.pack(pady=(0,8))

    # Score
    tk.Label(mainframe, text=f"Score: {score}", font=(FONT, 12), bg=BG_COLOR, fg=PROBLEM_COLOR).pack(pady=(0,13))

    # Main math question (big, bold)
    tk.Label(mainframe, text=f"What is {num1} {op} {num2} ?", font=(FONT, 23, "bold"),
             bg=BG_COLOR, fg=PROBLEM_COLOR).pack(pady=12)

    # Entry (centered)
    entry_frame = tk.Frame(mainframe, bg=BG_COLOR)
    entry_frame.pack(pady=8)
    global answer_entry
    answer_entry = tk.Entry(entry_frame, font=(FONT, 17), justify="center", bd=2,
                            relief="groove", width=8)
    answer_entry.pack(ipady=7)
    answer_entry.focus()

    # Submit button (nice and wide)
    global submit_btn
    submit_btn = tk.Label(mainframe, text="Submit", font=(FONT, 13, "bold"), width=13,
                          bg=BTN_COLOR, fg="white", pady=7, cursor="hand2")
    submit_btn.default_bg = BTN_COLOR
    submit_btn.pack(pady=15)
    submit_btn.bind("<Enter>", lambda e: submit_btn.config(bg=BTN_HOVER))
    submit_btn.bind("<Leave>", lambda e: submit_btn.config(bg=BTN_COLOR))
    submit_btn.bind("<Button-1>", lambda e: submitAnswer())

    # Feedback/instructions label
    global feedback_label
    feedback_label = tk.Label(mainframe, text="You get two shots.", font=(FONT, 11),
                              bg=BG_COLOR, fg=PROBLEM_COLOR)
    feedback_label.pack(pady=14)

    nav_frame = tk.Frame(mainframe, bg=BG_COLOR)
    nav_frame.pack(pady=(12, 4))

    tip_btn = tk.Label(nav_frame, text="Tip", font=(FONT, 11, "bold"), width=10,
                       bg=BTN_COLOR, fg=BTN_TEXT, pady=5, cursor="hand2")
    tip_btn.default_bg = BTN_COLOR
    tip_btn.grid(row=0, column=0, padx=5)
    tip_btn.bind("<Enter>", lambda e: tip_btn.config(bg=BTN_HOVER))
    tip_btn.bind("<Leave>", lambda e: tip_btn.config(bg=tip_btn.default_bg))
    tip_btn.bind("<Button-1>", lambda e: showTip())

    back_btn = tk.Label(nav_frame, text="Back", font=(FONT, 11, "bold"), width=10,
                        bg=BTN_COLOR, fg=BTN_TEXT, pady=5, cursor="hand2")
    back_btn.default_bg = BTN_COLOR
    back_btn.grid(row=0, column=1, padx=5)
    back_btn.bind("<Enter>", lambda e: back_btn.config(bg=BTN_HOVER))
    back_btn.bind("<Leave>", lambda e: back_btn.config(bg=back_btn.default_bg))
    back_btn.bind("<Button-1>", lambda e: displayMenu())

def isCorrect(user_answer):
    """Check if the player's guess matches the real answer."""
    return user_answer == current_answer

def submitAnswer():
    """Handle the submit button, score updates, and feedback."""
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
        answer_entry.config(state="disabled")
        submit_btn.config(bg="#4bb543")  # green for correct
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
        attempts_left -= 1
        if attempts_left > 0:
            feedback_label.config(text=random.choice(try_again_words) + " Try again.")
            answer_entry.delete(0, tk.END)
            submit_btn.config(bg=BTN_COLOR)
        else:
            answer_entry.config(state="disabled")
            submit_btn.config(bg="#cf1b1b") # red on wrong
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
    """Convert the point total to a simple letter grade."""
    # Simple grading (out of 100)
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

    endf = tk.Frame(root, bg=BG_COLOR)
    endf.pack(expand=1)

    tk.Label(endf, text="Quiz Finished!", font=(FONT, 25, "bold"), bg=BG_COLOR, fg=PROBLEM_COLOR).pack(pady=(48,16))
    tk.Label(endf, text=f"Final Score: {score} / 100", font=(FONT, 14), bg=BG_COLOR, fg=PROBLEM_COLOR).pack(pady=8)

    tk.Label(endf, text=f"Grade: {grade}", font=(FONT, 15, "bold"),
             bg=BG_COLOR, fg=PROBLEM_COLOR).pack(pady=4)

    # One more encouraging msg depending on grade
    extra = ""
    if grade == "A+" or grade == "A":
        extra = "Amazing job!"
    elif grade in ["B", "C"]:
        extra = "Not bad! Try again for a higher score?"
    else:
        extra = "Give it another shot!"
    tk.Label(endf, text=extra, font=(FONT, 11), bg=BG_COLOR, fg=PROBLEM_COLOR).pack(pady=6)
    tk.Label(endf, text="Play again?", font=(FONT, 12), bg=BG_COLOR, fg=PROBLEM_COLOR).pack(pady=(22,6))

    # Play again and quit buttons (with hover)
    play_again = tk.Label(endf, text="Play Again", font=(FONT, 13, "bold"),
                          width=13, bg=BTN_COLOR, fg=BTN_TEXT, pady=7, cursor="hand2")
    play_again.default_bg = BTN_COLOR
    play_again.pack(pady=9)
    play_again.bind("<Enter>", lambda e: play_again.config(bg=BTN_HOVER))
    play_again.bind("<Leave>", lambda e: play_again.config(bg=play_again.default_bg))
    play_again.bind("<Button-1>", lambda e: displayMenu())

    quit_btn = tk.Label(endf, text="Quit", font=(FONT, 13, "bold"),
                        width=13, bg=BTN_COLOR, fg=BTN_TEXT, pady=6, cursor="hand2")
    quit_btn.default_bg = BTN_COLOR
    quit_btn.pack(pady=6)
    quit_btn.bind("<Enter>", lambda e: quit_btn.config(bg=BTN_HOVER))
    quit_btn.bind("<Leave>", lambda e: quit_btn.config(bg=quit_btn.default_bg))
    quit_btn.bind("<Button-1>", lambda e: root.destroy())

# Kick things off by showing the menu and starting the GUI loop
displayMenu()
root.mainloop()