"""
Core Scraping Engine for Serper API
====================================
Contains the original proven scraping logic, Serper Places & Search APIs,
dynamic business/category query generator, and streaming callbacks.
"""

import requests
import re
import csv
import json
import time
import os
import threading
from typing import Callable, Optional, List, Dict, Any

# ─────────────────────────────────────────────
# DEFAULT CONFIGURATION & API KEY (PRESERVED)
# ─────────────────────────────────────────────
DEFAULT_API_KEY = "abb6e72105a832dee04d7a18dd103b387fe1a7ea"

PLACES_URL = "https://google.serper.dev/places"
SEARCH_URL = "https://google.serper.dev/search"

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}|0\d{2,4}[\-\s]?\d{6,8}")

JUNK_EMAIL = [
    "sentry", "wixpress", "example.com", "cloudflare", "amazonaws",
    "googleapis", "facebook", "schema.org", "w3.org", ".png", ".jpg",
    ".svg", ".webp", "noreply", "no-reply", "bootstrap", "jquery"
]

SKIP_DOMAINS = [
    "justdial.com", "shiksha.com", "collegedunia.com", "careers360.com",
    "edustoke.com", "uniapply.com", "getmyuni.com", "sulekha.com",
    "wikipedia.org", "indiamart.com", "quora.com", "facebook.com",
    "instagram.com", "youtube.com", "targetstudy.com", "icbse.com"
]

# ─────────────────────────────────────────────
# CATEGORIES & SMART QUERY TEMPLATES
# ─────────────────────────────────────────────
POPULAR_CATEGORIES = [
    "Schools & Colleges",
    "Hospitals & Healthcare",
    "Doctors & Clinics",
    "Gyms & Fitness Centers",
    "Restaurants, Cafes & Bakeries",
    "Hotels & Resorts",
    "Real Estate Agents & Builders",
    "IT & Software Companies",
    "Lawyers & Law Firms",
    "Chartered Accountants (CA)",
    "Coaching Institutes & Tuition Centers",
    "Car Showrooms & Auto Services",
    "Beauty Parlours & Salons",
    "Pharmacies & Medical Stores",
    "Custom / Other (Type Your Own)"
]

CATEGORY_TEMPLATES = {
    "Schools & Colleges": {
        "places": [
            "CBSE school in {loc}",
            "ICSE school in {loc}",
            "public school in {loc}",
            "international school in {loc}",
            "convent school in {loc}",
            "senior secondary school in {loc}",
            "play school and preschool in {loc}",
            "engineering college in {loc}",
            "management MBA college in {loc}",
            "degree college in {loc}",
            "law college in {loc}",
            "pharmacy college in {loc}",
            "medical and dental college in {loc}",
            "private university in {loc}",
        ],
        "search": [
            "top schools in {loc} contact number email",
            "engineering colleges in {loc} contact details",
            "degree colleges in {loc} contact phone email",
            "MBA BBA colleges in {loc} phone number",
        ]
    },
    "Hospitals & Healthcare": {
        "places": [
            "hospital in {loc}",
            "super speciality hospital in {loc}",
            "multi speciality hospital in {loc}",
            "private hospital in {loc}",
            "government hospital in {loc}",
            "eye hospital in {loc}",
            "maternity hospital in {loc}",
            "trauma centre in {loc}",
            "diagnostic center in {loc}",
            "pathology lab in {loc}",
        ],
        "search": [
            "top hospitals in {loc} contact number email",
            "best private hospital in {loc} phone number email",
            "diagnostic centres in {loc} contact details",
        ]
    },
    "Doctors & Clinics": {
        "places": [
            "doctor clinic in {loc}",
            "general physician in {loc}",
            "dental clinic in {loc}",
            "dentist in {loc}",
            "pediatrician child specialist in {loc}",
            "gynecologist in {loc}",
            "orthopedic doctor in {loc}",
            "dermatologist skin clinic in {loc}",
            "cardiologist heart clinic in {loc}",
            "ENT specialist clinic in {loc}",
        ],
        "search": [
            "top doctors clinic in {loc} phone number",
            "best dental clinic in {loc} contact details",
            "private clinic in {loc} contact number",
        ]
    },
    "Gyms & Fitness Centers": {
        "places": [
            "gym in {loc}",
            "fitness center in {loc}",
            "unisex gym in {loc}",
            "crossfit gym in {loc}",
            "yoga center in {loc}",
            "zumba classes in {loc}",
            "bodybuilding gym in {loc}",
            "health club in {loc}",
        ],
        "search": [
            "best gyms in {loc} contact number phone",
            "fitness club in {loc} contact details email",
        ]
    },
    "Restaurants, Cafes & Bakeries": {
        "places": [
            "restaurant in {loc}",
            "family restaurant in {loc}",
            "fine dining restaurant in {loc}",
            "cafe in {loc}",
            "bakery and cake shop in {loc}",
            "pure veg restaurant in {loc}",
            "fast food restaurant in {loc}",
            "pizzeria and burger cafe in {loc}",
        ],
        "search": [
            "popular restaurants in {loc} phone number contact",
            "best cafes in {loc} contact details",
        ]
    },
    "Hotels & Resorts": {
        "places": [
            "hotel in {loc}",
            "luxury hotel in {loc}",
            "resort in {loc}",
            "guest house in {loc}",
            "budget hotel in {loc}",
            "3 star hotel in {loc}",
            "banquet hall and hotel in {loc}",
        ],
        "search": [
            "hotels in {loc} phone number reception email",
            "resorts in {loc} contact booking details",
        ]
    },
    "Real Estate Agents & Builders": {
        "places": [
            "real estate agent in {loc}",
            "property dealer in {loc}",
            "builders and developers in {loc}",
            "commercial property dealer in {loc}",
            "residential property consultant in {loc}",
            "real estate consultant in {loc}",
        ],
        "search": [
            "top property dealers in {loc} phone number email",
            "real estate brokers in {loc} contact details",
            "builders and developers in {loc} office phone number",
        ]
    },
    "IT & Software Companies": {
        "places": [
            "IT company in {loc}",
            "software company in {loc}",
            "web development company in {loc}",
            "mobile app development company in {loc}",
            "digital marketing agency in {loc}",
            "IT consultant in {loc}",
            "technology solutions in {loc}",
        ],
        "search": [
            "IT companies in {loc} contact number email",
            "software development companies in {loc} office address phone",
            "digital marketing agencies in {loc} contact details",
        ]
    },
    "Lawyers & Law Firms": {
        "places": [
            "lawyer in {loc}",
            "advocate in {loc}",
            "law firm in {loc}",
            "civil lawyer in {loc}",
            "criminal lawyer in {loc}",
            "corporate lawyer in {loc}",
            "high court advocate in {loc}",
            "district court lawyer in {loc}",
        ],
        "search": [
            "top advocates in {loc} contact number email",
            "law firms in {loc} contact details phone",
        ]
    },
    "Chartered Accountants (CA)": {
        "places": [
            "chartered accountant in {loc}",
            "CA firm in {loc}",
            "tax consultant in {loc}",
            "GST consultant in {loc}",
            "auditor in {loc}",
            "accounting firm in {loc}",
        ],
        "search": [
            "top CA firms in {loc} contact number email",
            "chartered accountants in {loc} phone number",
        ]
    },
    "Coaching Institutes & Tuition Centers": {
        "places": [
            "coaching institute in {loc}",
            "IIT JEE coaching in {loc}",
            "NEET medical coaching in {loc}",
            "UPSC IAS coaching in {loc}",
            "SSC banking coaching in {loc}",
            "commerce tuition coaching in {loc}",
            "computer training institute in {loc}",
        ],
        "search": [
            "top coaching institutes in {loc} phone number email",
            "best tuition centres in {loc} contact details",
        ]
    },
    "Car Showrooms & Auto Services": {
        "places": [
            "car showroom in {loc}",
            "used car dealer in {loc}",
            "car service center in {loc}",
            "auto workshop in {loc}",
            "automobile repair shop in {loc}",
        ],
        "search": [
            "car dealers in {loc} contact number phone",
            "car service centers in {loc} contact details",
        ]
    },
    "Beauty Parlours & Salons": {
        "places": [
            "beauty parlour in {loc}",
            "unisex salon in {loc}",
            "hair salon in {loc}",
            "makeup studio in {loc}",
            "bridal makeup artist in {loc}",
            "spa in {loc}",
        ],
        "search": [
            "top salons in {loc} phone number",
            "beauty parlours in {loc} contact details",
        ]
    },
    "Pharmacies & Medical Stores": {
        "places": [
            "pharmacy in {loc}",
            "chemist and druggist in {loc}",
            "medical store in {loc}",
            "24 hours pharmacy in {loc}",
            "wholesale medicine supplier in {loc}",
        ],
        "search": [
            "medical stores in {loc} contact phone number",
            "pharmacies in {loc} phone number",
        ]
    }
}


def generate_smart_queries(category: str, location: str, localities: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Dynamically generate optimized Serper Places & Search queries
    for any category and location chosen by user.
    """
    loc = location.strip() or "India"
    cat = category.strip()

    template = CATEGORY_TEMPLATES.get(cat)

    if template:
        places = [q.format(loc=loc) for q in template["places"]]
        search = [q.format(loc=loc) for q in template["search"]]
    else:
        # Custom category
        places = [
            f"{cat} in {loc}",
            f"top {cat} in {loc}",
            f"best {cat} in {loc}",
            f"famous {cat} in {loc}",
            f"local {cat} in {loc}",
            f"{cat} services in {loc}",
        ]
        search = [
            f"top {cat} in {loc} contact number email",
            f"best {cat} in {loc} phone number contact details",
            f"list of {cat} in {loc} phone number",
        ]

    # Add sub-localities if provided
    if localities:
        for area in localities:
            area_clean = area.strip()
            if area_clean:
                places.append(f"{cat} in {area_clean} {loc}")

    # Generate safe filename
    safe_loc = re.sub(r"[^a-zA-Z0-9]+", "_", loc.lower()).strip("_")
    safe_cat = re.sub(r"[^a-zA-Z0-9]+", "_", cat.lower()).strip("_")
    default_filename = f"{safe_loc}_{safe_cat}_leads.csv"

    return {
        "places": places,
        "search": search,
        "filename": default_filename
    }


# ─────────────────────────────────────────────
# PRESET QUERIES (PRESERVED FOR BACKWARD COMPATIBILITY)
# ─────────────────────────────────────────────
PRESET_GHAZIABAD_SCHOOLS = {
    "name": "Ghaziabad Schools & Colleges",
    "output_file": "ghaziabad_schools_colleges.csv",
    "category": "Schools & Colleges",
    "location": "Ghaziabad",
    "places": [
        "CBSE school in Ghaziabad",
        "ICSE school in Ghaziabad",
        "public school in Ghaziabad",
        "international school in Ghaziabad",
        "convent school in Ghaziabad",
        "government school in Ghaziabad",
        "senior secondary school in Ghaziabad",
        "play school and preschool in Ghaziabad",
        "schools in Indirapuram Ghaziabad",
        "schools in Vaishali Ghaziabad",
        "schools in Raj Nagar Extension Ghaziabad",
        "schools in Crossing Republik Ghaziabad",
        "schools in Vasundhara Ghaziabad",
        "schools in Kavi Nagar Ghaziabad",
        "schools in Modinagar Ghaziabad",
        "schools in Muradnagar Ghaziabad",
        "schools in Loni Ghaziabad",
        "engineering college in Ghaziabad",
        "management MBA college in Ghaziabad",
        "degree college in Ghaziabad",
        "law college in Ghaziabad",
        "pharmacy college in Ghaziabad",
        "medical and dental college in Ghaziabad",
        "B.Ed college in Ghaziabad",
        "polytechnic college in Ghaziabad",
        "colleges in Modinagar and Muradnagar Ghaziabad",
        "private university in Ghaziabad",
    ],
    "search": [
        "top schools in Ghaziabad contact number email",
        "engineering colleges in Ghaziabad contact details",
        "CBSE schools in Indirapuram Vaishali Ghaziabad phone number",
        "degree colleges in Ghaziabad Uttar Pradesh contact",
        "MBA BBA colleges in Ghaziabad phone number",
    ]
}

PRESET_AYODHYA_HOSPITALS = {
    "name": "Ayodhya Hospitals & Healthcare",
    "output_file": "ayodhya_hospitals.csv",
    "category": "Hospitals & Healthcare",
    "location": "Ayodhya",
    "places": [
        "hospital in Ayodhya",
        "super speciality hospital in Ayodhya",
        "multi speciality hospital Ayodhya",
        "private hospital in Ayodhya",
        "government hospital in Ayodhya",
        "eye hospital in Ayodhya",
        "dental clinic in Ayodhya",
        "maternity hospital in Ayodhya",
        "trauma centre in Ayodhya",
        "diagnostic center in Ayodhya",
        "pathology lab in Ayodhya",
    ],
    "search": [
        "top hospitals in Ayodhya contact number email",
        "doctors clinic in Ayodhya contact details phone",
        "best private hospital in Ayodhya phone number",
    ]
}

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def clean_name(name: str) -> str:
    """Strip aggregator suffixes from names"""
    name = re.sub(
        r"\s*[-|:]\s*(?:JustDial|Shiksha|Collegedunia|Careers360|GetMyUni|Edustoke|UniApply|Sulekha|Google|Facebook).*$",
        "",
        name or "",
        flags=re.IGNORECASE
    )
    return name.strip()

def extract_phone(text: str) -> str:
    """Extract first valid phone number"""
    for p in PHONE_RE.findall(text or ""):
        digits = re.sub(r"\D", "", p)
        if len(digits) >= 10:
            return p.strip()
    return ""

def is_valid(name: str) -> bool:
    """Check if name is valid entity, not generic listicle"""
    if not name or len(name) < 3 or len(name) > 130:
        return False
    skip = [
        "justdial", "shiksha", "collegedunia", "careers360", "edustoke",
        "sulekha", "advertisement", "wikipedia", "youtube", "top 10",
        "top 20", "best schools", "best colleges", "best hospitals",
        "list of", "fee structure"
    ]
    return not any(s in name.lower() for s in skip)

def infer_category(query: str, place_category: str = "") -> str:
    """Infer entity category based on query and place meta"""
    if place_category:
        return place_category
    q_low = query.lower()
    if any(k in q_low for k in ["college", "university", "mba", "polytechnic", "degree", "b.ed"]):
        return "College / University"
    if any(k in q_low for k in ["hospital", "clinic", "dental", "eye", "pathology", "diagnostic"]):
        return "Hospital / Healthcare"
    if any(k in q_low for k in ["school", "preschool", "cbse", "icse", "convent"]):
        return "School"
    if any(k in q_low for k in ["gym", "fitness", "yoga"]):
        return "Fitness & Gym"
    if any(k in q_low for k in ["restaurant", "cafe", "bakery", "dining"]):
        return "Restaurant / Food"
    if any(k in q_low for k in ["hotel", "resort"]):
        return "Hotel / Hospitality"
    if any(k in q_low for k in ["real estate", "property", "builder"]):
        return "Real Estate"
    if any(k in q_low for k in ["software", "web development", "it company"]):
        return "IT & Software"
    if any(k in q_low for k in ["lawyer", "advocate", "law firm"]):
        return "Legal Services"
    if any(k in q_low for k in ["chartered accountant", "ca firm", "tax"]):
        return "Financial & Tax"
    return "Organization / Business"

def get_email_from_site(url: str, timeout: int = 7) -> str:
    """Scrape official website and contact pages for email"""
    if not url:
        return ""
    base = url.rstrip("/")
    pages = [base, base + "/contact", base + "/contact-us", base + "/about-us"]
    for page in pages:
        try:
            r = requests.get(page, timeout=timeout, headers=BROWSER_HEADERS)
            if r.status_code != 200:
                continue
            found = EMAIL_RE.findall(r.text)
            clean = [e for e in set(found) if not any(j in e.lower() for j in JUNK_EMAIL)]
            if clean:
                return clean[0]
        except Exception:
            continue
    return ""

# ─────────────────────────────────────────────
# CORE SCRAPER ENGINE CLASS
# ─────────────────────────────────────────────
class ScraperEngine:
    def __init__(self,
                 api_key: str = DEFAULT_API_KEY,
                 extract_email: bool = True,
                 request_delay: float = 0.4,
                 query_delay: float = 1.0):
        self.api_key = api_key or DEFAULT_API_KEY
        self.extract_email = extract_email
        self.request_delay = request_delay
        self.query_delay = query_delay

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.is_running = False

        self.seen_names = set()
        self.all_results = []
        self.total_phone_count = 0
        self.total_email_count = 0

        # Callbacks
        self.on_log: Optional[Callable[[str, str], None]] = None
        self.on_record: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_progress: Optional[Callable[[int, int, str], None]] = None
        self.on_stats: Optional[Callable[[Dict[str, int]], None]] = None
        self.on_finish: Optional[Callable[[int, str], None]] = None

    def log(self, message: str, level: str = "info"):
        if self.on_log:
            self.on_log(message, level)
        else:
            print(f"[{level.upper()}] {message}")

    def update_stats(self):
        if self.on_stats:
            self.on_stats({
                "total": len(self.all_results),
                "phones": self.total_phone_count,
                "emails": self.total_email_count,
            })

    def serper_places(self, query: str) -> List[Dict[str, Any]]:
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = json.dumps({"q": query, "gl": "in", "hl": "en"})
        try:
            resp = requests.post(PLACES_URL, headers=headers, data=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                places = data.get("places", [])
                self.log(f"Places API returned {len(places)} items for '{query}'", "info")
                return places
            else:
                self.log(f"Places API error: HTTP {resp.status_code} - {resp.text[:120]}", "error")
        except Exception as e:
            self.log(f"Places API request failed: {e}", "error")
        return []

    def serper_search(self, query: str, num: int = 10) -> List[Dict[str, Any]]:
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = json.dumps({"q": query, "gl": "in", "hl": "en", "num": num})
        try:
            resp = requests.post(SEARCH_URL, headers=headers, data=payload, timeout=20)
            if resp.status_code == 200:
                organic = resp.json().get("organic", [])
                self.log(f"Search API returned {len(organic)} items for '{query}'", "info")
                return organic
            else:
                self.log(f"Search API error: HTTP {resp.status_code} - {resp.text[:120]}", "error")
        except Exception as e:
            self.log(f"Search API request failed: {e}", "error")
        return []

    def check_pause_and_stop(self) -> bool:
        """Returns True if stopped, otherwise waits if paused and returns False."""
        if self.stop_event.is_set():
            return True
        while self.pause_event.is_set():
            if self.stop_event.is_set():
                return True
            time.sleep(0.3)
        return False

    def run(self, place_queries: List[str], search_queries: List[str], output_file: str):
        self.is_running = True
        self.stop_event.clear()
        self.pause_event.clear()
        self.seen_names.clear()
        self.all_results.clear()
        self.total_phone_count = 0
        self.total_email_count = 0

        fieldnames = ["Name", "Category", "Phone Number", "Email", "Address", "Website", "Rating", "Reviews Count"]

        # Ensure output directory exists and prepare file with header
        out_dir = os.path.dirname(output_file)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        # Open file in append or write mode with immediate flushing
        csv_file = open(output_file, "w", newline="", encoding="utf-8")
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_file.flush()

        total_queries = len(place_queries) + len(search_queries)
        current_query_idx = 0

        self.log(f"Starting Scraper. Output destination: {output_file}", "success")
        self.log(f"Total Places Queries: {len(place_queries)} | Search Queries: {len(search_queries)}", "info")

        try:
            # ─────────────────────────────────────────
            # PHASE 1: Places API
            # ─────────────────────────────────────────
            if place_queries:
                self.log("═══ PHASE 1: Google Places Data (Serper Places API) ═══", "header")

            for query in place_queries:
                if self.check_pause_and_stop():
                    self.log("Scraping stopped by user.", "warning")
                    break

                current_query_idx += 1
                if self.on_progress:
                    self.on_progress(current_query_idx, total_queries, query)

                places = self.serper_places(query)

                for place in places:
                    if self.check_pause_and_stop():
                        break

                    name = clean_name(place.get("title", ""))
                    phone = place.get("phoneNumber", "") or extract_phone(place.get("address", ""))
                    website = place.get("website", "") or ""
                    address = place.get("address", "")
                    category = infer_category(query, place.get("category", ""))
                    rating = place.get("rating", "")
                    reviews_count = place.get("ratingCount", "")

                    norm_name = name.lower()
                    if not is_valid(name) or norm_name in self.seen_names:
                        continue
                    self.seen_names.add(norm_name)

                    # Email Extraction
                    email = ""
                    if self.extract_email and website:
                        self.log(f"Checking website for email: {name} ({website[:35]}...)", "info")
                        email = get_email_from_site(website)

                    if phone:
                        self.total_phone_count += 1
                    if email:
                        self.total_email_count += 1

                    record = {
                        "Name": name,
                        "Category": category,
                        "Phone Number": phone,
                        "Email": email,
                        "Address": address,
                        "Website": website,
                        "Rating": rating,
                        "Reviews Count": reviews_count,
                    }

                    self.all_results.append(record)
                    csv_writer.writerow(record)
                    csv_file.flush()

                    if self.on_record:
                        self.on_record(record)
                    self.update_stats()

                    self.log(f"✔ Found: {name} | Phone: {phone or 'N/A'} | Email: {email or 'N/A'}", "success")
                    time.sleep(self.request_delay)

                time.sleep(self.query_delay)

            # ─────────────────────────────────────────
            # PHASE 2: Search API
            # ─────────────────────────────────────────
            if not self.stop_event.is_set() and search_queries:
                self.log("═══ PHASE 2: Search Snippet Extraction (Serper Search API) ═══", "header")

            for query in search_queries:
                if self.check_pause_and_stop():
                    self.log("Scraping stopped by user.", "warning")
                    break

                current_query_idx += 1
                if self.on_progress:
                    self.on_progress(current_query_idx, total_queries, query)

                organic = self.serper_search(query, num=10)

                for item in organic:
                    if self.check_pause_and_stop():
                        break

                    title = clean_name(item.get("title", ""))
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")
                    phone = extract_phone(snippet)
                    email_in_snippet = EMAIL_RE.findall(snippet)

                    domain = link.split("/")[2] if "//" in link else ""
                    if any(d in domain for d in SKIP_DOMAINS):
                        continue

                    norm_title = title.lower()
                    if not is_valid(title) or norm_title in self.seen_names:
                        continue
                    self.seen_names.add(norm_title)

                    email = ""
                    if email_in_snippet:
                        email = email_in_snippet[0]
                    elif self.extract_email and link:
                        self.log(f"Scanning website: {link[:35]}...", "info")
                        email = get_email_from_site(link)

                    if phone:
                        self.total_phone_count += 1
                    if email:
                        self.total_email_count += 1

                    record = {
                        "Name": title,
                        "Category": infer_category(query),
                        "Phone Number": phone,
                        "Email": email,
                        "Address": "Location from search snippet",
                        "Website": link,
                        "Rating": "",
                        "Reviews Count": "",
                    }

                    self.all_results.append(record)
                    csv_writer.writerow(record)
                    csv_file.flush()

                    if self.on_record:
                        self.on_record(record)
                    self.update_stats()

                    self.log(f"✔ Found: {title} | Phone: {phone or 'N/A'} | Email: {email or 'N/A'}", "success")
                    time.sleep(self.request_delay)

                time.sleep(self.query_delay)

        finally:
            csv_file.close()
            self.is_running = False
            total_count = len(self.all_results)
            self.log(f"🏁 Finished! Total records collected: {total_count} (Saved in: {output_file})", "success")
            if self.on_finish:
                self.on_finish(total_count, output_file)

    def pause(self):
        self.pause_event.set()
        self.log("Scraping paused.", "warning")

    def resume(self):
        self.pause_event.clear()
        self.log("Scraping resumed.", "info")

    def stop(self):
        self.stop_event.set()
        self.pause_event.clear()
        self.log("Stop request received, wrapping up...", "warning")
