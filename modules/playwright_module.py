# playwright_module.py

from typing import List, Optional, Iterable
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


class PlaywrightModule:
    def __init__(self, link: str, headless: bool = True, nav_timeout_ms: int = 45000):
        self.link = link
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=headless,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
            ],
        )
        self._context = self._browser.new_context(
            locale="de-DE",
            timezone_id="Europe/Berlin",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 900},
        )
        def _should_block(route):
            url = route.request.url.lower()
            if any(url.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".mp4", ".webm", ".avi")):
                return True
            if any(part in url for part in ("/analytics", "/gtm.js", "/tag/js")):
                return True
            if any(url.endswith(ext) for ext in (".woff", ".woff2", ".ttf", ".otf")):
                return True
            return False

        self._context.route("**/*", lambda route: route.abort() if _should_block(route) else route.continue_())

        self._page = self._context.new_page()
        self._page.set_default_timeout(nav_timeout_ms)

    def find_entry_elements(self) -> List[str]:
        self._goto(self.link)
        self._accept_cookies()

        self._expand_listing(max_clicks=50, pause_ms=800)

        links = self._collect_detail_links()
        uniq = list({u for u in links if u})
        return uniq

    def get_links(self, elements: Optional[Iterable[str]]) -> List[str]:
        if elements is None:
            return []
        return list(elements)

    def close(self):
        try:
            self._context.close()
        finally:
            try:
                self._browser.close()
            finally:
                self._pw.stop()

    def _goto(self, url: str):
        try:
            self._page.goto(url, wait_until="domcontentloaded")
        except PlaywrightTimeoutError:
            self._page.goto(url, wait_until="load")

    def _accept_cookies(self):
        selectors = [
            'button:has-text("Alle akzeptieren")',
            "#onetrust-accept-btn-handler",
            "[data-testid='uc-accept-all-button']",
            "button[mode='primary']:has-text('Akzeptieren')",
        ]

        for sel in selectors:
            try:
                el = self._page.locator(sel).first
                if el.is_visible():
                    el.click()
                    return
            except Exception:
                pass

        try:
            for frame in self._page.frames:
                url = (frame.url or "").lower()
                if any(k in url for k in ("consent", "usercentrics", "onetrust")):
                    for sel in selectors:
                        try:
                            el = frame.locator(sel).first
                            if el.is_visible():
                                el.click()
                                return
                        except Exception:
                            pass
        except Exception:
            pass  

    def _expand_listing(self, max_clicks: int = 50, pause_ms: int = 800):
        item_selector = "#entrycontainer .uppercover div[id^='entry_'], #entrycontainer .lowercover div[id^='entry_']"
        load_btn_selector = "button.loadbutton, .loadbutton"

        def count_items() -> int:
            try:
                return self._page.locator(item_selector).count()
            except Exception:
                return 0

        clicks = 0
        last_count = count_items()

        while clicks < max_clicks:
            try:
                if self._page.locator(".hitlistitem.endoflist.infinite-scroll-last.infinite-scroll-error").first.is_visible():
                    break
            except Exception:
                pass

            btn = self._page.locator(load_btn_selector).first
            if btn.is_visible():
                try:
                    btn.click()
                    self._page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
            else:
                try:
                    self._page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                except Exception:
                    pass

            self._page.wait_for_timeout(pause_ms)

            cur = count_items()
            if cur <= last_count:
                break
            last_count = cur
            clicks += 1

    def _collect_detail_links(self) -> List[str]:
        try:
            anchors = self._page.locator("#entrycontainer a.todetails")
            hrefs = anchors.evaluate_all("els => els.map(e => e.getAttribute('href'))")
            abs_hrefs = []
            base = self._page.url
            for h in hrefs:
                if not h:
                    continue
                if h.startswith("http"):
                    abs_hrefs.append(h)
                else:
                    try:
                        from urllib.parse import urljoin
                        abs_hrefs.append(urljoin(base, h))
                    except Exception:
                        abs_hrefs.append(h)
            return abs_hrefs
        except Exception:
            return []
