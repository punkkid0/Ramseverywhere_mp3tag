import customtkinter as ctk


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, config_summary: str):
        super().__init__(master)
        self.title("Settings")
        self.geometry("480x320")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="Configuration",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 8))

        ctk.CTkLabel(
            self,
            text="Edit config.yaml in your project or music folder to change:",
            anchor="w",
            justify="left",
        ).pack(anchor="w", padx=20)

        textbox = ctk.CTkTextbox(self, height=150)
        textbox.pack(fill="both", expand=True, padx=20, pady=12)
        textbox.insert("1.0", config_summary)
        textbox.configure(state="disabled")

        ctk.CTkButton(self, text="Close", command=self.destroy).pack(pady=(0, 20))