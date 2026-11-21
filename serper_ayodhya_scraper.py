"""
Smart Business & Lead Scraper (Serper Engine)
=============================================
Strategy:
  1. Serper PLACES API  → Google Maps se seedha name + phone + address + website + rating
  2. Serper SEARCH API  → Snippets se phone + email extract karo
  3. Website scraping   → Official website se email dhundho (optional)

Default Mode: Launches Modern Tkinter UI
CLI Mode: Run with '--cli' flag for headless command-line scraping:
    python serper_ayodhya_scraper.py --cli
    python serper_ayodhya_scraper.py --cli --category "Hospitals & Healthcare" --location "Ayodhya"
"""

import sys
import argparse
import requests
import re
import csv
import json
import time

from scraper_core import (
    DEFAULT_API_KEY,
    generate_smart_queries,
    POPULAR_CATEGORIES,
    PRESET_GHAZIABAD_SCHOOLS,
    PRESET_AYODHYA_HOSPITALS
)

# ─────────────────────────────────────────────
# 1. API KEY & CONFIGURATION (EXACT & UNCHANGED)
# ─────────────────────────────────────────────
API_KEY = "abb6e72105a832dee04d7a18dd103b387fe1a7ea"

PLACES_URL = "https://google.serper.dev/places"   # structured local data
SEARCH_URL = "https://google.serper.dev/search"   # organic search fallback

HEADERS = {
    "X-API-KEY":    API_KEY,
    "Content-Type": "application/json"
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}|0\d{2,4}[\-\s]?\d{6,8}")

JUNK_EMAIL = [
    "sentry", "wixpress", "example.com", "cloudflare", "amazonaws",
    "googleapis", "facebook", "schema.org", "w3.org", ".png", ".jpg",
    ".svg", ".webp", "noreply", "no-reply", "bootstrap", "jquery"
]

PLACE_QUERIES = PRESET_GHAZIABAD_SCHOOLS["places"]
SEARCH_QUERIES = PRESET_GHAZIABAD_SCHOOLS["search"]


# ═══════════════════════════════════════════
# 1. Serper PLACES API — main data source
# ═══════════════════════════════════════════

def serper_places(query):
    """
    Google Maps local business data.
    Returns list of places with: title, address, phoneNumber, website, category, rating, ratingCount
    """
    payload = json.dumps({
        "q":   query,
        "gl":  "in",
        "hl":  "en",
    })
    try:
        resp = requests.post(PLACES_URL, headers=HEADERS, data=payload, timeout=20)
        if resp.status_code == 200:
            data   = resp.json()
            places = data.get("places", [])
            print(f"     Places API → {len(places)} results")
            return places
        else:
            print(f"     Places API error: HTTP {resp.status_code} → {resp.text[:100]}")
    except Exception as e:
        print(f"     Places API exception: {e}")
    return []


# ═══════════════════════════════════════════
# 2. Serper SEARCH API — snippet extraction
# ═══════════════════════════════════════════

def serper_search(query, num=10):
    payload = json.dumps({"q": query, "gl": "in", "hl": "en", "num": num})
    try:
        resp = requests.post(SEARCH_URL, headers=HEADERS, data=payload, timeout=20)
        if resp.status_code == 200:
            organic = resp.json().get("organic", [])
            print(f"     Search API → {len(organic)} results")
            return organic
        print(f"     Search API error: HTTP {resp.status_code}")
    except Exception as e:
        print(f"     Search API exception: {e}")
    return []


# ═══════════════════════════════════════════
# 3. Website scraper — email only
# ═══════════════════════════════════════════

def get_email_from_site(url, timeout=7):
    if not url:
        return ""
    base  = url.rstrip("/")
    pages = [base, base + "/contact", base + "/contact-us", base + "/about-us"]
    for page in pages:
        try:
            r = requests.get(page, timeout=timeout, headers=BROWSER_HEADERS)
            if r.status_code != 200:
                continue
            found = EMAIL_RE.findall(r.text)
            clean = [e for e in set(found)
                     if not any(j in e.lower() for j in JUNK_EMAIL)]
            if clean:
                return clean[0]
        except Exception:
            continue
    return ""


# ═══════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════

def extract_phone(text):
    for p in PHONE_RE.findall(text or ""):
        if len(re.sub(r"\D", "", p)) >= 10:
            return p.strip()
    return ""


def clean_name(name):
    # Strip aggregator suffixes from titles
    name = re.sub(
        r"\s*[-|:]\s*(?:JustDial|Shiksha|Collegedunia|Careers360|GetMyUni|Edustoke|UniApply|Sulekha|Google|Facebook).*$",
        "",
        name or "",
        flags=re.IGNORECASE
    )
    return name.strip()


def is_valid(name):
    if not name or len(name) < 3 or len(name) > 130:
        return False
    # Filter out generic listicle/directory titles
    skip = [
        "justdial", "shiksha", "collegedunia", "careers360", "edustoke",
        "sulekha", "advertisement", "wikipedia", "youtube", "top 10",
        "top 20", "best schools", "best colleges", "list of", "fee structure"
    ]
    return not any(s in name.lower() for s in skip)


def infer_category(query, place_category=""):
    if place_category:
        return place_category
    q_low = query.lower()
    if any(k in q_low for k in ["college", "university", "mba", "polytechnic", "degree", "b.ed"]):
        return "College / University"
    if any(k in q_low for k in ["hospital", "clinic", "dental", "eye", "pathology", "diagnostic"]):
        return "Hospital / Healthcare"
    if any(k in q_low for k in ["school", "preschool", "cbse", "icse", "convent"]):
        return "School"
    return "Organization / Business"


# ═══════════════════════════════════════════
# CLI EXECUTION
# ═══════════════════════════════════════════

def run_cli(category=None, location=None, output=None):
    all_results = []
    seen_names  = set()

    if category and location:
        smart = generate_smart_queries(category, location)
        places_list = smart["places"]
        search_list = smart["search"]
        out_file = output or smart["filename"]
    else:
        places_list = PLACE_QUERIES
        search_list = SEARCH_QUERIES
        out_file = output or "ghaziabad_schools_colleges.csv"

    print("=" * 65)
    print(f"  🎯 Smart Lead Scraper (CLI Mode)")
    print(f"  📌 Target: {category or 'Schools & Colleges'} in {location or 'Ghaziabad'}")
    print(f"  📄 Output: {out_file}")
    print("=" * 65)

    # PHASE 1: Places API
    print("\n📌 PHASE 1: Google Places Data (via Serper Places API)")
    print("─" * 63)

    for query in places_list:
        print(f"\n  🔍 {query}")
        places = serper_places(query)

        for place in places:
            name     = clean_name(place.get("title", ""))
            phone    = place.get("phoneNumber", "") or extract_phone(place.get("address", ""))
            website  = place.get("website", "") or ""
            address  = place.get("address", "")
            cat      = infer_category(query, place.get("category", ""))
            rating   = place.get("rating", "")
            reviews  = place.get("ratingCount", "")

            norm_name = name.lower()
            if not is_valid(name) or norm_name in seen_names:
                continue
            seen_names.add(norm_name)

            print(f"  ✔ {name} | {phone or 'no phone'}")

            email = get_email_from_site(website) if website else ""

            all_results.append({
                "Name":          name,
                "Category":      cat,
                "Phone Number":  phone,
                "Email":         email,
                "Address":       address,
                "Website":       website,
                "Rating":        rating,
                "Reviews Count": reviews,
            })
            time.sleep(0.4)

        time.sleep(1)

    # PHASE 2: Search API
    print("\n📌 PHASE 2: Search Snippet Extraction")
    print("─" * 63)

    skip_domains = [
        "justdial.com", "shiksha.com", "collegedunia.com", "careers360.com",
        "edustoke.com", "uniapply.com", "getmyuni.com", "sulekha.com",
        "wikipedia.org", "indiamart.com", "quora.com", "facebook.com",
        "instagram.com", "youtube.com", "targetstudy.com", "icbse.com"
    ]

    for query in search_list:
        print(f"\n  🔍 {query}")
        organic = serper_search(query, num=10)

        for item in organic:
            title   = clean_name(item.get("title", ""))
            snippet = item.get("snippet", "")
            link    = item.get("link", "")
            phone   = extract_phone(snippet)
            email_in_snippet = EMAIL_RE.findall(snippet)

            domain = link.split("/")[2] if "//" in link else ""
            if any(d in domain for d in skip_domains):
                continue

            norm_title = title.lower()
            if not is_valid(title) or norm_title in seen_names:
                continue

            seen_names.add(norm_title)
            print(f"  ✔ {title} | {phone or 'no phone'}")

            email = email_in_snippet[0] if email_in_snippet else (get_email_from_site(link) if link else "")

            all_results.append({
                "Name":          title,
                "Category":      infer_category(query),
                "Phone Number":  phone,
                "Email":         email,
                "Address":       f"{location or 'Local area'}",
                "Website":       link,
                "Rating":        "",
                "Reviews Count": "",
            })
            time.sleep(0.4)

        time.sleep(1)

    # Save CSV
    fieldnames = ["Name", "Category", "Phone Number", "Email", "Address", "Website", "Rating", "Reviews Count"]
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\n{'=' * 65}")
    print(f"✅ Done! {len(all_results)} records saved → {out_file}")
    has_phone = sum(1 for r in all_results if r["Phone Number"])
    has_email = sum(1 for r in all_results if r["Email"])
    print(f"   With Phone : {has_phone}")
    print(f"   With Email : {has_email}")
    print("=" * 65)


def main():
    if "--cli" in sys.argv:
        parser = argparse.ArgumentParser(description="Smart Lead Scraper CLI")
        parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
        parser.add_argument("--category", type=str, default=None, help="Target business/category")
        parser.add_argument("--location", type=str, default=None, help="Target city/location")
        parser.add_argument("--output", type=str, default=None, help="Output CSV path")
        args = parser.parse_args()
        run_cli(category=args.category, location=args.location, output=args.output)
    else:
        try:
            from scraper_gui import main as gui_main
            gui_main()
        except ImportError:
            run_cli()


if __name__ == "__main__":
    main()
