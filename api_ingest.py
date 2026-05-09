import requests
import duckdb
import urllib3
import time

# suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

con = duckdb.connect("data/citations.duckdb")

# make sure tables exist with field column
con.execute("CREATE TABLE IF NOT EXISTS works (id TEXT, title TEXT, year INT, field TEXT)")
con.execute("CREATE TABLE IF NOT EXISTS citations (citing_id TEXT, cited_id TEXT)")

def fetch_page(year, cursor="*"):
    url = (
        f"https://api.openalex.org/works"
        f"?filter=publication_year:{year}"
        f"&per_page=200"
        f"&cursor={cursor}"
        f"&select=id,title,publication_year,topics,referenced_works"
    )
    r = requests.get(url, verify=False)
    return r.json()

target_per_year = 200000
years = [2020, 2021, 2022, 2023, 2024]

for year in years:
    print(f"\n--- ingesting {year} ---")
    cursor = "*"
    kept = 0

    while kept < target_per_year:
        try:
            data = fetch_page(year, cursor)
        except Exception as e:
            print(f"  error: {e}, retrying in 5s...")
            time.sleep(5)
            continue

        results = data.get("results", [])
        if not results:
            break

        for work in results:
            work_id = work.get("id")
            title = work.get("title", "")
            pub_year = work.get("publication_year")
            refs = work.get("referenced_works", [])
            topics = work.get("topics", [])
            field = topics[0]["field"]["display_name"] if topics and "field" in topics[0] else "Unknown"

            if not work_id or not pub_year:
                continue

            con.execute("INSERT INTO works VALUES (?, ?, ?, ?)", [work_id, title, pub_year, field])
            for ref in refs:
                con.execute("INSERT INTO citations VALUES (?, ?)", [work_id, ref])

            kept += 1

        if kept % 10000 == 0:
            print(f"  {year}: kept {kept} papers so far...")

        # get next cursor
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            break

        # be polite to the API
        time.sleep(0.1)

    print(f"  {year}: done, kept {kept} papers")

print("\nall done.")