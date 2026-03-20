import platform
import customtkinter as ctk
import tkinter as tk

# Core Logic
from app import PromptAnalyzer, PromptBuilder

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MacOSPromptImprover(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Prompt Improver")
        self.geometry("1160x760")
        self.minsize(900, 600)
        
        # ─── NATIVE MAC RENDERING HACKS ───
        # Simulate real glassmorphism by applying an alpha layer over
        # custom darkened backgrounds. Works on macOS and Windows natively.
        self.attributes('-alpha', 0.93)
        self.configure(fg_color="#0D0D11")  # ultra dark blue-black base
        
        # ─── Grid Configuration ───
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ─── Left panel (Input) ───
        # Glass frame simulation (transparent fg on Tkinter blends down to root)
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        
        self.left_header = ctk.CTkLabel(self.left_frame, text="✦  YOUR PROMPT", font=("SF Pro Display", 16, "bold"), text_color="#F2F2F7")
        self.left_header.pack(anchor="w", padx=20, pady=(20, 10))
        
        # Mode Selector
        self.mode_var = ctk.StringVar(value="General Mode")
        self.mode_selector = ctk.CTkSegmentedButton(
            self.left_frame, values=["General Mode", "Coding Mode"], 
            variable=self.mode_var, command=self._mode_changed,
            fg_color="#18181A",  # Semi-transparent dark backing
            selected_color="#363638", unselected_color="#18181A", selected_hover_color="#454545"
        )
        self.mode_selector.pack(fill="x", padx=20, pady=(0, 15))

        # Main Textbox (Frosty dark glass)
        self.input_text = ctk.CTkTextbox(
            self.left_frame, wrap="word", font=("SF Pro Text", 13), 
            fg_color="#1A1A1E", border_color="#2C2C30", border_width=1, corner_radius=12
        )
        self.input_text.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # Options Frame (Fully seamless to background)
        self.options_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.options_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.options_frame.grid_columnconfigure(0, weight=1)
        self.options_frame.grid_columnconfigure(1, weight=1)
        
        # Dropdowns (Styled for high contrast on the frosted glass)
        db_kwargs = {"fg_color": "#212126", "button_color": "#2C2C30", "button_hover_color": "#3A3A40", "corner_radius": 8}
        
        self.model_var = ctk.StringVar(value="Claude Sonnet 4.6 (Thinking)")
        self.model_dropdown = ctk.CTkOptionMenu(
            self.options_frame, variable=self.model_var,
            values=["Claude Sonnet 4.6 (Thinking)", "Claude Opus 4.6 (Thinking)", "Gemini 3.1 Pro (High)", "Gemini 3.1 Pro (Low)", "Gemini 3 Flash", "GPT-OSS 120B (Medium)"],
            **db_kwargs
        )
        self.model_dropdown.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="ew")
        
        self.audience_var = ctk.StringVar(value="General Audience")
        self.general_audiences = ["General Audience", "Business User", "Student", "Expert / Specialist"]
        self.coding_audiences = ["Junior Dev", "Senior Engineer", "Non-technical Stakeholder"]
        
        self.audience_dropdown = ctk.CTkOptionMenu(
            self.options_frame, variable=self.audience_var, 
            values=self.general_audiences, **db_kwargs
        )
        self.audience_dropdown.grid(row=0, column=1, padx=0, pady=10, sticky="ew")
        
        self.fmt_var = ctk.StringVar(value="Prose / Paragraphs")
        self.fmt_dropdown = ctk.CTkOptionMenu(
            self.options_frame, variable=self.fmt_var,
            values=["Prose / Paragraphs", "Bullet Points", "Markdown Table", "JSON", "Step-by-Step", "Code Snippet"],
            **db_kwargs
        )
        self.fmt_dropdown.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="ew")
        
        self.tone_var = ctk.StringVar(value="Direct & Concise")
        self.tone_dropdown = ctk.CTkOptionMenu(
            self.options_frame, variable=self.tone_var,
            values=["Direct & Concise", "Friendly & Helpful", "Academic / Formal", "Creative & Witty"],
            **db_kwargs
        )
        self.tone_dropdown.grid(row=1, column=1, padx=0, pady=10, sticky="ew")

        # Accent Button
        self.improve_btn = ctk.CTkButton(
            self.left_frame, text="Improve Prompt  ⌘↵", 
            height=40, font=("SF Pro Text", 14, "bold"), command=self._improve,
            corner_radius=12, fg_color="#3B82F6", hover_color="#2563EB"
        )
        self.improve_btn.pack(pady=(0, 20), padx=20, fill="x")

        # ─── Right panel (Output) ───
        # Using a deeper black to create depth separating left and right panes
        self.right_frame = ctk.CTkFrame(self, fg_color="#0A0A0C", corner_radius=0)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        
        self.right_header_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.right_header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.right_header = ctk.CTkLabel(self.right_header_frame, text="Improved Prompt", font=("SF Pro Display", 16, "bold"), text_color="#F2F2F7")
        self.right_header.pack(side="left")
        
        self.copy_btn = ctk.CTkButton(
            self.right_header_frame, text="Copy", width=60, height=28, 
            fg_color="#212124", hover_color="#2C2C30", command=self._copy,
            corner_radius=8
        )
        self.copy_btn.pack(side="right")

        self.output_text = ctk.CTkTextbox(
            self.right_frame, wrap="word", font=("Menlo", 13), state="disabled", 
            fg_color="transparent", border_width=0
        )
        self.output_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.improved_cache = ""

        # Keyboard shortcuts
        self.bind("<Control-Return>", lambda _: self._improve())
        self.bind("<Command-Return>",  lambda _: self._improve())
        
        # Init
        self._mode_changed("General Mode")

    def _mode_changed(self, value):
        if value == "Coding Mode":
            self.audience_dropdown.configure(values=self.coding_audiences)
            self.audience_var.set(self.coding_audiences[1])
            self.tone_dropdown.configure(values=["Direct & Concise", "Best Practices Focused", "Highly Technical", "Step-by-Step Tutorial"])
            self.tone_var.set("Best Practices Focused")
            if not self.input_text.get("1.0", "end").strip():
                self.input_text.insert("1.0", "Write a python script that...")
                self.input_text.tag_add("sel", "1.0", "end")
        else:
            self.audience_dropdown.configure(values=self.general_audiences)
            self.audience_var.set(self.general_audiences[0])
            self.tone_dropdown.configure(values=["Direct & Concise", "Friendly & Helpful", "Academic / Formal", "Creative & Witty"])
            self.tone_var.set("Direct & Concise")

    def _improve(self):
        raw = self.input_text.get("1.0", "end").strip()
        if not raw: return
        
        fmt_map = {
            "Prose / Paragraphs": "prose",
            "Bullet Points": "bullets",
            "Markdown Table": "table",
            "JSON": "json",
            "Step-by-Step": "steps",
            "Code Snippet": "code"
        }
        
        meta = {
            "model": self.model_var.get(),
            "audience": self.audience_var.get(),
            "output_fmt": fmt_map.get(self.fmt_var.get(), "prose"),
            "tone": self.tone_var.get()
        }
        
        meta["mode"] = "coding" if self.mode_var.get() == "Coding Mode" else "general"
        analysis = PromptAnalyzer().analyze(raw)
        result = PromptBuilder().build(raw, analysis, meta)
        
        self.improved_cache = result
        
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result)
        self.output_text.configure(state="disabled")
        
    def _copy(self):
        if not self.improved_cache:
            return
        self.clipboard_clear()
        self.clipboard_append(self.improved_cache)
        self.copy_btn.configure(text="Copied ✓", fg_color="#3dd68c", text_color="#1c1c1e")
        self.after(2000, lambda: self.copy_btn.configure(text="Copy", fg_color="#212124", text_color="#ffffff"))

if __name__ == "__main__":
    app = MacOSPromptImprover()
    app.mainloop()
