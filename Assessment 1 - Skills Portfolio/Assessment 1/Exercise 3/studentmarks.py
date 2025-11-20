import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import threading

# ----- Helper functions -----

def calculate_total_coursework(student):
    """Sum of course1, course2, course3"""
    return student['course1'] + student['course2'] + student['course3']

def calculate_overall_percentage(student):
    """Total is (coursework + exam) / 160 * 100"""
    coursework = calculate_total_coursework(student)
    total = coursework + student['exam']
    return round((total / 160) * 100, 2)

def calculate_grade(percentage):
    if percentage >= 70:
        return 'A'
    elif percentage >= 60:
        return 'B'
    elif percentage >= 50:
        return 'C'
    elif percentage >= 40:
        return 'D'
    else:
        return 'F'

def read_students_from_file(filename):
    """Reads students from file into a list of dicts. Returns list or raises."""
    students = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            if not lines:
                return []
            n = int(lines[0])
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) < 6:
                    continue
                student = {
                    "student_code": parts[0],
                    "name": parts[1],
                    "course1": int(parts[2]),
                    "course2": int(parts[3]),
                    "course3": int(parts[4]),
                    "exam": int(parts[5])
                }
                students.append(student)
        return students
    except FileNotFoundError:
        raise FileNotFoundError("Student file not found.")
    except Exception as e:
        raise e

def write_students_to_file(filename, students):
    """Writes the student list to file in correct format."""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(str(len(students)) + "\n")
        for s in students:
            s_line = f"{s['student_code']},{s['name']},{s['course1']},{s['course2']},{s['course3']},{s['exam']}\n"
            f.write(s_line)

def get_student_by_code(students, code):
    """Returns student dict matching student_code or None."""
    for s in students:
        if s['student_code'] == code:
            return s
    return None

def get_student_by_name(students, name):
    """Returns student dict matching name or None (case-insensitive)."""
    for s in students:
        if s['name'].lower() == name.lower():
            return s
    return None

# Main Application Class

class StudentRecordsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Records Manager")
        self.root.configure(bg="#f4f6fa")
        self.root.geometry("950x600")
        self.root.minsize(800,500)
        self.filename = os.path.join(os.path.dirname(__file__), "studentMarks.txt")
        self.students = []
        self.current_sort_asc = True
        self.current_sort_by_percentage = False
        self.style = ttk.Style()
        self.setup_styles()
        self.initialize_ui()
        self.status_msg_queue = []
        self.data_reload()

    def setup_styles(self):
        # Modern color palette
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f4f6fa')
        self.style.configure('SideBar.TFrame', background='#e8eaf0')
        self.style.configure('Content.TFrame', background='#ffffff', relief='flat')
        self.style.configure('Header.TLabel', font=('Segoe UI', 20, 'bold'), background='#ffffff')
        self.style.configure('SubHeader.TLabel', font=('Segoe UI', 11, 'bold'), background='#ffffff')
        self.style.configure('BlueAccent.TButton', font=('Segoe UI', 11), background='#468fd6', foreground='#fff')
        self.style.map('BlueAccent.TButton',
            background=[('active', '#3575b2'), ('pressed', '#346699'), ('!disabled', '#468fd6')]
        )
        self.style.configure('TButton', font=('Segoe UI', 11), padding=4)
        self.style.configure('TLabel', font=('Segoe UI', 11), background="#f4f6fa")
        self.style.configure('Status.TLabel', font=('Segoe UI', 10), background="#e8eaf0", foreground="#222")
        self.style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'))
        self.style.configure('Treeview', font=('Segoe UI', 11))

    def initialize_ui(self):
        # Layout: Sidebar, Top bar, Content frame, Status bar
        self.mainframe = ttk.Frame(self.root, style='TFrame')
        self.mainframe.pack(fill='both', expand=True)
        self.mainframe.rowconfigure(0, weight=1)
        self.mainframe.columnconfigure(1, weight=1)
        
        # Sidebar menu
        self.sidebar = ttk.Frame(self.mainframe, width=200, style='SideBar.TFrame')
        self.sidebar.grid(row=0, column=0, sticky='nsw')
        self.sidebar.grid_propagate(False)
        self.sidebar.rowconfigure(99, weight=1)
        self.build_sidebar()

        # Content
        self.content_frame = ttk.Frame(self.mainframe, style='Content.TFrame')
        self.content_frame.grid(row=0, column=1, sticky='nsew', padx=(0,0), pady=0)
        self.content_frame.rowconfigure(0, weight=1)
        self.content_frame.columnconfigure(0, weight=1)

        # Status bar
        self.statusbar = ttk.Label(self.root, style='Status.TLabel', anchor="w")
        self.statusbar.pack(side='bottom', fill='x')
        self.set_status("Welcome! Ready.")

        # Bind resize to make treeviews adapt
        self.root.bind('<Configure>', self._on_resize)

    def build_sidebar(self):
        # Sidebar for navigation menu
        menu_items = [
            ("View All Records", self.display_all_students),
            ("View Individual", self.search_student_popup),
            ("Highest Mark", self.display_highest_student),
            ("Lowest Mark", self.display_lowest_student),
            ("Sort Records", self.sort_students_popup),
            ("Add Student", self.add_student_popup),
            ("Update Student", self.update_student_popup),
            ("Delete Student", self.delete_student_popup),
            ("Refresh", self.data_reload),
        ]
        padding = {'padx':20, 'pady':10}
        for idx, (txt, cmd) in enumerate(menu_items):
            style = 'BlueAccent.TButton' if idx in (0,1,2,3,4,5,6,7) else 'TButton'
            btn = ttk.Button(self.sidebar, text=txt, style=style, command=cmd)
            btn.grid(row=idx, column=0, sticky='ew', **padding)
        # Filler
        ttk.Label(self.sidebar, text="", style='TLabel', background='#e8eaf0').grid(row=99)
        # App title
        lbl = ttk.Label(self.sidebar, text="Student Records\nApp", style="Header.TLabel",
                        background="#e8eaf0", anchor="center", justify="center")
        lbl.grid(row=101, column=0, sticky='sew', pady=(10,10))

    def clear_content_frame(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def set_status(self, message):
        self.statusbar.config(text=" " + message)
        # Optional: animate status fade or reset after time
        # Just set message for now

    def _on_resize(self, event):
        # For responsive Treeview resizing
        children = self.content_frame.winfo_children()
        for c in children:
            if isinstance(c, ttk.Treeview):
                c['height'] = max(10, int(self.content_frame.winfo_height() / 32))

    # --- File/data loading and refreshing ---

    def data_reload(self):
        try:
            self.students = read_students_from_file(self.filename)
        except Exception as e:
            self.students = []
            self.show_error(f"Error loading student file:\n{e}")
            self.set_status("Data load failed.")
            return
        self.set_status("Data loaded.")
        self.display_all_students()

    # --- Main display functions ---

    def display_all_students(self, sort_asc=None):
        """Displays all students in scrollable treeview table"""
        self.clear_content_frame()
        panel = ttk.Frame(self.content_frame, style='Content.TFrame', padding=(15,10,10,10))
        panel.grid(row=0, column=0, sticky='nsew')
        title = ttk.Label(panel, text="All Student Records", style="Header.TLabel")
        title.grid(row=0, column=0, sticky='w', pady=(0,10), columnspan=2)
        
        # Treeview with scroll
        columns = ("student_code","name","coursework","exam","overall_pct","grade")
        tree_frame = ttk.Frame(panel, style="Content.TFrame")
        tree_frame.grid(row=1, column=0, sticky="nsew", columnspan=2)
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', style='Treeview')
        tree.heading("student_code", text="Student Number")
        tree.heading("name", text="Name")
        tree.heading("coursework", text="Coursework (60)")
        tree.heading("exam", text="Exam (100)")
        tree.heading("overall_pct", text="Overall %")
        tree.heading("grade", text="Grade")
        for col in columns:
            tree.column(col, anchor="center", width=110, minwidth=80, stretch=True)
        # Font
        tree.tag_configure('oddrow', background='#f1f6fc')
        tree.tag_configure('evenrow', background='#fff')

        # Scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=vsb.set)
        vsb.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True, padx=(0,10), pady=(0,5))

        # Sorting
        list_students = self.students.copy()
        if self.current_sort_by_percentage:
            list_students.sort(key=lambda s: calculate_overall_percentage(s),
                               reverse=not self.current_sort_asc)
        if sort_asc is not None:
            order = sort_asc
            list_students.sort(key=lambda s: calculate_overall_percentage(s),
                               reverse=not order)
        # Add rows to tree
        total_pct = 0.0
        total_count = len(list_students)
        for idx, s in enumerate(list_students):
            coursework = calculate_total_coursework(s)
            overall_pct = calculate_overall_percentage(s)
            grade = calculate_grade(overall_pct)
            values = (
                s['student_code'],
                s['name'],
                f"{coursework}",
                f"{s['exam']}",
                f"{overall_pct:.2f}",
                grade
            )
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            tree.insert('', 'end', values=values, tags=(tag,))
            total_pct += overall_pct

        # Footer
        avg_pct = (total_pct / total_count) if total_count else 0.0

        info_text = (
            f"Total number of students: {total_count}\n"
            f"Class average percentage: {avg_pct:.2f}%"
        )
        lbl = ttk.Label(panel, text=info_text, style="SubHeader.TLabel", background="#fff")
        lbl.grid(row=2, column=0, sticky='w', pady=(12,8), columnspan=2)
        self.set_status(f"Displayed all {total_count} students.")

    def format_student_full(self, student):
        coursework = calculate_total_coursework(student)
        pct = calculate_overall_percentage(student)
        grade = calculate_grade(pct)
        s = "Name: {}\nStudent Number: {}\nCoursework (out of 60): {}\nExam (out of 100): {}\nOverall Percentage: {:.2f}%\nGrade: {}".format(
            student['name'], student['student_code'], coursework, student['exam'], pct, grade
        )
        return s

    def display_student_record(self, student, title=None):
        """Display ONE full student record as pretty panel"""
        self.clear_content_frame()
        panel = ttk.Frame(self.content_frame, style='Content.TFrame', padding=(17,15,17,17))
        panel.grid(row=0, column=0, sticky='nsew')
        lbl_title = ttk.Label(panel, text=title or "Student Record", style="Header.TLabel")
        lbl_title.grid(row=0, column=0, sticky='w', pady=(0,10))
        txt = self.format_student_full(student)
        lbl = ttk.Label(panel, text=txt, style="TLabel", background="#fff", font=("Segoe UI", 13), justify="left")
        lbl.grid(row=1, column=0, sticky='w', padx=(0,20))
        self.set_status(f"Displayed student: {student['name']} ({student['student_code']})")

    def display_highest_student(self):
        if not self.students:
            self.show_error("No students found.")
            return
        s = max(self.students, key=lambda s: calculate_overall_percentage(s))
        self.display_student_record(s, title="Student With Highest Total Mark")

    def display_lowest_student(self):
        if not self.students:
            self.show_error("No students found.")
            return
        s = min(self.students, key=lambda s: calculate_overall_percentage(s))
        self.display_student_record(s, title="Student With Lowest Total Mark")

    # --- Popup and searching ---

    def search_student_popup(self):
        # Prompt for student number or name; then display if found
        def on_search():
            val = entry.get().strip()
            if not val:
                self.show_error("Please enter student number or name.")
                return
            s = get_student_by_code(self.students, val)
            if not s:
                s = get_student_by_name(self.students, val)
            if not s:
                self.show_error("Student not found!")
                return
            popup.destroy()
            self.display_student_record(s)

        popup = tk.Toplevel(self.root)
        popup.title("Search Student")
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(bg='#eaf2fb')
        popup.resizable(False, False)
        frm = ttk.Frame(popup, padding=25)
        frm.pack(fill='both', expand=True)
        lbl = ttk.Label(frm, text="Enter student number or name:", font=("Segoe UI", 11))
        lbl.pack(anchor='w', pady=(0,9))
        entry = ttk.Entry(frm, font=("Segoe UI", 11), width=28)
        entry.pack(fill='x', pady=(0,9))
        entry.focus_set()
        btn = ttk.Button(frm, text="Search", style="BlueAccent.TButton", command=on_search)
        btn.pack()
        popup.bind('<Return>', lambda e: on_search())
        self.set_status("Searching for student record ...")

    def sort_students_popup(self):
        def set_sort(order):
            self.current_sort_asc = (order == "Ascending")
            self.current_sort_by_percentage = True
            popup.destroy()
            self.display_all_students(sort_asc=(order=="Ascending"))

        popup = tk.Toplevel(self.root)
        popup.title("Sort Student Records")
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(bg='#eaf2fb')
        popup.resizable(False, False)
        frm = ttk.Frame(popup, padding=25)
        frm.pack(fill='both', expand=True)
        lbl = ttk.Label(frm, text="Sort by overall percentage:", font=("Segoe UI", 11))
        lbl.pack(anchor='w', pady=(0,12))
        btn1 = ttk.Button(frm, text="Ascending", style="BlueAccent.TButton", command=lambda: set_sort("Ascending"))
        btn1.pack(fill='x', pady=(0,7))
        btn2 = ttk.Button(frm, text="Descending", style="BlueAccent.TButton", command=lambda: set_sort("Descending"))
        btn2.pack(fill='x')
        self.set_status("Sort menu opened.")

    # --- Add Student ---

    def add_student_popup(self):
        """Show form to add student; validate and append"""
        popup = tk.Toplevel(self.root)
        popup.title("Add Student Record")
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(bg='#eaf2fb')
        frm = ttk.Frame(popup, padding=20)
        frm.pack(fill='both', expand=True)
        popup.resizable(False, False)

        fields = [
            {'label': 'Student number', 'key': 'student_code'},
            {'label': 'Name', 'key': 'name'},
            {'label': 'Course 1 (out of 20)', 'key': 'course1'},
            {'label': 'Course 2 (out of 20)', 'key': 'course2'},
            {'label': 'Course 3 (out of 20)', 'key': 'course3'},
            {'label': 'Exam mark (out of 100)', 'key': 'exam'}
        ]
        entries = {}
        for idx, f in enumerate(fields):
            ttk.Label(frm, text=f['label'] + ":", font=("Segoe UI", 11)).grid(row=idx, column=0, sticky='w', pady=(0,7))
            ent = ttk.Entry(frm, font=("Segoe UI", 11), width=26)
            ent.grid(row=idx, column=1, pady=(0,7))
            entries[f['key']] = ent

        def on_submit():
            record = {}
            for f in fields:
                val = entries[f['key']].get().strip()
                if f['key'] in ('course1','course2','course3','exam'):
                    if not val.isdigit():
                        self.show_error("All marks must be numbers.", parent=popup)
                        return
                if not val:
                    self.show_error("All fields are required.", parent=popup)
                    return
                record[f['key']] = val

            # Validation on marks
            try:
                c1 = int(record['course1'])
                c2 = int(record['course2'])
                c3 = int(record['course3'])
                ex = int(record['exam'])
                scode = record['student_code']
                sname = record['name']
                if scode in [s['student_code'] for s in self.students]:
                    self.show_error("Student number already exists!", parent=popup)
                    return
                if not (0 <= c1 <= 20 and 0 <= c2 <= 20 and 0 <= c3 <= 20):
                    self.show_error("Course marks must be between 0 and 20.", parent=popup)
                    return
                if not (0 <= ex <= 100):
                    self.show_error("Exam mark must be between 0 and 100.", parent=popup)
                    return
                # Passed checks
                new_student = {
                    "student_code": scode,
                    "name": sname,
                    "course1": c1,
                    "course2": c2,
                    "course3": c3,
                    "exam": ex
                }
                self.students.append(new_student)
                write_students_to_file(self.filename, self.students)
                popup.destroy()
                self.set_status(f"Added {sname} ({scode}). File updated.")
                self.data_reload()
            except Exception as e:
                self.show_error(f"Invalid entry: {e}", parent=popup)

        btn = ttk.Button(frm, text="Add Record", style="BlueAccent.TButton", command=on_submit)
        btn.grid(row=len(fields), column=0, pady=(17,0), columnspan=2, sticky='ew')
        self.set_status("Add student record: form opened.")

    # --- Delete Student ---

    def delete_student_popup(self):
        # Prompt for student code or name, confirm before deleting
        popup = tk.Toplevel(self.root)
        popup.title("Delete Student Record")
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(bg='#eaf2fb')
        frm = ttk.Frame(popup, padding=25)
        frm.pack(fill='both', expand=True)
        popup.resizable(False, False)
        ttk.Label(frm, text="Enter student number or name:", font=("Segoe UI", 11)).pack(anchor='w', pady=(0,10))
        entry = ttk.Entry(frm, font=("Segoe UI", 11), width=28)
        entry.pack(fill='x', pady=(0,9))
        entry.focus_set()
        
        def do_delete():
            val = entry.get().strip()
            if not val:
                self.show_error("Enter student number or name.", parent=popup)
                return
            idx, student = None, None
            for i,s in enumerate(self.students):
                if s['student_code'] == val or s['name'].lower() == val.lower():
                    idx = i
                    student = s
                    break
            if idx is None:
                self.show_error("Student not found.", parent=popup)
                return
            # Confirm
            agreed = messagebox.askyesno(
                "Confirm Deletion",
                f"Delete student:\n{student['name']} ({student['student_code']})?",
                parent=popup
            )
            if not agreed:
                return
            # Execute deletion
            del self.students[idx]
            write_students_to_file(self.filename, self.students)
            popup.destroy()
            self.set_status(f"Deleted student {student['student_code']}.")
            self.data_reload()

        btn = ttk.Button(frm, text="Delete", style="BlueAccent.TButton", command=do_delete)
        btn.pack(pady=(13,0))
        self.set_status("Delete student: popup opened.")

    # --- Update Student ---

    def update_student_popup(self):
        # Step 1: Prompt for number or name
        popup = tk.Toplevel(self.root)
        popup.title("Update Student Record")
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(bg='#eaf2fb')
        frm = ttk.Frame(popup, padding=20)
        frm.pack(fill='both', expand=True)
        popup.resizable(False, False)
        ttk.Label(frm, text="Enter student number or name to update:", font=("Segoe UI", 11)).grid(row=0, column=0, sticky='w', pady=(0,8))
        entry = ttk.Entry(frm, font=("Segoe UI", 11), width=28)
        entry.grid(row=1, column=0)
        entry.focus_set()
        def on_next():
            val = entry.get().strip()
            student = get_student_by_code(self.students, val)
            if not student:
                student = get_student_by_name(self.students, val)
            if not student:
                self.show_error("Student not found.", parent=popup)
                return
            popup.destroy()
            self._update_student_details_popup(student)
        btn = ttk.Button(frm, text="Edit", style="BlueAccent.TButton", command=on_next)
        btn.grid(row=2, column=0, pady=(9,0))
        self.set_status("Update student: find student.")

    def _update_student_details_popup(self, student):
        # Step 2: Edit fields in a popup
        popup = tk.Toplevel(self.root)
        popup.title("Edit Student Record")
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(bg='#eaf2fb')
        frm = ttk.Frame(popup, padding=20)
        frm.pack(fill='both', expand=True)
        popup.resizable(False, False)

        fields = [
            {'label': 'Name', 'key': 'name'},
            {'label': 'Course 1 (out of 20)', 'key': 'course1'},
            {'label': 'Course 2 (out of 20)', 'key': 'course2'},
            {'label': 'Course 3 (out of 20)', 'key': 'course3'},
            {'label': 'Exam mark (out of 100)', 'key': 'exam'}
        ]
        entries = {}
        ttk.Label(frm, text="Student number: " + student['student_code'], font=("Segoe UI", 10, 'italic')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0,8))
        for idx, f in enumerate(fields):
            ttk.Label(frm, text=f['label'] + ":", font=("Segoe UI", 11)).grid(row=idx+1, column=0, sticky='w', pady=(0,7))
            ent = ttk.Entry(frm, font=("Segoe UI", 11), width=26)
            ent.insert(0, str(student[f['key']]))
            ent.grid(row=idx+1, column=1, pady=(0,7))
            entries[f['key']] = ent

        def do_update():
            for f in fields:
                val = entries[f['key']].get().strip()
                if not val:
                    self.show_error("All fields are required.", parent=popup)
                    return
                if f['key'] != 'name' and not val.isdigit():
                    self.show_error("All marks must be numbers.", parent=popup)
                    return
            # Validate ranges
            try:
                c1 = int(entries['course1'].get())
                c2 = int(entries['course2'].get())
                c3 = int(entries['course3'].get())
                ex = int(entries['exam'].get())
                if not (0 <= c1 <= 20 and 0 <= c2 <= 20 and 0 <= c3 <= 20):
                    self.show_error("Course marks must be between 0 and 20.", parent=popup)
                    return
                if not (0 <= ex <= 100):
                    self.show_error("Exam mark must be between 0 and 100.", parent=popup)
                    return
                # Find index in list
                idx = None
                for i,s in enumerate(self.students):
                    if s['student_code'] == student['student_code']:
                        idx = i
                        break
                if idx is None:
                    self.show_error("Student record missing!", parent=popup)
                    return
                # Confirm update
                agreed = messagebox.askyesno(
                    "Confirm Update",
                    "Apply these changes to student record?",
                    parent=popup
                )
                if not agreed:
                    return
                # Update student
                self.students[idx]['name'] = entries['name'].get().strip()
                self.students[idx]['course1'] = c1
                self.students[idx]['course2'] = c2
                self.students[idx]['course3'] = c3
                self.students[idx]['exam'] = ex
                write_students_to_file(self.filename, self.students)
                popup.destroy()
                self.set_status("Student record updated.")
                self.data_reload()
            except Exception as e:
                self.show_error(f"Error: {e}", parent=popup)

        btn = ttk.Button(frm, text="Update", style="BlueAccent.TButton", command=do_update)
        btn.grid(row=len(fields)+2, column=0, pady=(13,0), columnspan=2, sticky='ew')
        self.set_status("Update student: edit fields.")

    # --- Utility UI ---

    def show_error(self, msg, parent=None):
        messagebox.showerror("Error", msg, parent=parent or self.root)
        self.set_status("Error: " + msg)

# ------------ Main entry ------------

def main():
    root = tk.Tk()
    app = StudentRecordsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
