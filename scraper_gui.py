"""
Modern Tkinter UI for Google Serper Scraper
===========================================
Professional lead generation interface with dynamic category/city selector,
live data streaming, thread-safe operations, real-time statistics, search & export.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import queue
import threading
import subprocess
import webbrowser

from scraper_core import (
    DEFAULT_API_KEY,
    POPULAR_CATEGORIES,
    PRESET_GHAZIABAD_SCHOOLS,
    PRESET_AYODHYA_HOSPITALS,
    generate_smart_queries,
    ScraperEngine
)

# ─────────────────────────────────────────────
# COLOR PALETTE (Modern Slate & Dark Theme)
# ─────────────────────────────────────────────
THEME = {
    "bg_dark":      "#181825",
    "bg_card":      "#1e1e2e",
    "bg_card_alt":  "#252538",
    "bg_input":     "#313244",
    "border":       "#45475a",
    "fg_text":      "#cdd6f4",
    "fg_subtext":   "#a6adc8",
    "accent_blue":  "#89b4fa",
    "accent_green": "#a6e3a1",
    "accent_amber": "#f9e2af",
    "accent_red":   "#f38ba8",
    "accent_purple":"#cba6f7",
    "btn_start":    "#22c55e",
    "btn_pause":    "#eab308",
    "btn_stop":     "#ef4444",
    "console_bg":   "#11111b",
    "console_fg":   "#cdd6f4",
}


class ScraperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Lead Scraper — Custom Business & Location Extractor")
        self.geometry("1220x860")
        self.minsize(1020, 720)
        self.configure(bg=THEME["bg_dark"])

        # Thread queue & engine
        self.event_queue = queue.Queue()
        self.engine: ScraperEngine = None
        self.worker_thread = None
        self.all_table_data = []

        # State tracking
        self.is_paused = False
        self.is_scraping = False

        # Current working dir
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self._setup_styles()
        self._build_ui()
        self._apply_smart_queries()  # Default init with initial values
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Start processing event queue
        self.after(50, self._process_queue)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Global Treeview style
        style.configure(
            "Treeview",
            background=THEME["bg_card"],
            foreground=THEME["fg_text"],
            fieldbackground=THEME["bg_card"],
            rowheight=28,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Treeview.Heading",
            background=THEME["bg_card_alt"],
            foreground=THEME["accent_blue"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=6
        )
        style.map(
            "Treeview",
            background=[("selected", THEME["bg_input"])],
            foreground=[("selected", "#ffffff")]
        )

        # Notebook tabs
        style.configure(
            "TNotebook",
            background=THEME["bg_dark"],
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            background=THEME["bg_card"],
            foreground=THEME["fg_subtext"],
            padding=[16, 8],
            font=("Segoe UI", 10, "bold")
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", THEME["bg_card_alt"])],
            foreground=[("selected", THEME["accent_blue"])]
        )

        # Progressbar
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor=THEME["bg_input"],
            background=THEME["accent_blue"],
            bordercolor=THEME["bg_card"],
            thickness=14
        )

    def _build_ui(self):
        # 1. Header Frame
        header = tk.Frame(self, bg=THEME["bg_card"], height=64, padx=20, pady=10)
        header.pack(fill="x", side="top")

        title_box = tk.Frame(header, bg=THEME["bg_card"])
        title_box.pack(side="left")

        lbl_title = tk.Label(
            title_box,
            text="⚡ Smart Lead & Business Data Scraper",
            font=("Segoe UI", 15, "bold"),
            fg=THEME["fg_text"],
            bg=THEME["bg_card"]
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            title_box,
            text="Custom Business & City Targeting • Serper Places & Search APIs • Phone • Email • CSV Auto-Export",
            font=("Segoe UI", 9),
            fg=THEME["fg_subtext"],
            bg=THEME["bg_card"]
        )
        lbl_sub.pack(anchor="w")

        # Status badge in header
        self.lbl_status = tk.Label(
            header,
            text="● IDLE",
            font=("Segoe UI", 10, "bold"),
            fg=THEME["accent_blue"],
            bg=THEME["bg_input"],
            padx=14,
            pady=6,
            relief="flat"
        )
        self.lbl_status.pack(side="right")

        # 2. Main Container
        main_container = tk.Frame(self, bg=THEME["bg_dark"], padx=15, pady=10)
        main_container.pack(fill="both", expand=True)

        # 3. Target Configuration Card (Category, Location, API Key, Filename)
        self._build_targeting_card(main_container)

        # 4. KPI Summary Cards
        self._build_kpi_cards(main_container)

        # 5. Notebook (Tabs: Data Table, Console Log, Query Editor)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True, pady=(10, 0))

        # Tab 1: Live Results Table
        self.tab_table = tk.Frame(self.notebook, bg=THEME["bg_card"])
        self.notebook.add(self.tab_table, text="  📊 Live Records (0)  ")
        self._build_table_tab(self.tab_table)

        # Tab 2: Console Logs
        self.tab_logs = tk.Frame(self.notebook, bg=THEME["bg_card"])
        self.notebook.add(self.tab_logs, text="  📟 Real-time Terminal  ")
        self._build_logs_tab(self.tab_logs)

        # Tab 3: Query Configuration
        self.tab_queries = tk.Frame(self.notebook, bg=THEME["bg_card"])
        self.notebook.add(self.tab_queries, text="  ⚙️ Query Editor  ")
        self._build_queries_tab(self.tab_queries)

    def _build_targeting_card(self, parent):
        card = tk.Frame(parent, bg=THEME["bg_card"], padx=15, pady=12, relief="flat")
        card.pack(fill="x", pady=(0, 10))

        # ─── SECTION 1: WHAT TO SCRAPE (Category + City) ───
        row_target = tk.Frame(card, bg=THEME["bg_card"])
        row_target.pack(fill="x", pady=(0, 8))

        # Business / Data Type Dropdown
        tk.Label(row_target, text="1. Business / Data Type:", font=("Segoe UI", 9, "bold"), fg=THEME["accent_blue"], bg=THEME["bg_card"]).pack(side="left", padx=(0, 6))
        self.category_var = tk.StringVar(value="Schools & Colleges")
        self.category_combo = ttk.Combobox(
            row_target,
            textvariable=self.category_var,
            values=POPULAR_CATEGORIES,
            state="readonly",
            width=26,
            font=("Segoe UI", 9)
        )
        self.category_combo.pack(side="left", padx=(0, 14))
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_select)

        # City / Target Location Entry
        tk.Label(row_target, text="2. City / Location:", font=("Segoe UI", 9, "bold"), fg=THEME["accent_green"], bg=THEME["bg_card"]).pack(side="left", padx=(0, 6))
        self.location_var = tk.StringVar(value="Ghaziabad")
        self.entry_location = tk.Entry(
            row_target,
            textvariable=self.location_var,
            bg=THEME["bg_input"],
            fg=THEME["fg_text"],
            insertbackground=THEME["fg_text"],
            relief="flat",
            font=("Segoe UI", 9),
            width=18
        )
        self.entry_location.pack(side="left", padx=(0, 14))

        # Sub-Localities Entry (Optional)
        tk.Label(row_target, text="3. Sub-Areas (Optional):", font=("Segoe UI", 9), fg=THEME["fg_subtext"], bg=THEME["bg_card"]).pack(side="left", padx=(0, 6))
        self.localities_var = tk.StringVar(value="Indirapuram, Vaishali, Raj Nagar")
        self.entry_localities = tk.Entry(
            row_target,
            textvariable=self.localities_var,
            bg=THEME["bg_input"],
            fg=THEME["fg_text"],
            insertbackground=THEME["fg_text"],
            relief="flat",
            font=("Segoe UI", 9),
            width=26
        )
        self.entry_localities.pack(side="left", padx=(0, 12))

        # Generate Queries Button
        btn_generate = tk.Button(
            row_target,
            text="⚡ Apply / Generate Queries",
            bg=THEME["accent_blue"],
            fg="#0f172a",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._apply_smart_queries
        )
        btn_generate.pack(side="left")

        # ─── SECTION 1.5: CUSTOM CATEGORY ROW (Hidden by default, shown if Custom selected) ───
        self.row_custom_cat = tk.Frame(card, bg=THEME["bg_card"])
        tk.Label(self.row_custom_cat, text="Custom Niche / Business:", font=("Segoe UI", 9, "bold"), fg=THEME["accent_purple"], bg=THEME["bg_card"]).pack(side="left", padx=(0, 6))
        self.custom_cat_var = tk.StringVar(value="Solar panel dealers")
        self.entry_custom_cat = tk.Entry(
            self.row_custom_cat,
            textvariable=self.custom_cat_var,
            bg=THEME["bg_input"],
            fg=THEME["fg_text"],
            insertbackground=THEME["fg_text"],
            relief="flat",
            font=("Segoe UI", 9),
            width=35
        )
        self.entry_custom_cat.pack(side="left", padx=(0, 10))
        tk.Label(self.row_custom_cat, text="(e.g., Interior designers, Event planners, Solar panel suppliers, Pet clinics)", font=("Segoe UI", 8, "italic"), fg=THEME["fg_subtext"], bg=THEME["bg_card"]).pack(side="left")

        # ─── SECTION 2: OUTPUT FILE & SERPER API KEY ───
        row_config = tk.Frame(card, bg=THEME["bg_card"])
        row_config.pack(fill="x", pady=(6, 8))

        # Output CSV Path
        tk.Label(row_config, text="Output CSV File:", font=("Segoe UI", 9, "bold"), fg=THEME["fg_text"], bg=THEME["bg_card"]).pack(side="left", padx=(0, 6))
        self.output_path_var = tk.StringVar(value="ghaziabad_schools_colleges_leads.csv")
        self.entry_output = tk.Entry(
            row_config,
            textvariable=self.output_path_var,
            bg=THEME["bg_input"],
            fg=THEME["fg_text"],
            insertbackground=THEME["fg_text"],
            relief="flat",
            font=("Segoe UI", 9),
            width=36
        )
        self.entry_output.pack(side="left", padx=(0, 6))

        btn_browse = tk.Button(
            row_config,
            text="📂 Browse",
            bg=THEME["bg_card_alt"],
            fg=THEME["fg_text"],
            relief="flat",
            font=("Segoe UI", 8),
            cursor="hand2",
            padx=8,
            command=self._browse_output_file
        )
        btn_browse.pack(side="left", padx=(0, 20))

        # Serper API Key
        tk.Label(row_config, text="Serper API Key:", font=("Segoe UI", 9, "bold"), fg=THEME["fg_text"], bg=THEME["bg_card"]).pack(side="left", padx=(0, 6))
        self.api_key_var = tk.StringVar(value=DEFAULT_API_KEY)
        self.entry_api = tk.Entry(
            row_config,
            textvariable=self.api_key_var,
            show="●",
            bg=THEME["bg_input"],
            fg=THEME["fg_text"],
            insertbackground=THEME["fg_text"],
            relief="flat",
            font=("Segoe UI", 9),
            width=24
        )
        self.entry_api.pack(side="left", padx=(0, 6))

        self.btn_show_key = tk.Button(
            row_config,
            text="👁",
            bg=THEME["bg_card_alt"],
            fg=THEME["fg_text"],
            relief="flat",
            font=("Segoe UI", 8),
            cursor="hand2",
            command=self._toggle_api_visibility
        )
        self.btn_show_key.pack(side="left", padx=(0, 20))

        # Quick preset shortcut
        tk.Label(row_config, text="Quick Presets:", font=("Segoe UI", 9), fg=THEME["fg_subtext"], bg=THEME["bg_card"]).pack(side="left", padx=(0, 4))
        btn_p1 = tk.Button(row_config, text="Ghaziabad Schools", bg=THEME["bg_card_alt"], fg=THEME["accent_blue"], relief="flat", font=("Segoe UI", 8), cursor="hand2", command=lambda: self._load_preset_shortcut("ghaziabad"))
        btn_p1.pack(side="left", padx=2)
        btn_p2 = tk.Button(row_config, text="Ayodhya Hospitals", bg=THEME["bg_card_alt"], fg=THEME["accent_green"], relief="flat", font=("Segoe UI", 8), cursor="hand2", command=lambda: self._load_preset_shortcut("ayodhya"))
        btn_p2.pack(side="left", padx=2)

        # ─── SECTION 3: OPTIONS & ACTION BUTTONS ───
        row_actions = tk.Frame(card, bg=THEME["bg_card"])
        row_actions.pack(fill="x", pady=(4, 0))

        # Checkbox: Extract Email
        self.extract_email_var = tk.BooleanVar(value=True)
        chk_email = tk.Checkbutton(
            row_actions,
            text="Scan Official Websites for Emails",
            variable=self.extract_email_var,
            bg=THEME["bg_card"],
            fg=THEME["accent_green"],
            activebackground=THEME["bg_card"],
            activeforeground=THEME["accent_green"],
            selectcolor=THEME["bg_input"],
            font=("Segoe UI", 9)
        )
        chk_email.pack(side="left", padx=(0, 16))

        # Request delay slider
        tk.Label(row_actions, text="Delay (sec):", font=("Segoe UI", 9), fg=THEME["fg_subtext"], bg=THEME["bg_card"]).pack(side="left", padx=(0, 4))
        self.delay_scale = tk.Scale(
            row_actions,
            from_=0.1,
            to=2.0,
            resolution=0.1,
            orient="horizontal",
            length=90,
            bg=THEME["bg_card"],
            fg=THEME["fg_text"],
            troughcolor=THEME["bg_input"],
            highlightthickness=0,
            relief="flat",
            font=("Segoe UI", 8)
        )
        self.delay_scale.set(0.4)
        self.delay_scale.pack(side="left", padx=(0, 20))

        # Action Buttons
        self.btn_start = tk.Button(
            row_actions,
            text="▶  Start Scraping",
            bg=THEME["btn_start"],
            fg="#0f172a",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=4,
            command=self._start_scraping
        )
        self.btn_start.pack(side="left", padx=(0, 8))

        self.btn_pause = tk.Button(
            row_actions,
            text="⏸  Pause",
            bg=THEME["btn_pause"],
            fg="#0f172a",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            state="disabled",
            padx=12,
            pady=4,
            command=self._toggle_pause
        )
        self.btn_pause.pack(side="left", padx=(0, 8))

        self.btn_stop = tk.Button(
            row_actions,
            text="⏹  Stop",
            bg=THEME["btn_stop"],
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            state="disabled",
            padx=12,
            pady=4,
            command=self._stop_scraping
        )
        self.btn_stop.pack(side="left", padx=(0, 20))

        # CSV & Folder Utilities
        btn_open_csv = tk.Button(
            row_actions,
            text="📊 Open CSV",
            bg=THEME["bg_card_alt"],
            fg=THEME["accent_blue"],
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self._open_csv_file
        )
        btn_open_csv.pack(side="right", padx=(6, 0))

        btn_open_folder = tk.Button(
            row_actions,
            text="📁 Open Folder",
            bg=THEME["bg_card_alt"],
            fg=THEME["fg_text"],
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self._open_project_folder
        )
        btn_open_folder.pack(side="right")

    def _build_kpi_cards(self, parent):
        kpi_frame = tk.Frame(parent, bg=THEME["bg_dark"])
        kpi_frame.pack(fill="x", pady=(0, 10))

        # 4 KPI cards
        self.card_total = self._create_kpi_card(kpi_frame, "🏢 Total Scraped", "0", THEME["accent_blue"])
        self.card_phones = self._create_kpi_card(kpi_frame, "📞 With Phone", "0", THEME["accent_green"])
        self.card_emails = self._create_kpi_card(kpi_frame, "✉️ With Email", "0", THEME["accent_purple"])
        self.card_progress_info = self._create_kpi_card(kpi_frame, "⏳ Query Progress", "0 / 0", THEME["accent_amber"])

        # Progress bar under cards
        pbar_frame = tk.Frame(parent, bg=THEME["bg_dark"])
        pbar_frame.pack(fill="x", pady=(0, 5))

        self.pbar = ttk.Progressbar(pbar_frame, style="Horizontal.TProgressbar", mode="determinate")
        self.pbar.pack(fill="x", side="left", expand=True)

        self.lbl_progress_pct = tk.Label(
            pbar_frame,
            text="0%",
            font=("Segoe UI", 9, "bold"),
            fg=THEME["accent_blue"],
            bg=THEME["bg_dark"],
            padx=8
        )
        self.lbl_progress_pct.pack(side="right")

    def _create_kpi_card(self, parent, label_text, default_val, accent_color):
        card = tk.Frame(parent, bg=THEME["bg_card"], padx=14, pady=10)
        card.pack(side="left", fill="both", expand=True, padx=4)

        lbl_head = tk.Label(card, text=label_text, font=("Segoe UI", 9), fg=THEME["fg_subtext"], bg=THEME["bg_card"])
        lbl_head.pack(anchor="w")

        lbl_val = tk.Label(card, text=default_val, font=("Segoe UI", 16, "bold"), fg=accent_color, bg=THEME["bg_card"])
        lbl_val.pack(anchor="w", pady=(2, 0))
        return lbl_val

    def _build_table_tab(self, parent):
        # Search / filter bar
        filter_bar = tk.Frame(parent, bg=THEME["bg_card"], padx=10, pady=8)
        filter_bar.pack(fill="x")

        tk.Label(filter_bar, text="🔍 Search in results:", font=("Segoe UI", 9), fg=THEME["fg_subtext"], bg=THEME["bg_card"]).pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_table())
        entry_filter = tk.Entry(
            filter_bar,
            textvariable=self.search_var,
            bg=THEME["bg_input"],
            fg=THEME["fg_text"],
            insertbackground=THEME["fg_text"],
            relief="flat",
            font=("Segoe UI", 9),
            width=30
        )
        entry_filter.pack(side="left", padx=(0, 15))

        btn_clear_filter = tk.Button(
            filter_bar,
            text="Clear",
            bg=THEME["bg_card_alt"],
            fg=THEME["fg_text"],
            relief="flat",
            font=("Segoe UI", 8),
            command=lambda: self.search_var.set("")
        )
        btn_clear_filter.pack(side="left")

        lbl_hint = tk.Label(
            filter_bar,
            text="💡 Tip: Double-click any row to view complete details, rating, or copy phone/email.",
            font=("Segoe UI", 8, "italic"),
            fg=THEME["fg_subtext"],
            bg=THEME["bg_card"]
        )
        lbl_hint.pack(side="right")

        # Table & Scrollbars
        table_container = tk.Frame(parent, bg=THEME["bg_card"])
        table_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("name", "category", "phone", "email", "address", "website", "rating", "reviews")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="Name")
        self.tree.heading("category", text="Category")
        self.tree.heading("phone", text="Phone Number")
        self.tree.heading("email", text="Email Address")
        self.tree.heading("address", text="Address")
        self.tree.heading("website", text="Website")
        self.tree.heading("rating", text="Rating")
        self.tree.heading("reviews", text="Reviews")

        self.tree.column("name", width=250, minwidth=160)
        self.tree.column("category", width=130, minwidth=100)
        self.tree.column("phone", width=120, minwidth=100)
        self.tree.column("email", width=180, minwidth=130)
        self.tree.column("address", width=210, minwidth=130)
        self.tree.column("website", width=160, minwidth=110)
        self.tree.column("rating", width=65, minwidth=50, anchor="center")
        self.tree.column("reviews", width=75, minwidth=60, anchor="center")

        # Alternating row colors
        self.tree.tag_configure("even", background="#1e1e2e")
        self.tree.tag_configure("odd", background="#222235")

        vsb = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self._on_row_double_click)

    def _build_logs_tab(self, parent):
        top_bar = tk.Frame(parent, bg=THEME["bg_card"], padx=10, pady=8)
        top_bar.pack(fill="x")

        btn_clear = tk.Button(
            top_bar,
            text="🧹 Clear Log Console",
            bg=THEME["bg_card_alt"],
            fg=THEME["fg_text"],
            relief="flat",
            font=("Segoe UI", 8),
            cursor="hand2",
            command=self._clear_logs
        )
        btn_clear.pack(side="left")

        self.autoscroll_var = tk.BooleanVar(value=True)
        chk_scroll = tk.Checkbutton(
            top_bar,
            text="Auto-scroll to latest",
            variable=self.autoscroll_var,
            bg=THEME["bg_card"],
            fg=THEME["fg_subtext"],
            selectcolor=THEME["bg_input"],
            font=("Segoe UI", 8)
        )
        chk_scroll.pack(side="right")

        # Console Text Box
        console_frame = tk.Frame(parent, bg=THEME["console_bg"])
        console_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.txt_console = tk.Text(
            console_frame,
            bg=THEME["console_bg"],
            fg=THEME["console_fg"],
            insertbackground=THEME["fg_text"],
            font=("Consolas", 9),
            wrap="word",
            relief="flat",
            padx=10,
            pady=10
        )
        console_sb = ttk.Scrollbar(console_frame, orient="vertical", command=self.txt_console.yview)
        self.txt_console.configure(yscrollcommand=console_sb.set)

        self.txt_console.pack(side="left", fill="both", expand=True)
        console_sb.pack(side="right", fill="y")

        # Color tags for console
        self.txt_console.tag_config("info", foreground=THEME["fg_text"])
        self.txt_console.tag_config("success", foreground=THEME["accent_green"])
        self.txt_console.tag_config("warning", foreground=THEME["accent_amber"])
        self.txt_console.tag_config("error", foreground=THEME["accent_red"])
        self.txt_console.tag_config("header", foreground=THEME["accent_purple"], font=("Consolas", 9, "bold"))

    def _build_queries_tab(self, parent):
        hint = tk.Label(
            parent,
            text="View or directly edit the active queries for Places & Search APIs before scraping. One query per line.",
            font=("Segoe UI", 9),
            fg=THEME["fg_subtext"],
            bg=THEME["bg_card"],
            padx=10,
            pady=8
        )
        hint.pack(anchor="w")

        q_frame = tk.Frame(parent, bg=THEME["bg_card"], padx=10)
        q_frame.pack(fill="both", expand=True)

        # Left Column: Places Queries
        left = tk.Frame(q_frame, bg=THEME["bg_card"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        tk.Label(left, text="📍 Serper Places Queries (Google Maps Data):", font=("Segoe UI", 9, "bold"), fg=THEME["accent_blue"], bg=THEME["bg_card"]).pack(anchor="w", pady=(0, 4))
        self.txt_places_queries = tk.Text(left, bg=THEME["bg_input"], fg=THEME["fg_text"], insertbackground=THEME["fg_text"], font=("Segoe UI", 9), relief="flat", height=14)
        self.txt_places_queries.pack(fill="both", expand=True)

        # Right Column: Search Queries
        right = tk.Frame(q_frame, bg=THEME["bg_card"])
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))

        tk.Label(right, text="🔎 Serper Search Queries (Organic Snippets):", font=("Segoe UI", 9, "bold"), fg=THEME["accent_green"], bg=THEME["bg_card"]).pack(anchor="w", pady=(0, 4))
        self.txt_search_queries = tk.Text(right, bg=THEME["bg_input"], fg=THEME["fg_text"], insertbackground=THEME["fg_text"], font=("Segoe UI", 9), relief="flat", height=14)
        self.txt_search_queries.pack(fill="both", expand=True)

        bottom_bar = tk.Frame(parent, bg=THEME["bg_card"], padx=10, pady=10)
        bottom_bar.pack(fill="x")

        btn_regenerate = tk.Button(
            bottom_bar,
            text="⚡ Regenerate from Target & City",
            bg=THEME["bg_card_alt"],
            fg=THEME["accent_blue"],
            font=("Segoe UI", 8),
            relief="flat",
            command=self._apply_smart_queries
        )
        btn_regenerate.pack(side="left")

    # ─────────────────────────────────────────────
    # DYNAMIC TARGETING & PRESET LOGIC
    # ─────────────────────────────────────────────
    def _on_category_select(self, event=None):
        cat = self.category_var.get()
        if "Custom" in cat:
            self.row_custom_cat.pack(fill="x", pady=(2, 6))
        else:
            self.row_custom_cat.pack_forget()

        # Automatically re-generate queries when category changes
        self._apply_smart_queries()

    def _apply_smart_queries(self):
        cat = self.category_var.get()
        if "Custom" in cat:
            cat = self.custom_cat_var.get().strip() or "Business"

        loc = self.location_var.get().strip() or "India"
        sub_areas = [s.strip() for s in self.localities_var.get().split(",") if s.strip()]

        result = generate_smart_queries(category=cat, location=loc, localities=sub_areas)

        # Populate Query text fields
        self.txt_places_queries.delete("1.0", tk.END)
        self.txt_places_queries.insert(tk.END, "\n".join(result["places"]))

        self.txt_search_queries.delete("1.0", tk.END)
        self.txt_search_queries.insert(tk.END, "\n".join(result["search"]))

        # Suggest output filename
        self.output_path_var.set(result["filename"])

    def _load_preset_shortcut(self, preset_key):
        if preset_key == "ghaziabad":
            self.category_var.set("Schools & Colleges")
            self.location_var.set("Ghaziabad")
            self.localities_var.set("Indirapuram, Vaishali, Raj Nagar Extension, Crossing Republik, Vasundhara")
            self.row_custom_cat.pack_forget()
            self._apply_smart_queries()
            self.output_path_var.set("ghaziabad_schools_colleges.csv")
        elif preset_key == "ayodhya":
            self.category_var.set("Hospitals & Healthcare")
            self.location_var.set("Ayodhya")
            self.localities_var.set("Civil Lines, Faizabad, Naya Ghat")
            self.row_custom_cat.pack_forget()
            self._apply_smart_queries()
            self.output_path_var.set("ayodhya_hospitals.csv")

    def _toggle_api_visibility(self):
        if self.entry_api.cget("show") == "":
            self.entry_api.config(show="●")
            self.btn_show_key.config(text="👁")
        else:
            self.entry_api.config(show="")
            self.btn_show_key.config(text="🔒")

    def _browse_output_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=self.output_path_var.get()
        )
        if filename:
            self.output_path_var.set(filename)

    # ─────────────────────────────────────────────
    # SCRAPING CONTROLS
    # ─────────────────────────────────────────────
    def _start_scraping(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please provide a valid Serper API key.")
            return

        places_text = self.txt_places_queries.get("1.0", tk.END).strip()
        search_text = self.txt_search_queries.get("1.0", tk.END).strip()

        place_queries = [line.strip() for line in places_text.splitlines() if line.strip()]
        search_queries = [line.strip() for line in search_text.splitlines() if line.strip()]

        if not place_queries and not search_queries:
            messagebox.showwarning("Warning", "Please provide at least one query to search.")
            return

        out_file = self.output_path_var.get().strip()
        if not out_file:
            messagebox.showerror("Error", "Please specify an output CSV file name.")
            return

        # Prepare UI for scraping
        self.is_scraping = True
        self.is_paused = False
        self.btn_start.config(state="disabled")
        self.btn_pause.config(state="normal", text="⏸  Pause")
        self.btn_stop.config(state="normal")
        self.lbl_status.config(text="● SCRAPING...", fg=THEME["accent_green"])

        # Reset counts and progress
        self.all_table_data.clear()
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.notebook.tab(self.tab_table, text="  📊 Live Records (0)  ")

        self.card_total.config(text="0")
        self.card_phones.config(text="0")
        self.card_emails.config(text="0")
        self.card_progress_info.config(text=f"0 / {len(place_queries) + len(search_queries)}")
        self.pbar["value"] = 0
        self.lbl_progress_pct.config(text="0%")

        # Initialize Scraper Engine
        delay_val = float(self.delay_scale.get())
        self.engine = ScraperEngine(
            api_key=api_key,
            extract_email=self.extract_email_var.get(),
            request_delay=delay_val,
            query_delay=1.0
        )

        # Wire callbacks to event queue for thread safety
        self.engine.on_log = lambda msg, lvl="info": self.event_queue.put(("log", msg, lvl))
        self.engine.on_record = lambda rec: self.event_queue.put(("record", rec))
        self.engine.on_progress = lambda cur, tot, q: self.event_queue.put(("progress", cur, tot, q))
        self.engine.on_stats = lambda s: self.event_queue.put(("stats", s))
        self.engine.on_finish = lambda tot, f: self.event_queue.put(("finish", tot, f))

        # Launch worker thread
        self.worker_thread = threading.Thread(
            target=self.engine.run,
            args=(place_queries, search_queries, out_file),
            daemon=True
        )
        self.worker_thread.start()

    def _toggle_pause(self):
        if not self.engine:
            return
        if not self.is_paused:
            self.engine.pause()
            self.is_paused = True
            self.btn_pause.config(text="▶  Resume")
            self.lbl_status.config(text="● PAUSED", fg=THEME["accent_amber"])
        else:
            self.engine.resume()
            self.is_paused = False
            self.btn_pause.config(text="⏸  Pause")
            self.lbl_status.config(text="● SCRAPING...", fg=THEME["accent_green"])

    def _stop_scraping(self):
        if self.engine and self.is_scraping:
            self.btn_stop.config(state="disabled")
            self.lbl_status.config(text="● STOPPING...", fg=THEME["accent_red"])
            self.engine.stop()

    # ─────────────────────────────────────────────
    # THREAD QUEUE EVENT PROCESSING
    # ─────────────────────────────────────────────
    def _process_queue(self):
        try:
            while True:
                event = self.event_queue.get_nowait()
                kind = event[0]

                if kind == "log":
                    _, message, level = event
                    self._append_log(message, level)

                elif kind == "record":
                    _, record = event
                    self._add_record_to_table(record)

                elif kind == "progress":
                    _, cur, tot, query = event
                    self.card_progress_info.config(text=f"{cur} / {tot}")
                    pct = int((cur / tot) * 100) if tot > 0 else 0
                    self.pbar["value"] = pct
                    self.lbl_progress_pct.config(text=f"{pct}%")

                elif kind == "stats":
                    _, stats = event
                    self.card_total.config(text=str(stats.get("total", 0)))
                    self.card_phones.config(text=str(stats.get("phones", 0)))
                    self.card_emails.config(text=str(stats.get("emails", 0)))

                elif kind == "finish":
                    _, total_saved, file_path = event
                    self._on_scrape_completed(total_saved, file_path)

        except queue.Empty:
            pass

        self.after(50, self._process_queue)

    def _append_log(self, text, level="info"):
        self.txt_console.insert(tk.END, f"{text}\n", level)
        if self.autoscroll_var.get():
            self.txt_console.see(tk.END)

    def _clear_logs(self):
        self.txt_console.delete("1.0", tk.END)

    def _add_record_to_table(self, record):
        self.all_table_data.append(record)
        idx = len(self.all_table_data)
        tag = "even" if idx % 2 == 0 else "odd"

        self.tree.insert(
            "",
            "end",
            values=(
                record.get("Name", ""),
                record.get("Category", ""),
                record.get("Phone Number", ""),
                record.get("Email", ""),
                record.get("Address", ""),
                record.get("Website", ""),
                record.get("Rating", ""),
                record.get("Reviews Count", ""),
            ),
            tags=(tag,)
        )
        self.notebook.tab(self.tab_table, text=f"  📊 Live Records ({len(self.all_table_data)})  ")

    def _filter_table(self):
        q = self.search_var.get().strip().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)

        filtered_count = 0
        for i, rec in enumerate(self.all_table_data, 1):
            if not q or any(q in str(val).lower() for val in rec.values()):
                tag = "even" if filtered_count % 2 == 0 else "odd"
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        rec.get("Name", ""),
                        rec.get("Category", ""),
                        rec.get("Phone Number", ""),
                        rec.get("Email", ""),
                        rec.get("Address", ""),
                        rec.get("Website", ""),
                        rec.get("Rating", ""),
                        rec.get("Reviews Count", ""),
                    ),
                    tags=(tag,)
                )
                filtered_count += 1

    def _on_row_double_click(self, event):
        item_id = self.tree.selection()
        if not item_id:
            return
        vals = self.tree.item(item_id, "values")
        if not vals:
            return

        # Detail Popup Dialog
        win = tk.Toplevel(self)
        win.title(vals[0][:40])
        win.geometry("580x480")
        win.configure(bg=THEME["bg_card"])
        win.transient(self)

        fields = [
            ("Name", vals[0]),
            ("Category", vals[1]),
            ("Phone Number", vals[2]),
            ("Email", vals[3]),
            ("Address", vals[4]),
            ("Website", vals[5]),
            ("Rating", vals[6]),
            ("Reviews Count", vals[7]),
        ]

        tk.Label(win, text="Entity Details", font=("Segoe UI", 12, "bold"), fg=THEME["accent_blue"], bg=THEME["bg_card"], pady=8).pack()

        form = tk.Frame(win, bg=THEME["bg_card"], padx=15)
        form.pack(fill="both", expand=True)

        for label_text, val in fields:
            row = tk.Frame(form, bg=THEME["bg_card"], pady=3)
            row.pack(fill="x")

            tk.Label(row, text=f"{label_text}:", width=14, anchor="w", font=("Segoe UI", 9, "bold"), fg=THEME["fg_subtext"], bg=THEME["bg_card"]).pack(side="left")

            e = tk.Entry(row, bg=THEME["bg_input"], fg=THEME["fg_text"], relief="flat", font=("Segoe UI", 9))
            e.insert(0, val)
            e.configure(state="readonly")
            e.pack(side="left", fill="x", expand=True, padx=(4, 6))

            btn_copy = tk.Button(
                row,
                text="Copy",
                bg=THEME["bg_card_alt"],
                fg=THEME["accent_green"],
                relief="flat",
                font=("Segoe UI", 8),
                command=lambda v=val: self._copy_to_clipboard(v)
            )
            btn_copy.pack(side="right")

        btn_close = tk.Button(win, text="Close", bg=THEME["bg_card_alt"], fg=THEME["fg_text"], relief="flat", command=win.destroy, pady=4)
        btn_close.pack(pady=10)

    def _copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", f"Copied to clipboard: {text[:40]}")

    def _on_scrape_completed(self, total_saved, file_path):
        self.is_scraping = False
        self.is_paused = False
        self.btn_start.config(state="normal")
        self.btn_pause.config(state="disabled", text="⏸  Pause")
        self.btn_stop.config(state="disabled")
        self.lbl_status.config(text="● COMPLETED", fg=THEME["accent_blue"])

        messagebox.showinfo(
            "Scraping Completed",
            f"Successfully finished!\n\nTotal records collected: {total_saved}\nFile saved to: {file_path}"
        )

    # ─────────────────────────────────────────────
    # UTILITIES
    # ─────────────────────────────────────────────
    def _open_csv_file(self):
        path = self.output_path_var.get().strip()
        full_path = os.path.abspath(path)
        if not os.path.exists(full_path):
            messagebox.showwarning("File Not Found", f"No file exists yet at:\n{full_path}\nRun the scraper first.")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(full_path)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", full_path])
            else:
                subprocess.Popen(["xdg-open", full_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    def _open_project_folder(self):
        try:
            if sys.platform.startswith("win"):
                os.startfile(self.base_dir)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", self.base_dir])
            else:
                subprocess.Popen(["xdg-open", self.base_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def _on_closing(self):
        if self.is_scraping:
            if messagebox.askyesno("Exit Confirmation", "A scraping task is currently running. Do you want to stop and exit?"):
                if self.engine:
                    self.engine.stop()
                self.destroy()
        else:
            self.destroy()


def main():
    app = ScraperApp()
    app.mainloop()


if __name__ == "__main__":
    main()
