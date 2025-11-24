import tkinter as tk
from tkinter import ttk
import random
import os
import threading
import subprocess
import sys

# Try to import PIL for icon creation
try:
    from PIL import Image, ImageTk, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Try to import audio libraries
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

HAS_PYGAME = False
pygame = None
try:
    import pygame
    # Initialize pygame mixer with proper settings
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.mixer.init()
    HAS_PYGAME = True
except (ImportError, Exception):
    HAS_PYGAME = False
    pygame = None

class AlexaJokeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alexa Joke App")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Set custom window icon
        self.set_window_icon()
        
        # Set root window background color for card effect - calm blue-gray
        self.root.configure(bg='#f5f7fa')
        
        # Load jokes from file
        self.jokes = self.load_jokes()
        self.current_joke = None
        self.current_setup = ""
        self.current_punchline = ""
        self.punchline_animation_id = None
        self.setup_animation_id = None
        self.typing_sound_playing = False  # Track typing sound state for 1-second rule
        self.typing_sound_end_timer = None # Keep reference to the timer
        
        # Setup sound file paths
        self.setup_sound_paths()
        
        # Create GUI elements
        self.create_widgets()
    
    def set_window_icon(self):
        """Create and set a custom window icon for Alexa Joke App"""
        try:
            if HAS_PIL:
                icon_path = os.path.join(os.path.dirname(__file__), "alexa_icon.ico")
                
                # Create icon file if it doesn't exist
                if not os.path.exists(icon_path):
                    # Create icon images in multiple sizes
                    icon_images = []
                    for size in [(16, 16), (32, 32), (48, 48), (64, 64)]:
                        # Create an image with a blue background (matching app theme)
                        img = Image.new('RGBA', size, color=(52, 152, 219, 255))  # #3498db
                        draw = ImageDraw.Draw(img)
                        
                        # Draw a circle for the icon background
                        margin = max(1, size[0] // 8)
                        draw.ellipse([margin, margin, size[0]-margin, size[1]-margin], 
                                   outline='white', width=max(1, size[0] // 16))
                        
                        # Draw "A" letter for Alexa in white
                        try:
                            from PIL import ImageFont
                            font_size = max(8, size[0] // 2)
                            draw.text((size[0]//2, size[1]//2), 'A', fill='white', 
                                     anchor='mm', font=None)
                        except:
                            draw.text((size[0]//2, size[1]//2), 'A', fill='white', anchor='mm')
                        
                        icon_images.append(img)
                    
                    # Save as ICO file with multiple sizes
                    icon_images[0].save(icon_path, format='ICO', sizes=[(img.width, img.height) for img in icon_images])
                
                # Set the icon using iconbitmap (best for Windows)
                try:
                    self.root.iconbitmap(icon_path)
                except:
                    # Fallback to iconphoto
                    img = Image.open(icon_path)
                    photo = ImageTk.PhotoImage(img)
                    self.root.iconphoto(True, photo)
                    self.icon_images = [photo]
            else:
                # Fallback: Try to use iconbitmap if icon file exists
                icon_path = os.path.join(os.path.dirname(__file__), "alexa_icon.ico")
                if os.path.exists(icon_path):
                    try:
                        self.root.iconbitmap(icon_path)
                    except:
                        pass
        except Exception as e:
            # If icon setting fails, continue without custom icon
            pass

    def setup_sound_paths(self):
        """Setup paths to MP3 sound files"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sound_assets_dir = os.path.join(script_dir, 'sound assets')
        
        # Use sound files from sound assets folder
        self.button_click_sound = os.path.join(sound_assets_dir, 'button.mp3')
        self.typing_sound = os.path.join(sound_assets_dir, 'typing.mp3')
        
        # Verify files exist
        if not os.path.exists(self.button_click_sound):
            print(f"Warning: Button sound not found at {self.button_click_sound}")
        if not os.path.exists(self.typing_sound):
            print(f"Warning: Typing sound not found at {self.typing_sound}")
        
        # Preload sounds if pygame is available
        self.button_sound_obj = None
        self.typing_sound_obj = None
        if HAS_PYGAME:
            try:
                if os.path.exists(self.button_click_sound):
                    self.button_sound_obj = pygame.mixer.Sound(self.button_click_sound)
                if os.path.exists(self.typing_sound):
                    self.typing_sound_obj = pygame.mixer.Sound(self.typing_sound)
            except Exception as e:
                print(f"Error loading sounds: {e}")
        
    def load_jokes(self):
        """Load jokes from randomJokes.txt file"""
        jokes = []
        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            jokes_file = os.path.join(script_dir, 'resources', 'randomJokes.txt')
            with open(jokes_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    # Find the first question mark
                    q_index = line.find('?')
                    if q_index != -1:
                        setup = line[:q_index + 1].strip()
                        punchline = line[q_index + 1:].strip()
                        jokes.append({'setup': setup, 'punchline': punchline})
                    else:
                        # If no question mark, treat entire line as setup
                        jokes.append({'setup': line, 'punchline': ''})
        except FileNotFoundError:
            print("Error: randomJokes.txt not found!")
            return []
        return jokes
    
    def create_widgets(self):
        """Create and arrange GUI widgets"""
        # Configure root window to center content
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Configure modern button styles
        self.setup_button_styles()
        
        # Create shadow frame for soft shadow effect - subtle blue-gray shadow
        shadow_frame = tk.Frame(self.root, bg='#c8d6e5', padx=2, pady=2)
        shadow_frame.grid(row=0, column=0, sticky="", padx=10, pady=10)
        
        # Create card container frame with white background and subtle border
        card_frame = tk.Frame(shadow_frame, bg='#ffffff', relief='flat', 
                             borderwidth=1, highlightbackground='#e1e8ed',
                             highlightthickness=1)
        card_frame.pack(fill='both', expand=True)
        
        # Main content frame with padding inside the card
        main_frame = tk.Frame(card_frame, bg='#ffffff', padx=30, pady=30)
        main_frame.pack(fill='both', expand=True)
        
        # Title label - dark blue-gray for contrast
        title_label = tk.Label(main_frame, text="Alexa Joke App", 
                               font=('Arial', 16, 'bold'),
                               bg='#ffffff', fg='#2c3e50')
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Button to get a joke
        self.tell_joke_btn = ttk.Button(
            main_frame,
            text="Alexa tell me a Joke",
            command=self.tell_joke_with_sound,
            width=30,
            style='Accent.TButton'
        )
        self.tell_joke_btn.grid(row=1, column=0, pady=10)
        
        # Label for joke setup - dark text for readability
        self.setup_label = tk.Label(main_frame, text="", 
                                     font=('Arial', 12),
                                     wraplength=500, justify='center',
                                     bg='#ffffff', fg='#34495e')
        self.setup_label.grid(row=2, column=0, pady=20, padx=10)
        
        # Label for punchline - calm teal accent color
        self.punchline_label = tk.Label(main_frame, text="", 
                                         font=('Arial', 12, 'italic'),
                                         wraplength=500, justify='center',
                                         foreground='#16a085', bg='#ffffff')
        self.punchline_label.grid(row=3, column=0, pady=10, padx=10)
        
        # Button frame for action buttons
        button_frame = tk.Frame(main_frame, bg='#ffffff')
        button_frame.grid(row=4, column=0, pady=20)
        
        # Show punchline button (should play button mp3)
        self.show_punchline_btn = ttk.Button(
            button_frame,
            text="Show Punchline",
            command=self.show_punchline_with_sound,
            state='disabled',
            width=20
        )
        self.show_punchline_btn.grid(row=0, column=0, padx=5)
        self.add_hover_effect(self.show_punchline_btn)
        
        # Next joke button (should play button mp3)
        self.next_joke_btn = ttk.Button(
            button_frame,
            text="Next Joke",
            command=self.next_joke_with_sound,
            state='disabled',
            width=20
        )
        self.next_joke_btn.grid(row=0, column=1, padx=5)
        self.add_hover_effect(self.next_joke_btn)
        
        # Quit button (should play button mp3)
        self.quit_btn = ttk.Button(
            button_frame,
            text="Quit",
            command=self.quit_with_sound,
            width=20
        )
        self.quit_btn.grid(row=0, column=2, padx=5)
        self.add_hover_effect(self.quit_btn)
        
        # Add hover effect to main joke button
        self.add_hover_effect(self.tell_joke_btn)

    def setup_button_styles(self):
        """Configure modern button styles with calm color palette"""
        style = ttk.Style()
        
        # Configure default button style
        style.configure('TButton',
                       background='#ecf0f1',
                       foreground='#2c3e50',
                       borderwidth=1,
                       relief='flat',
                       padding=8)
        style.map('TButton',
                 background=[('active', '#d5dbdb'),
                            ('pressed', '#bdc3c7')],
                 relief=[('pressed', 'sunken')])
        
        # Configure accent button style for main action
        style.configure('Accent.TButton',
                       background='#3498db',
                       foreground='#000000',
                       borderwidth=1,
                       relief='flat',
                       padding=8)
        style.map('Accent.TButton',
                 background=[('active', '#2980b9'),
                            ('pressed', '#21618c')],
                 foreground=[('active', '#000000'),
                            ('pressed', '#000000')],
                 relief=[('pressed', 'sunken')])
        
    def tell_joke_with_sound(self):
        """Play button sound, then tell a joke and play typing sound"""
        self.play_button_click()
        self.tell_joke(play_typing=True)
    
    def show_punchline_with_sound(self):
        """Play button sound, then show punchline"""
        self.play_button_click()
        self.show_punchline()
    
    def next_joke_with_sound(self):
        """Play button sound, then go to next joke and play typing sound"""
        self.play_button_click()
        self.next_joke(play_typing=True)
    
    def quit_with_sound(self):
        """Play button sound, then quit app (with a short delay to let it play)"""
        self.play_button_click()
        self.root.after(160, self.root.quit)  # ~150-170ms matches button.mp3 demo sounds length

    def tell_joke(self, play_typing=False):
        """Select a random joke and display the setup. Optionally, play typing sound when revealing setup."""
        if not self.jokes:
            self.setup_label.config(text="No jokes available!", bg='#ffffff')
            return
        
        # Select random joke
        self.current_joke = random.choice(self.jokes)
        self.current_setup = self.current_joke['setup']
        self.current_punchline = self.current_joke['punchline']
        
        # Clear labels
        self.setup_label.config(text="")
        self.punchline_label.config(text="")
        
        # Cancel any ongoing animations
        if self.punchline_animation_id:
            self.root.after_cancel(self.punchline_animation_id)
            self.punchline_animation_id = None
        if self.setup_animation_id:
            self.root.after_cancel(self.setup_animation_id)
            self.setup_animation_id = None
        
        # Also, stop typing sound if punchline was revealing before (edge case)
        self._stop_typing_sound_after_1s()
        
        # Start progressive reveal for setup, and play typing if asked
        if play_typing:
            self.progressive_reveal_setup(self.current_setup, 0, play_typing=True)
        else:
            self.progressive_reveal_setup(self.current_setup, 0, play_typing=False)
        
        # Enable buttons
        self.show_punchline_btn.config(state='normal')
        self.next_joke_btn.config(state='normal')
    
    def show_punchline(self):
        """Display the punchline of the current joke with progressive reveal"""
        if self.current_punchline:
            # Play beep sound
            self.play_beep()
            # Start progressive reveal animation with typing sound
            self.progressive_reveal_punchline(self.current_punchline, 0)
        else:
            self.punchline_label.config(text="(No punchline available)")

    def progressive_reveal_setup(self, full_text, index, play_typing=False):
        """Reveal setup character by character. If play_typing, play typing sound with each char."""
        if index <= len(full_text):
            # Display substring up to current index
            self.setup_label.config(text=full_text[:index])
            # Play typing sound for each character (skip spaces/punct if you want)
            if play_typing and index > 0 and index <= len(full_text) and full_text[index - 1] not in ' \t\n.,!?;:':
                self.play_typing_sound()
            # Schedule next character reveal
            self.setup_animation_id = self.root.after(
                30, lambda: self.progressive_reveal_setup(full_text, index + 1, play_typing=play_typing)
            )
        else:
            self.setup_animation_id = None

    def progressive_reveal_punchline(self, full_text, index):
        """Reveal punchline character by character with typing sound"""
        if index <= len(full_text):
            # Display substring up to current index
            self.punchline_label.config(text=full_text[:index])
            # Play typing sound for each character (skip spaces and punctuation for subtlety)
            if index > 0 and index <= len(full_text) and full_text[index - 1] not in ' \t\n.,!?;:':
                self.play_typing_sound()
            # Schedule next character reveal
            self.punchline_animation_id = self.root.after(30, 
                lambda: self.progressive_reveal_punchline(full_text, index + 1))
        else:
            self.punchline_animation_id = None
            # Stop the typing sound after the final punchline character is shown (and 1s has elapsed)
            self._stop_typing_sound_after_1s()
    
    def play_button_click(self):
        """Play a short, clean UI sound for button clicks"""
        def _play():
            if not os.path.exists(self.button_click_sound):
                return
            
            # Try pygame first
            if HAS_PYGAME:
                try:
                    if self.button_sound_obj:
                        self.button_sound_obj.play()
                        return
                    else:
                        sound = pygame.mixer.Sound(self.button_click_sound)
                        sound.play()
                        return
                except Exception as e:
                    print(f"Pygame error: {e}")
            
            # Fallback: Use subprocess to play MP3 (Windows)
            if sys.platform == 'win32':
                try:
                    # Try using start command (Windows)
                    subprocess.Popen(['start', '/min', self.button_click_sound], 
                                   shell=True, stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                except Exception:
                    try:
                        # Alternative: use os.startfile
                        os.startfile(self.button_click_sound)
                    except Exception:
                        pass
        
        # Play in a separate thread to avoid blocking
        threading.Thread(target=_play, daemon=True).start()

    def play_typing_sound(self):
        """Play a subtle text-typing sound synchronized with character reveal
        But ensure the typing sound finishes/gets stopped after 1 second from the last play trigger.
        """
        def _play():
            if not os.path.exists(self.typing_sound):
                return

            # Only play typing sound if one isn't already 'ongoing'
            if not self.typing_sound_playing:
                self.typing_sound_playing = True

                # Try pygame first
                if HAS_PYGAME:
                    try:
                        if self.typing_sound_obj:
                            channel = self.typing_sound_obj.play()
                        else:
                            sound = pygame.mixer.Sound(self.typing_sound)
                            channel = sound.play()
                        # No need to block
                    except Exception as e:
                        print(f"Pygame error: {e}")
                # Fallback: Use subprocess to play MP3 (Windows)
                elif sys.platform == 'win32':
                    try:
                        subprocess.Popen(['start', '/min', self.typing_sound], 
                                       shell=True, stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL)
                    except Exception:
                        try:
                            os.startfile(self.typing_sound)
                        except Exception:
                            pass

                # After 1 second, stop the typing sound
                if self.typing_sound_end_timer:
                    self.root.after_cancel(self.typing_sound_end_timer)
                self.typing_sound_end_timer = self.root.after(1000, self._stop_typing_sound)
            else:
                # Typing sound is already playing, but reset the 1-second timer
                if self.typing_sound_end_timer:
                    self.root.after_cancel(self.typing_sound_end_timer)
                self.typing_sound_end_timer = self.root.after(1000, self._stop_typing_sound)

        # Start _play in background so as not to block UI
        threading.Thread(target=_play, daemon=True).start()

    def _stop_typing_sound(self):
        """Stop the typing sound, called after 1 second, or forcibly when next joke is shown."""
        # Stop pygame channel if possible
        if HAS_PYGAME:
            try:
                pygame.mixer.stop()
            except Exception:
                pass
        # Set state so it can be triggered again
        self.typing_sound_playing = False
        self.typing_sound_end_timer = None

    def _stop_typing_sound_after_1s(self):
        """Convenience: forcibly stop typing sound and clear any existing 1s timer."""
        if self.typing_sound_end_timer:
            self.root.after_cancel(self.typing_sound_end_timer)
            self.typing_sound_end_timer = None
        self._stop_typing_sound()

    def play_beep(self):
        """Play a beep sound when punchline appears (Windows only)"""
        if HAS_WINSOUND:
            try:
                winsound.Beep(800, 200)  # Frequency 800Hz, duration 200ms
            except Exception:
                pass  # Silently fail if beep doesn't work
    
    def add_hover_effect(self, button):
        """Add hover effect to a button using Enter/Leave events"""
        def on_enter(event):
            button.configure(cursor='hand2')
        
        def on_leave(event):
            button.configure(cursor='')
        
        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)
    
    def next_joke(self, play_typing=False):
        """Get another random joke. Optionally, play typing sound for the setup reveal."""
        # Also, stop typing sound so it doesn't linger when going to next joke.
        self._stop_typing_sound_after_1s()
        self.tell_joke(play_typing=play_typing)

def main():
    root = tk.Tk()
    app = AlexaJokeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

