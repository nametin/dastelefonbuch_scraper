# beautifulsoup_module.py

import base64
import re
from bs4 import BeautifulSoup, NavigableString
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BeautifulSoupModule:
    def __init__(self, links=None):
        self.links = links
        self.soup = None

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        })
        
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(max_retries=retry, pool_connections=50, pool_maxsize=50)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def fetch_page(self, url):
        try: 
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                self.soup = BeautifulSoup(response.text, 'lxml')
            else:
                print(f"Failed to retrieve the page. Status code: {response.status_code}")
        except Exception as e:
            print(f"[fetch] {url} -> {e}")
            self.soup = None

    def decode_cloudflare_email(self, encoded_email):
        hex_pairs = [encoded_email[i : i + 2] for i in range(0, len(encoded_email), 2)]

        key = int(hex_pairs[0], 16)

        decoded_chars = [chr(int(hp, 16) ^ key) for hp in hex_pairs[1:]]

        return "".join(decoded_chars)

    def _clean_text(self, s: str) -> str:
        if not s:
            return ""
        s = (s.replace("\u00a0", " ")   # NBSP
            .replace("…", "")
            .replace("\t", " ")
            .replace("\r", " ")
            .replace('"', " ")
            .strip())
        # ardışık boşlukları tek boşluğa indir
        return re.sub(r"\s{2,}", " ", s)
        
    def _normalize_phone_de(self, raw: str) -> str:
        if not raw:
            return ""
        return " ".join(raw.split())  

    def _extract_address(self, container) -> str | None:
        if not container:
            return None

        addr_el = container.select_one("address, [itemprop='address']")
        if not addr_el:
            return None

        addr = BeautifulSoup(str(addr_el), "lxml")

        for h in addr.select(".hide"):
            h.decompose()

        BR = "__BR__"
        for br in addr.find_all("br"):
            br.replace_with(NavigableString(f" {BR} "))
        raw = "".join(addr.strings).replace("\u00a0", " ")
        raw = re.sub(r"\s+", " ", raw).strip()
        parts = [p.strip() for p in raw.split(BR)]
        parts = [re.sub(r"\s*,\s*", ", ", p) for p in parts if p]  # ", " normalize

        parts = [re.sub(r"\s{2,}", " ", p) for p in parts]

        return ", ".join(parts) if parts else None

    def find_info(self, link):
        self.fetch_page(link)
        if not self.soup:
            print("[find_info] if not self.soup problem!!")
            return None, None, None, None, None

        main_info_section = self.soup.find(class_="maininfo")
        if not main_info_section:
            print("[find_info] if not main_info_section problem!!")
            return None, None, None, None, None

        # NAME
        name = None
        try:
            tag = main_info_section.find(attrs={"itemprop": "name"})
            if tag:
                name = self._clean_text(tag.get_text(strip=True))
        except Exception as e:
            print(f"[parse:name] {e}")

        # ADDRESS: pozisyon bazlı yerine itemprop hedefle
        address = None
        try:
            # addr = main_info_section.find(attrs={"itemprop": "address"})
            address = self._extract_address(main_info_section)
        except Exception as e:
            print(f"[parse:address] {e}")

        # PHONE
        telephone_number = None
        try:
            telsec = main_info_section.find(class_="nr")
            if telsec:
                visible_texts = []
                for t in telsec.find_all(string=True, recursive=True):
                    parent_classes = t.parent.get("class") or []
                    if parent_classes == ["hide"]:
                        continue
                    visible_texts.append(t)
                telephone_number = self._normalize_phone_de(self._clean_text("".join(visible_texts)))
        except Exception as e:
            print(f"[parse:phone] {e}")

        # BUTTONS
        website_address, email_address = None, None
        try:
            buttons = main_info_section.find(class_="buttons")
            if buttons:
                # Website
                link = buttons.find("a", rel="noopener")
                if link and link.get("href"):
                    website_address = self._clean_text(link["href"])
                # Email
                email_icon = buttons.find(class_="icon icon_email")
                if email_icon:
                    href = (email_icon.parent or {}).get("href", None)
                    if href:
                        href = href.replace("mailto:", "")
                        if href.startswith("/cdn-cgi/l/email-protection"):
                            href = href.replace("/cdn-cgi/l/email-protection#", "")
                            href = self.decode_cloudflare_email(href)
                        email_address = self._clean_text(href)
        except Exception as e:
            print(f"[parse:buttons] {e}")

        return name, address, telephone_number, website_address, email_address