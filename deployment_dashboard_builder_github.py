import json
import os
import uuid
import webbrowser
import sys
import tkinter as tk
from dataclasses import dataclass, asdict, field
from datetime import datetime
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import List

APP_BG = "#0A0A0F"
PANEL_BG = "#11111A"
CARD_BG = "#14192A"
ALT_BG = "#0E1220"
TEXT_PRIMARY = "#E8ECF3"
TEXT_MUTED = "#94A0B8"
ACCENT = "#EB4BC6"
OUTLINE = "#262C3D"
SUCCESS = "#22C55E"
WARN = "#F59E0B"
DANGER = "#FF5A5F"
INFO = "#38BDF8"

STATUS_OPTIONS = ["Not Started", "In Progress", "Blocked", "Ready for Review", "Complete"]
MILESTONES = [
    "Rack Delivered",
    "Network Ready",
    "QuLSR Installed",
    "White Rabbit Validated",
    "Carina Configured",
    "Final Validation",
]


@dataclass
class LocationRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Location"
    customer: str = "Customer"
    address: str = ""
    engineer: str = ""
    status: str = "Not Started"
    progress: int = 0
    notes: str = ""
    blockers: str = ""
    next_steps: str = ""
    milestones: dict = field(default_factory=lambda: {m: False for m in MILESTONES})
    exports: List[str] = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class DashboardBuilder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Deployment Progress Dashboard Builder")
        self.geometry("1480x900")
        self.minsize(1200, 760)
        self.configure(bg=APP_BG)

        self.data_path = os.path.abspath("deployment_dashboard_data.json")
        self.html_path = os.path.abspath("deployment_dashboard_preview.html")

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self._configure_styles()

        self.dashboard_name_var = tk.StringVar(value="Deployment Support Dashboard")
        self.customer_group_var = tk.StringVar(value="Internal Deployment Team")
        self.search_var = tk.StringVar()
        self.status_filter_var = tk.StringVar(value="All")
        self.location_records: List[LocationRecord] = []
        self.location_tabs = {}
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()
        self.new_dashboard(seed=True)

    def _configure_styles(self):
        self.style.configure("Dark.TFrame", background=PANEL_BG)
        self.style.configure("Card.TFrame", background=CARD_BG)
        self.style.configure("Dark.TLabel", background=PANEL_BG, foreground=TEXT_PRIMARY)
        self.style.configure("Muted.TLabel", background=PANEL_BG, foreground=TEXT_MUTED)
        self.style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT_PRIMARY)
        self.style.configure("CardMuted.TLabel", background=CARD_BG, foreground=TEXT_MUTED)
        self.style.configure(
            "Tech.TButton",
            background="#181C2B",
            foreground=TEXT_PRIMARY,
            borderwidth=1,
            focusthickness=0,
            padding=8,
        )
        self.style.map("Tech.TButton", background=[("active", "#20263A"), ("pressed", "#161A27")])
        self.style.configure("Dark.TNotebook", background=APP_BG, borderwidth=0)
        self.style.configure(
            "Dark.TNotebook.Tab",
            background="#181C2B",
            foreground=TEXT_PRIMARY,
            padding=(16, 8),
            borderwidth=0,
        )
        self.style.map(
            "Dark.TNotebook.Tab",
            background=[("selected", ACCENT), ("active", "#22293E")],
            foreground=[("selected", "#FFFFFF")],
        )
        self.style.configure("Dark.TLabelframe", background=PANEL_BG, foreground=TEXT_PRIMARY, bordercolor=OUTLINE)
        self.style.configure("Dark.TLabelframe.Label", background=PANEL_BG, foreground=TEXT_PRIMARY)

    def _entry(self, parent, textvariable=None, width=None):
        return tk.Entry(
            parent,
            textvariable=textvariable,
            width=width,
            bg=ALT_BG,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            highlightthickness=1,
            highlightbackground=OUTLINE,
        )

    def _text(self, parent, height=4):
        return tk.Text(
            parent,
            height=height,
            bg=ALT_BG,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            wrap="word",
            highlightthickness=1,
            highlightbackground=OUTLINE,
        )

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self, style="Dark.TFrame", padding=(14, 12))
        top.grid(row=0, column=0, columnspan=2, sticky="nsew")
        for i in range(8):
            top.columnconfigure(i, weight=0)
        top.columnconfigure(2, weight=1)

        ttk.Label(top, text="Dashboard", style="Dark.TLabel").grid(row=0, column=0, sticky="w")
        self.dashboard_name_entry = self._entry(top, self.dashboard_name_var, width=34)
        self.dashboard_name_entry.grid(row=0, column=1, sticky="w", padx=(8, 10))
        self.dashboard_name_entry.bind("<FocusOut>", lambda _e: self.touch())

        ttk.Label(top, text="Team", style="Dark.TLabel").grid(row=0, column=2, sticky="e")
        self.customer_group_entry = self._entry(top, self.customer_group_var, width=28)
        self.customer_group_entry.grid(row=0, column=3, sticky="w", padx=(8, 14))
        self.customer_group_entry.bind("<FocusOut>", lambda _e: self.touch())

        ttk.Button(top, text="New", command=self.new_dashboard, style="Tech.TButton").grid(row=0, column=4, padx=4)
        ttk.Button(top, text="Save JSON", command=self.save_json, style="Tech.TButton").grid(row=0, column=5, padx=4)
        ttk.Button(top, text="Load JSON", command=self.load_json, style="Tech.TButton").grid(row=0, column=6, padx=4)
        ttk.Button(top, text="Export HTML", command=self.export_html, style="Tech.TButton").grid(row=0, column=7, padx=4)
        ttk.Button(top, text="Export GitHub Site", command=self.export_github_site, style="Tech.TButton").grid(row=0, column=8, padx=4)
        ttk.Button(top, text="Preview HTML", command=self.preview_html, style="Tech.TButton").grid(row=0, column=9, padx=(4, 0))

        left = ttk.Frame(self, style="Dark.TFrame", padding=(14, 10))
        left.grid(row=1, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(4, weight=1)
        self.left_panel = left

        ttk.Label(left, text="Locations", style="Dark.TLabel", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        search_entry = self._entry(left, self.search_var)
        search_entry.grid(row=1, column=0, sticky="ew", pady=(8, 8))
        search_entry.bind("<KeyRelease>", lambda _e: self.refresh_location_list())

        filter_row = ttk.Frame(left, style="Dark.TFrame")
        filter_row.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        filter_row.columnconfigure(1, weight=1)
        ttk.Label(filter_row, text="Status", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        status_filter = ttk.Combobox(filter_row, textvariable=self.status_filter_var, values=["All", *STATUS_OPTIONS], state="readonly")
        status_filter.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        status_filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh_location_list())

        button_row = ttk.Frame(left, style="Dark.TFrame")
        button_row.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        button_row.columnconfigure((0,1), weight=1)
        ttk.Button(button_row, text="Add Location", command=self.add_location, style="Tech.TButton").grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(button_row, text="Delete", command=self.delete_selected_location, style="Tech.TButton").grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.location_list = tk.Listbox(
            left,
            bg=ALT_BG,
            fg=TEXT_PRIMARY,
            selectbackground=ACCENT,
            selectforeground="#FFFFFF",
            relief="flat",
            highlightthickness=1,
            highlightbackground=OUTLINE,
            activestyle="none",
        )
        self.location_list.grid(row=4, column=0, sticky="nsew")
        self.location_list.bind("<<ListboxSelect>>", self.on_location_list_select)

        helper = (
            "GitHub-only note:\n"
            "This builder can export a single HTML dashboard that works great on GitHub Pages.\n"
            "Shared live editing does not persist on GitHub Pages alone; for that, you'd later add a backend.\n"
            "For now, use this to design the interface and preview the web version."
        )
        ttk.Label(left, text=helper, style="Muted.TLabel", justify="left").grid(row=5, column=0, sticky="ew", pady=(10, 0))

        main = ttk.Frame(self, style="Dark.TFrame", padding=(0, 10, 10, 10))
        main.grid(row=1, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        hero = ttk.Frame(main, style="Card.TFrame", padding=14)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        hero.columnconfigure(1, weight=1)
        tk.Label(hero, text="DEPLOYMENT OPS", bg=CARD_BG, fg=ACCENT, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.hero_title = tk.Label(hero, textvariable=self.dashboard_name_var, bg=CARD_BG, fg=TEXT_PRIMARY, font=("Segoe UI", 18, "bold"))
        self.hero_title.grid(row=1, column=0, sticky="w", pady=(4, 2))
        self.hero_subtitle = tk.Label(hero, textvariable=self.customer_group_var, bg=CARD_BG, fg=TEXT_MUTED, font=("Segoe UI", 10))
        self.hero_subtitle.grid(row=2, column=0, sticky="w")
        tk.Label(
            hero,
            text="Magenta-accent dashboard styled after your current app, with tabs, notes, milestone tracking, and HTML export preview.",
            bg=CARD_BG,
            fg=TEXT_MUTED,
            justify="right",
            wraplength=360,
        ).grid(row=0, column=1, rowspan=3, sticky="e")

        self.notebook = ttk.Notebook(main, style="Dark.TNotebook")
        self.notebook.grid(row=1, column=0, sticky="nsew")

        status_bar = ttk.Label(self, textvariable=self.status_var, style="Muted.TLabel", anchor="w")
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))

    def new_dashboard(self, seed=False):
        if not seed and not messagebox.askyesno("New Dashboard", "Clear the current dashboard and start fresh?", parent=self):
            return
        self.location_records = [
            LocationRecord(
                name="New York POP",
                customer="Acme Telecom",
                address="350 5th Ave, New York, NY",
                engineer="Alex",
                status="In Progress",
                progress=55,
                notes="Waiting on final fiber patch validation.",
                blockers="Customer maintenance window not confirmed.",
                next_steps="Validate White Rabbit timing and close rack checklist.",
                milestones={
                    "Rack Delivered": True,
                    "Network Ready": True,
                    "QuLSR Installed": True,
                    "White Rabbit Validated": False,
                    "Carina Configured": False,
                    "Final Validation": False,
                },
            ),
            LocationRecord(
                name="Chicago Core",
                customer="Acme Telecom",
                address="600 W Chicago Ave, Chicago, IL",
                engineer="Sam",
                status="Blocked",
                progress=35,
                notes="Router management VLAN mismatch discovered during turn-up.",
                blockers="Awaiting corrected switch template from networking.",
                next_steps="Apply updated VLAN template, rerun validation.",
            ),
        ]
        self.rebuild_tabs()
        self.refresh_location_list()
        self.notebook.select(0)
        self.status_var.set("Started a new dashboard")

    def touch(self):
        self.status_var.set("Changes staged in builder")

    def add_location(self):
        name = simpledialog.askstring("Add Location", "Location name:", parent=self)
        if not name:
            return
        record = LocationRecord(name=name.strip() or "New Location")
        self.location_records.append(record)
        self.rebuild_tabs(select_id=record.id)
        self.refresh_location_list()
        self.status_var.set(f"Added {record.name}")

    def delete_selected_location(self):
        tab_id = self.current_tab_id()
        if not tab_id:
            return
        record = self.get_record(tab_id)
        if not record:
            return
        if not messagebox.askyesno("Delete Location", f"Delete '{record.name}'?", parent=self):
            return
        self.location_records = [r for r in self.location_records if r.id != tab_id]
        if not self.location_records:
            self.location_records.append(LocationRecord())
        self.rebuild_tabs()
        self.refresh_location_list()
        self.status_var.set(f"Deleted {record.name}")

    def current_tab_id(self):
        current = self.notebook.select()
        if not current:
            return None
        for record_id, payload in self.location_tabs.items():
            if str(payload["frame"]) == current:
                return record_id
        return None

    def get_record(self, record_id):
        for record in self.location_records:
            if record.id == record_id:
                return record
        return None

    def rebuild_tabs(self, select_id=None):
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        self.location_tabs.clear()
        for record in self.location_records:
            frame = ttk.Frame(self.notebook, style="Dark.TFrame", padding=12)
            frame.columnconfigure(0, weight=3)
            frame.columnconfigure(1, weight=2)
            frame.rowconfigure(1, weight=1)
            self.notebook.add(frame, text=record.name)
            self.location_tabs[record.id] = self.build_location_tab(frame, record)
        target = select_id or (self.location_records[0].id if self.location_records else None)
        if target in self.location_tabs:
            self.notebook.select(self.location_tabs[target]["frame"])

    def build_location_tab(self, frame, record):
        top = ttk.Frame(frame, style="Card.TFrame", padding=14)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        for i in range(4):
            top.columnconfigure(i, weight=1)

        name_var = tk.StringVar(value=record.name)
        customer_var = tk.StringVar(value=record.customer)
        address_var = tk.StringVar(value=record.address)
        engineer_var = tk.StringVar(value=record.engineer)
        status_var = tk.StringVar(value=record.status)
        progress_var = tk.IntVar(value=record.progress)

        ttk.Label(top, text="Location", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        e1 = self._entry(top, name_var)
        e1.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(4, 8))

        ttk.Label(top, text="Customer", style="Card.TLabel").grid(row=0, column=1, sticky="w")
        e2 = self._entry(top, customer_var)
        e2.grid(row=1, column=1, sticky="ew", padx=8, pady=(4, 8))

        ttk.Label(top, text="Engineer", style="Card.TLabel").grid(row=0, column=2, sticky="w")
        e3 = self._entry(top, engineer_var)
        e3.grid(row=1, column=2, sticky="ew", padx=8, pady=(4, 8))

        ttk.Label(top, text="Status", style="Card.TLabel").grid(row=0, column=3, sticky="w")
        status_box = ttk.Combobox(top, textvariable=status_var, values=STATUS_OPTIONS, state="readonly")
        status_box.grid(row=1, column=3, sticky="ew", padx=(8, 0), pady=(4, 8))

        ttk.Label(top, text="Address", style="Card.TLabel").grid(row=2, column=0, sticky="w")
        e4 = self._entry(top, address_var)
        e4.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 8), pady=(4, 0))

        ttk.Label(top, text="Progress %", style="Card.TLabel").grid(row=2, column=2, sticky="w")
        progress_scale = tk.Scale(
            top,
            from_=0,
            to=100,
            orient="horizontal",
            variable=progress_var,
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            highlightthickness=0,
            troughcolor=ALT_BG,
            activebackground=ACCENT,
        )
        progress_scale.grid(row=3, column=2, columnspan=2, sticky="ew", padx=(8, 0))

        left = ttk.Frame(frame, style="Dark.TFrame")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)
        left.rowconfigure(3, weight=1)

        right = ttk.Frame(frame, style="Dark.TFrame")
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(3, weight=1)

        milestone_card = ttk.LabelFrame(left, text="Milestones", padding=12, style="Dark.TLabelframe")
        milestone_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        milestone_vars = {}
        for idx, milestone in enumerate(MILESTONES):
            var = tk.BooleanVar(value=record.milestones.get(milestone, False))
            milestone_vars[milestone] = var
            tk.Checkbutton(
                milestone_card,
                text=milestone,
                variable=var,
                bg=PANEL_BG,
                fg=TEXT_PRIMARY,
                activebackground=PANEL_BG,
                activeforeground=TEXT_PRIMARY,
                selectcolor=ALT_BG,
                highlightthickness=0,
                anchor="w",
            ).grid(row=idx, column=0, sticky="ew")

        notes_card = ttk.LabelFrame(left, text="Notes", padding=12, style="Dark.TLabelframe")
        notes_card.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        notes_card.columnconfigure(0, weight=1)
        notes_card.rowconfigure(1, weight=1)
        notes_text = self._text(notes_card, height=8)
        notes_text.grid(row=0, column=0, sticky="nsew")
        notes_text.insert("1.0", record.notes)

        next_card = ttk.LabelFrame(left, text="Next Steps", padding=12, style="Dark.TLabelframe")
        next_card.grid(row=2, column=0, sticky="nsew")
        next_card.columnconfigure(0, weight=1)
        next_text = self._text(next_card, height=5)
        next_text.grid(row=0, column=0, sticky="nsew")
        next_text.insert("1.0", record.next_steps)

        blocker_card = ttk.LabelFrame(right, text="Blockers", padding=12, style="Dark.TLabelframe")
        blocker_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        blocker_card.columnconfigure(0, weight=1)
        blocker_text = self._text(blocker_card, height=6)
        blocker_text.grid(row=0, column=0, sticky="nsew")
        blocker_text.insert("1.0", record.blockers)

        exports_card = ttk.LabelFrame(right, text="Interactive HTML Exports", padding=12, style="Dark.TLabelframe")
        exports_card.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        exports_card.columnconfigure(0, weight=1)
        exports_card.rowconfigure(0, weight=1)
        export_list = tk.Listbox(
            exports_card,
            bg=ALT_BG,
            fg=TEXT_PRIMARY,
            selectbackground=ACCENT,
            selectforeground="#FFFFFF",
            relief="flat",
            highlightthickness=1,
            highlightbackground=OUTLINE,
            activestyle="none",
            height=8,
        )
        export_list.grid(row=0, column=0, sticky="nsew")
        for path in record.exports:
            export_list.insert(tk.END, path)

        export_buttons = ttk.Frame(exports_card, style="Dark.TFrame")
        export_buttons.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        export_buttons.columnconfigure((0,1,2), weight=1)

        def add_export():
            files = filedialog.askopenfilenames(
                parent=self,
                title="Select interactive HTML exports",
                filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            )
            if not files:
                return
            for item in files:
                if item not in record.exports:
                    record.exports.append(item)
                    export_list.insert(tk.END, item)
            record.updated_at = datetime.now().isoformat(timespec="seconds")
            self.status_var.set(f"Attached {len(files)} export file(s) to {record.name}")

        def remove_export():
            sel = export_list.curselection()
            if not sel:
                return
            idx = sel[0]
            value = export_list.get(idx)
            export_list.delete(idx)
            record.exports = [x for x in record.exports if x != value]
            record.updated_at = datetime.now().isoformat(timespec="seconds")
            self.status_var.set("Removed export link")

        def open_export():
            sel = export_list.curselection()
            if not sel:
                return
            path = export_list.get(sel[0])
            if os.path.exists(path):
                webbrowser.open(f"file://{os.path.abspath(path)}")
            else:
                messagebox.showerror("Missing file", f"Could not find:\n{path}", parent=self)

        ttk.Button(export_buttons, text="Attach HTML", command=add_export, style="Tech.TButton").grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(export_buttons, text="Open", command=open_export, style="Tech.TButton").grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(export_buttons, text="Remove", command=remove_export, style="Tech.TButton").grid(row=0, column=2, sticky="ew", padx=(4, 0))

        footer = ttk.Frame(right, style="Dark.TFrame")
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        footer.columnconfigure(1, weight=1)
        ttk.Button(footer, text="Apply Tab Changes", command=lambda rid=record.id: self.sync_tab_to_record(rid), style="Tech.TButton").grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(footer, text="Duplicate Location", command=lambda rid=record.id: self.duplicate_location(rid), style="Tech.TButton").grid(row=0, column=1, sticky="ew", padx=(4, 0))

        updated_label = tk.Label(right, text=f"Updated: {record.updated_at}", bg=PANEL_BG, fg=TEXT_MUTED, anchor="w")
        updated_label.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        for widget in (e1, e2, e3, e4, status_box, progress_scale, notes_text, blocker_text, next_text):
            if isinstance(widget, tk.Text):
                widget.bind("<FocusOut>", lambda _e, rid=record.id: self.sync_tab_to_record(rid, quiet=True))
            else:
                widget.bind("<FocusOut>", lambda _e, rid=record.id: self.sync_tab_to_record(rid, quiet=True))
        status_box.bind("<<ComboboxSelected>>", lambda _e, rid=record.id: self.sync_tab_to_record(rid, quiet=True))

        return {
            "frame": frame,
            "name_var": name_var,
            "customer_var": customer_var,
            "address_var": address_var,
            "engineer_var": engineer_var,
            "status_var": status_var,
            "progress_var": progress_var,
            "milestone_vars": milestone_vars,
            "notes_text": notes_text,
            "blocker_text": blocker_text,
            "next_text": next_text,
            "export_list": export_list,
            "updated_label": updated_label,
        }

    def sync_tab_to_record(self, record_id, quiet=False):
        payload = self.location_tabs.get(record_id)
        record = self.get_record(record_id)
        if not payload or not record:
            return
        record.name = payload["name_var"].get().strip() or "New Location"
        record.customer = payload["customer_var"].get().strip()
        record.address = payload["address_var"].get().strip()
        record.engineer = payload["engineer_var"].get().strip()
        record.status = payload["status_var"].get().strip() or "Not Started"
        try:
            record.progress = int(payload["progress_var"].get())
        except Exception:
            record.progress = 0
        record.notes = payload["notes_text"].get("1.0", tk.END).strip()
        record.blockers = payload["blocker_text"].get("1.0", tk.END).strip()
        record.next_steps = payload["next_text"].get("1.0", tk.END).strip()
        record.milestones = {name: var.get() for name, var in payload["milestone_vars"].items()}
        record.updated_at = datetime.now().isoformat(timespec="seconds")
        payload["updated_label"].configure(text=f"Updated: {record.updated_at}")
        tab_index = self.notebook.index(payload["frame"])
        self.notebook.tab(tab_index, text=record.name)
        self.refresh_location_list()
        if not quiet:
            self.status_var.set(f"Saved changes for {record.name}")

    def duplicate_location(self, record_id):
        self.sync_tab_to_record(record_id, quiet=True)
        record = self.get_record(record_id)
        if not record:
            return
        clone = LocationRecord(**json.loads(json.dumps(asdict(record))))
        clone.id = str(uuid.uuid4())
        clone.name = f"{record.name} Copy"
        clone.updated_at = datetime.now().isoformat(timespec="seconds")
        self.location_records.append(clone)
        self.rebuild_tabs(select_id=clone.id)
        self.refresh_location_list()
        self.status_var.set(f"Duplicated {record.name}")

    def refresh_location_list(self):
        self.location_list.delete(0, tk.END)
        query = self.search_var.get().strip().lower()
        status_filter = self.status_filter_var.get().strip()
        for record in self.location_records:
            if query and query not in f"{record.name} {record.customer} {record.engineer}".lower():
                continue
            if status_filter not in ("", "All") and record.status != status_filter:
                continue
            self.location_list.insert(tk.END, f"{record.name}  •  {record.status}  •  {record.progress}%")

    def on_location_list_select(self, _event):
        sel = self.location_list.curselection()
        if not sel:
            return
        visible = []
        query = self.search_var.get().strip().lower()
        status_filter = self.status_filter_var.get().strip()
        for record in self.location_records:
            if query and query not in f"{record.name} {record.customer} {record.engineer}".lower():
                continue
            if status_filter not in ("", "All") and record.status != status_filter:
                continue
            visible.append(record)
        idx = sel[0]
        if idx < len(visible) and visible[idx].id in self.location_tabs:
            self.notebook.select(self.location_tabs[visible[idx].id]["frame"])

    def serialize(self):
        for record_id in list(self.location_tabs.keys()):
            self.sync_tab_to_record(record_id, quiet=True)
        return {
            "dashboard_name": self.dashboard_name_var.get().strip() or "Deployment Support Dashboard",
            "customer_group": self.customer_group_var.get().strip() or "Internal Deployment Team",
            "locations": [asdict(record) for record in self.location_records],
        }

    def save_json(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save dashboard data",
            defaultextension=".json",
            initialfile=os.path.basename(self.data_path),
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.serialize(), f, indent=2)
        self.data_path = path
        self.status_var.set(f"Saved data to {os.path.basename(path)}")

    def load_json(self):
        path = filedialog.askopenfilename(parent=self, title="Load dashboard data", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.dashboard_name_var.set(data.get("dashboard_name") or "Deployment Support Dashboard")
        self.customer_group_var.set(data.get("customer_group") or "Internal Deployment Team")
        self.location_records = []
        for item in data.get("locations", []):
            item.setdefault("milestones", {m: False for m in MILESTONES})
            item.setdefault("exports", [])
            item.setdefault("updated_at", datetime.now().isoformat(timespec="seconds"))
            self.location_records.append(LocationRecord(**item))
        if not self.location_records:
            self.location_records.append(LocationRecord())
        self.data_path = path
        self.rebuild_tabs()
        self.refresh_location_list()
        self.status_var.set(f"Loaded {os.path.basename(path)}")


    def slugify(self, value):
        value = (value or "").strip().lower()
        out = []
        last_dash = False
        for ch in value:
            if ch.isalnum():
                out.append(ch)
                last_dash = False
            elif not last_dash:
                out.append("-")
                last_dash = True
        slug = "".join(out).strip("-")
        return slug or "location"

    def export_github_site(self):
        base_dir = filedialog.askdirectory(parent=self, title="Choose folder for GitHub-ready site export")
        if not base_dir:
            return

        data = self.serialize()
        base_path = os.path.abspath(base_dir)
        exports_root = os.path.join(base_path, "exports")
        os.makedirs(exports_root, exist_ok=True)

        github_data = json.loads(json.dumps(data))
        used_names = set()
        for loc in github_data.get("locations", []):
            loc_slug = self.slugify(loc.get("name") or "location")
            loc_dir = os.path.join(exports_root, loc_slug)
            os.makedirs(loc_dir, exist_ok=True)
            rewritten = []
            for original in loc.get("exports", []):
                if not original:
                    continue
                if os.path.isfile(original):
                    filename = os.path.basename(original)
                    stem, ext = os.path.splitext(filename)
                    candidate = filename
                    counter = 2
                    while os.path.join(loc_slug, candidate) in used_names:
                        candidate = f"{stem}-{counter}{ext}"
                        counter += 1
                    used_names.add(os.path.join(loc_slug, candidate))
                    dest = os.path.join(loc_dir, candidate)
                    try:
                        import shutil
                        shutil.copy2(original, dest)
                        rewritten.append(f"exports/{loc_slug}/{candidate}")
                    except OSError:
                        rewritten.append(original)
                else:
                    rewritten.append(original)
            loc["exports"] = rewritten

        with open(os.path.join(base_path, "index.html"), "w", encoding="utf-8") as f:
            f.write(self.build_html(github_data))

        with open(os.path.join(base_path, "dashboard_data.json"), "w", encoding="utf-8") as f:
            json.dump(github_data, f, indent=2)

        with open(os.path.join(base_path, ".nojekyll"), "w", encoding="utf-8") as f:
            f.write("")

        readme = f"""# {github_data.get('dashboard_name', 'Deployment Support Dashboard')}

This folder is ready to upload to a GitHub repository and publish with GitHub Pages.

## Files
- `index.html` - main dashboard page
- `dashboard_data.json` - exported data snapshot
- `exports/` - copied interactive HTML exports attached to locations
- `.nojekyll` - keeps GitHub Pages from running Jekyll processing

## Publish
1. Create or open your GitHub repository.
2. Upload everything in this folder to the repo root.
3. On GitHub, open **Settings -> Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**.
5. Select your main branch and the **/(root)** folder.
6. Save, then wait for the Pages URL to appear.

Anyone with the URL can open the dashboard in a browser.
"""
        with open(os.path.join(base_path, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme)

        self.status_var.set(f"Exported GitHub-ready site to {base_path}")
        if messagebox.askyesno("Open folder?", "GitHub-ready site exported. Open the folder now?", parent=self):
            try:
                if os.name == "nt":
                    os.startfile(base_path)
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.Popen(["open", base_path])
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", base_path])
            except Exception:
                pass

    def export_html(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export dashboard HTML",
            defaultextension=".html",
            initialfile=os.path.basename(self.html_path),
            filetypes=[("HTML files", "*.html")],
        )
        if not path:
            return
        data = self.serialize()
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.build_html(data))
        self.html_path = path
        self.status_var.set(f"Exported HTML to {os.path.basename(path)}")

    def preview_html(self):
        data = self.serialize()
        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(self.build_html(data))
        webbrowser.open(f"file://{self.html_path}")
        self.status_var.set("Opened HTML preview in browser")

    def build_html(self, data):
        payload = json.dumps(data).replace("</script>", "<\\/script>")
        return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{data["dashboard_name"]}}</title>
<style>
:root {{
  --bg:#0A0A0F; --panel:#11111A; --card:#14192A; --alt:#0E1220; --text:#E8ECF3; --muted:#94A0B8;
  --accent:#EB4BC6; --outline:#262C3D; --green:#22C55E; --orange:#F59E0B; --red:#FF5A5F; --blue:#38BDF8;
}}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; min-height:100%; background:var(--bg); color:var(--text); font-family:Inter,Segoe UI,Arial,sans-serif; }}
body {{ padding:18px; }}
.header {{ display:grid; grid-template-columns:1fr auto; gap:16px; background:linear-gradient(180deg,#151725,#0e1018); border:1px solid var(--outline); border-radius:20px; padding:18px; margin-bottom:16px; }}
.eyebrow {{ color:var(--accent); font-size:12px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }}
.h1 {{ font-size:30px; font-weight:800; margin:8px 0 4px; }}
.sub {{ color:var(--muted); }}
.actions {{ display:flex; gap:10px; flex-wrap:wrap; align-items:flex-start; justify-content:flex-end; }}
button,.pill {{ border:1px solid var(--outline); background:#181C2B; color:var(--text); border-radius:12px; padding:10px 14px; cursor:pointer; }}
button:hover {{ background:#20263A; }}
.layout {{ display:grid; grid-template-columns:280px 1fr 340px; gap:16px; }}
.panel, .card {{ background:var(--panel); border:1px solid var(--outline); border-radius:18px; }}
.panel {{ padding:14px; }}
.card {{ padding:14px; background:var(--card); }}
.sidebar h3, .details h3 {{ margin:0 0 12px; font-size:16px; }}
.input, textarea, select {{ width:100%; background:var(--alt); color:var(--text); border:1px solid var(--outline); border-radius:12px; padding:10px 12px; }}
textarea {{ min-height:120px; resize:vertical; }}
.location-list {{ display:flex; flex-direction:column; gap:10px; margin-top:12px; max-height:70vh; overflow:auto; }}
.location-item {{ padding:12px; border:1px solid var(--outline); border-radius:14px; background:#0f1320; cursor:pointer; }}
.location-item.active {{ border-color:var(--accent); box-shadow:0 0 0 1px var(--accent) inset; }}
.location-name {{ font-weight:700; margin-bottom:4px; }}
.location-meta {{ color:var(--muted); font-size:13px; }}
.workspace {{ display:flex; flex-direction:column; gap:16px; }}
.tabbar {{ display:flex; gap:10px; flex-wrap:wrap; }}
.tab {{ padding:10px 14px; border-radius:999px; background:#171b29; border:1px solid var(--outline); cursor:pointer; }}
.tab.active {{ background:var(--accent); color:white; border-color:var(--accent); }}
.grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
.metric {{ background:var(--card); border:1px solid var(--outline); border-radius:18px; padding:14px; }}
.metric-label {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.08em; }}
.metric-value {{ font-size:28px; font-weight:800; margin-top:8px; }}
.section {{ background:var(--panel); border:1px solid var(--outline); border-radius:18px; padding:14px; }}
.section h4 {{ margin:0 0 12px; font-size:16px; }}
.two-col {{ display:grid; grid-template-columns:1.3fr 1fr; gap:16px; }}
.three {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }}
.checks {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
.check {{ background:#0f1320; border:1px solid var(--outline); border-radius:14px; padding:10px 12px; }}
.progress {{ height:12px; background:#0f1320; border:1px solid var(--outline); border-radius:999px; overflow:hidden; }}
.progress > span {{ display:block; height:100%; background:linear-gradient(90deg,var(--accent),#ff7fd9); }}
.exports {{ display:flex; flex-direction:column; gap:10px; }}
.export-chip {{ border:1px solid var(--outline); border-radius:12px; padding:10px; background:#0f1320; font-size:13px; word-break:break-all; }}
.dropzone {{ border:1px dashed var(--accent); border-radius:16px; padding:20px; text-align:center; color:var(--muted); background:rgba(235,75,198,.06); }}
.preview-frame {{ width:100%; min-height:420px; border:1px solid var(--outline); border-radius:14px; background:white; }}
.hidden {{ display:none !important; }}
.note {{ color:var(--muted); font-size:13px; line-height:1.45; }}
@media (max-width:1200px) {{ .layout{{grid-template-columns:1fr;}} .two-col,.three,.grid{{grid-template-columns:1fr;}} }}
</style>
</head>
<body>
<script id="dashboard-data" type="application/json">{payload}</script>
<div class="header">
  <div>
    <div class="eyebrow">Deployment Ops</div>
    <div class="h1" id="dashboard-title"></div>
    <div class="sub" id="dashboard-team"></div>
  </div>
  <div class="actions">
    <button id="download-html">Download Edited HTML</button>
    <button id="download-json">Download JSON Snapshot</button>
    <span class="pill">GitHub Pages friendly • browser edits stay local to each viewer</span>
  </div>
</div>
<div class="layout">
  <aside class="panel sidebar">
    <h3>Locations</h3>
    <input class="input" id="location-search" placeholder="Search locations, customers, engineers">
    <div class="location-list" id="location-list"></div>
  </aside>
  <main class="workspace">
    <div class="tabbar" id="tabbar"></div>
    <div class="grid" id="metrics"></div>
    <div class="two-col">
      <section class="section">
        <h4>Deployment Overview</h4>
        <div class="three">
          <div>
            <div class="note">Customer</div>
            <input class="input editable" id="customer">
          </div>
          <div>
            <div class="note">Engineer</div>
            <input class="input editable" id="engineer">
          </div>
          <div>
            <div class="note">Status</div>
            <select class="editable" id="status"></select>
          </div>
        </div>
        <div style="margin-top:12px">
          <div class="note">Address</div>
          <input class="input editable" id="address">
        </div>
        <div style="margin-top:12px">
          <div class="note">Progress</div>
          <div class="progress"><span id="progress-bar"></span></div>
          <input class="editable" type="range" min="0" max="100" id="progress-range" style="width:100%; margin-top:10px">
          <div class="note" id="progress-text"></div>
        </div>
      </section>
      <section class="section">
        <h4>Milestones</h4>
        <div class="checks" id="milestones"></div>
      </section>
    </div>
    <div class="two-col">
      <section class="section">
        <h4>Notes</h4>
        <textarea class="editable" id="notes"></textarea>
      </section>
      <section class="section">
        <h4>Blockers</h4>
        <textarea class="editable" id="blockers"></textarea>
      </section>
    </div>
    <section class="section">
      <h4>Next Steps</h4>
      <textarea class="editable" id="next-steps"></textarea>
    </section>
  </main>
  <aside class="panel details">
    <h3>Interactive HTML Documents</h3>
    <div class="exports" id="exports"></div>
    <div style="height:12px"></div>
    <div class="dropzone" id="dropzone">
      Drag an exported HTML file here to preview it in-browser.<br>
      <span class="note">This preview is local to your browser session.</span>
    </div>
    <input type="file" id="html-file" accept=".html,text/html" class="hidden">
    <div style="height:12px"></div>
    <iframe class="preview-frame" id="preview-frame" sandbox="allow-scripts allow-same-origin"></iframe>
  </aside>
</div>
<script>
const raw = JSON.parse(document.getElementById('dashboard-data').textContent);
const storageKey = 'deployment-support-dashboard:' + location.pathname;
const saved = localStorage.getItem(storageKey);
const data = saved ? JSON.parse(saved) : raw;
const statuses = {json.dumps(STATUS_OPTIONS)};
let activeIndex = 0;

const titleEl = document.getElementById('dashboard-title');
const teamEl = document.getElementById('dashboard-team');
const tabbar = document.getElementById('tabbar');
const locationList = document.getElementById('location-list');
const metrics = document.getElementById('metrics');
const customerEl = document.getElementById('customer');
const engineerEl = document.getElementById('engineer');
const statusEl = document.getElementById('status');
const addressEl = document.getElementById('address');
const progressRange = document.getElementById('progress-range');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const milestonesEl = document.getElementById('milestones');
const notesEl = document.getElementById('notes');
const blockersEl = document.getElementById('blockers');
const nextStepsEl = document.getElementById('next-steps');
const exportsEl = document.getElementById('exports');
const searchEl = document.getElementById('location-search');
const previewFrame = document.getElementById('preview-frame');
const htmlFile = document.getElementById('html-file');
const dropzone = document.getElementById('dropzone');

titleEl.textContent = data.dashboard_name || 'Deployment Support Dashboard';
teamEl.textContent = data.customer_group || 'Internal Deployment Team';
statusEl.innerHTML = statuses.map(s => `<option>${{s}}</option>`).join('');

function persist() {{
  localStorage.setItem(storageKey, JSON.stringify(data));
}}

function current() {{
  return data.locations[activeIndex];
}}

function renderMetrics(loc) {{
  const completed = Object.values(loc.milestones || {{}}).filter(Boolean).length;
  const openExports = (loc.exports || []).length;
  metrics.innerHTML = `
    <div class="metric"><div class="metric-label">Status</div><div class="metric-value">${{loc.status}}</div></div>
    <div class="metric"><div class="metric-label">Progress</div><div class="metric-value">${{loc.progress}}%</div></div>
    <div class="metric"><div class="metric-label">Milestones Done</div><div class="metric-value">${{completed}} / ${{Object.keys(loc.milestones || {{}}).length}}</div></div>
    <div class="metric"><div class="metric-label">Exports</div><div class="metric-value">${{openExports}}</div></div>`;
}}

function renderTabs() {{
  const query = (searchEl.value || '').toLowerCase().trim();
  tabbar.innerHTML = '';
  locationList.innerHTML = '';
  data.locations.forEach((loc, i) => {{
    const hay = `${{loc.name}} ${{loc.customer}} ${{loc.engineer}}`.toLowerCase();
    if (query && !hay.includes(query)) return;
    const tab = document.createElement('button');
    tab.className = 'tab' + (i === activeIndex ? ' active' : '');
    tab.textContent = loc.name;
    tab.onclick = () => {{ activeIndex = i; render(); }};
    tabbar.appendChild(tab);

    const item = document.createElement('div');
    item.className = 'location-item' + (i === activeIndex ? ' active' : '');
    item.innerHTML = `<div class="location-name">${{loc.name}}</div><div class="location-meta">${{loc.status}} • ${{loc.progress}}% • ${{loc.engineer || 'Unassigned'}}</div>`;
    item.onclick = () => {{ activeIndex = i; render(); }};
    locationList.appendChild(item);
  }});
}}

function renderMilestones(loc) {{
  milestonesEl.innerHTML = '';
  Object.entries(loc.milestones || {{}}).forEach(([name, value]) => {{
    const wrap = document.createElement('label');
    wrap.className = 'check';
    wrap.innerHTML = `<input type="checkbox" data-name="${{name}}" ${{value ? 'checked' : ''}}> ${{name}}`;
    milestonesEl.appendChild(wrap);
  }});
  milestonesEl.querySelectorAll('input').forEach(input => {{
    input.addEventListener('change', () => {{
      current().milestones[input.dataset.name] = input.checked;
      persist();
      renderMetrics(current());
    }});
  }});
}}

function renderExports(loc) {{
  exportsEl.innerHTML = '';
  if (!loc.exports || !loc.exports.length) {{
    exportsEl.innerHTML = '<div class="note">No attached export paths yet. In the local Python builder, attach your generated HTML files. Use Export GitHub Site to copy them into a publishable folder.</div>';
    return;
  }}
  loc.exports.forEach(path => {{
    const div = document.createElement('div');
    div.className = 'export-chip';

    const label = document.createElement('div');
    label.textContent = path;
    div.appendChild(label);

    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.gap = '8px';
    actions.style.marginTop = '8px';

    const isWebPath = !/^[a-zA-Z]:\|^\/|^file:\/\//.test(path);
    if (isWebPath) {{
      const previewBtn = document.createElement('button');
      previewBtn.textContent = 'Preview';
      previewBtn.onclick = () => {{ previewFrame.src = encodeURI(path); }};
      actions.appendChild(previewBtn);

      const link = document.createElement('a');
      link.href = path;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = 'Open tab';
      link.style.color = 'var(--blue)';
      link.style.alignSelf = 'center';
      actions.appendChild(link);
    }} else {{
      const note = document.createElement('div');
      note.className = 'note';
      note.textContent = 'Local file path. Publish with Export GitHub Site to make this open from the web.';
      actions.appendChild(note);
    }}
    div.appendChild(actions);
    exportsEl.appendChild(div);
  }});
}}

function render() {{
  if (!data.locations.length) return;
  const loc = current();
  renderTabs();
  renderMetrics(loc);
  customerEl.value = loc.customer || '';
  engineerEl.value = loc.engineer || '';
  statusEl.value = loc.status || statuses[0];
  addressEl.value = loc.address || '';
  progressRange.value = loc.progress || 0;
  progressBar.style.width = `${{loc.progress || 0}}%`;
  progressText.textContent = `${{loc.progress || 0}}% complete`;
  notesEl.value = loc.notes || '';
  blockersEl.value = loc.blockers || '';
  nextStepsEl.value = loc.next_steps || '';
  renderMilestones(loc);
  renderExports(loc);
}}

function bindEditable(el, updater) {{
  el.addEventListener('input', () => {{ updater(el.value); persist(); renderMetrics(current()); renderTabs(); }});
}}

bindEditable(customerEl, v => current().customer = v);
bindEditable(engineerEl, v => current().engineer = v);
bindEditable(addressEl, v => current().address = v);
bindEditable(statusEl, v => current().status = v);
bindEditable(notesEl, v => current().notes = v);
bindEditable(blockersEl, v => current().blockers = v);
bindEditable(nextStepsEl, v => current().next_steps = v);
progressRange.addEventListener('input', () => {{ current().progress = Number(progressRange.value || 0); persist(); render(); }});
searchEl.addEventListener('input', renderTabs);

document.getElementById('download-json').addEventListener('click', () => {{
  const blob = new Blob([JSON.stringify(data, null, 2)], {{type:'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'deployment_dashboard_snapshot.json';
  a.click();
  URL.revokeObjectURL(a.href);
}});

document.getElementById('download-html').addEventListener('click', () => {{
  persist();
  const html = document.documentElement.outerHTML.replace(rawString(), JSON.stringify(data).replace('</script>', '<\\/script>'));
  const blob = new Blob([html], {{type:'text/html'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'deployment_dashboard_edited.html';
  a.click();
  URL.revokeObjectURL(a.href);
}});

function rawString() {{
  return document.getElementById('dashboard-data').textContent;
}}

htmlFile.addEventListener('change', ev => {{
  const file = ev.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {{ previewFrame.srcdoc = e.target.result; }};
  reader.readAsText(file);
}});

dropzone.addEventListener('click', () => htmlFile.click());
['dragenter','dragover'].forEach(evt => dropzone.addEventListener(evt, e => {{ e.preventDefault(); dropzone.style.borderColor = '#fff'; }}));
['dragleave','drop'].forEach(evt => dropzone.addEventListener(evt, e => {{ e.preventDefault(); dropzone.style.borderColor = 'var(--accent)'; }}));
dropzone.addEventListener('drop', e => {{
  const file = e.dataTransfer.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {{ previewFrame.srcdoc = ev.target.result; }};
  reader.readAsText(file);
}});

render();
</script>
</body>
</html>'''


if __name__ == "__main__":
    app = DashboardBuilder()
    app.mainloop()
