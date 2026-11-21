import scraper_core

res = scraper_core.generate_smart_queries("Gyms & Fitness Centers", "Noida", ["Sector 62", "Sector 18"])
print("Places count:", len(res["places"]))
print("Search count:", len(res["search"]))
print("Suggested filename:", res["filename"])
print("First place query:", res["places"][0])
