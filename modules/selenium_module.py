# selenium_module.py
# Deprecated, use playwright_module.py instead
# pip install selenium is required for this module.
"""
usage in app.py:
add from modules.selenium_module import SeleniumModule
and replace 
bot = PlaywrightModule(link = link, headless=False)
with
bot = SeleniumModule(link)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By

import time

class SeleniumModule:

    def __init__(self, link):
        self.driver = webdriver.Chrome()
        self.link = link

    def accept_cookies(self):
        try:
            self.driver.maximize_window()
            accept_button = self.driver.find_element(By.XPATH, '//*[@id="cmpwelcomebtnyes"]/a')
            accept_button.click()
        except:
            pass

    def scroll_page_until_change(self):
        previous_height = self.driver.execute_script("return document.body.scrollHeight")
        count = 0
        while count < 5:

            try:
                load_button = self.driver.find_element(By.CLASS_NAME, "loadbutton")
                load_button.click()
            except:
                pass

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height != previous_height:
                return True
            previous_height = new_height
            count += 1
        return False

    def scroll_to_end_of_page(self):
        while self.scroll_page_until_change():

            try:
                self.accept_cookies()
                end_element = self.driver.find_element(
                    By.CLASS_NAME,
                    "hitlistitem endoflist infinite-scroll-last infinite-scroll-error",
                )
                if end_element:
                    break

            except:
                pass

    def find_entry_elements(self):
        self.driver.get(self.link)
        
        time.sleep(2)
        self.accept_cookies()
        self.scroll_to_end_of_page()

        entry_container = self.driver.find_element(By.ID, "entrycontainer")
        uppercover = entry_container.find_element(By.CLASS_NAME, "uppercover")
        entry_elements = uppercover.find_elements(By.XPATH, ".//div[starts-with(@id, 'entry_')]")

        lowercover = entry_container.find_element(By.CLASS_NAME, "lowercover")
        entry_elements += lowercover.find_elements(By.XPATH, ".//div[starts-with(@id, 'entry_')]")
        
        return entry_elements

    def get_links(self, entry_elements):
        details_links = []
        for entry in entry_elements:
            try:
                detail_link_element = entry.find_element(By.XPATH, ".//a[contains(@class, 'todetails')]")
                details_links.append(detail_link_element.get_attribute('href'))
            except:
                details_links.append(None)

        return details_links

    def collect_entries(self):
        entries = self.driver.find_elements_by_class_name("entry hitlistitem  ")
        return entries

    def close(self):
        self.driver.quit()
