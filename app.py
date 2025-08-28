# app.py

from modules.beautifulsoup_module import BeautifulSoupModule
from modules.excel_module import ExcelModule
from modules.playwright_module import PlaywrightModule

from concurrent.futures import ThreadPoolExecutor, as_completed

def main():
    link = "https://www.dastelefonbuch.de/Suche/Yoga/Augsburg"

    bot = PlaywrightModule(link, headless=True)
    elements = bot.find_entry_elements()
    links = bot.get_links(elements)
    links = list({u for u in links if u})

    bot.close()

    extracted_data = []
    def worker(u):
        try:
            bs = BeautifulSoupModule()
            return bs.find_info(u)
        except Exception as e: 
            print(f"[worker] {u} -> {e}")
            return None
        
    with ThreadPoolExecutor(max_workers=min(6, len(links))) as ex:
        futures = [ex.submit(worker, u) for u in links]
        for f in as_completed(futures):
            res = f.result()
            if res:
                extracted_data.append(res)

    em = ExcelModule("data.xlsx")
    em.add_headers(["Name", "Address", "Telephone Number", "Website Address", "Email Address"])

    for data in extracted_data:
        if data and any(data):
            em.add_row(data)

    em.save_file()

if __name__ == "__main__":
    main()
