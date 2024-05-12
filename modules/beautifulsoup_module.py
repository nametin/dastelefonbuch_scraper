import base64
from bs4 import BeautifulSoup
import requests

class BeautifulSoupModule:
    def __init__(self, links = None):
        self.links = links
        self.soup = None

    def fetch_page(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            self.soup = BeautifulSoup(response.text, 'html.parser')
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")

    def decode_cloudflare_email(self, encoded_email):
        hex_pairs = [encoded_email[i : i + 2] for i in range(0, len(encoded_email), 2)]

        key = int(hex_pairs[0], 16)

        decoded_chars = [chr(int(hp, 16) ^ key) for hp in hex_pairs[1:]]

        return "".join(decoded_chars)

    def find_info(self, link):
        self.fetch_page(link)

        main_info_section = self.soup.find(class_="maininfo")

        try:
            name = main_info_section.find(itemprop="name").get_text(strip=True)
        except:
            name = None
            
        try: 
            address_section = main_info_section.find(itemprop="address")
            street_address = address_section.find(itemprop="streetAddress").get_text(strip=True)
            street_number = address_section.contents[2].strip()  
            postal_code = address_section.find(itemprop="postalCode").get_text(strip=True)
            locality = address_section.find(itemprop="addressLocality").get_text(strip=True)
            region = address_section.contents[-1].strip() 
            address = f"{street_address} {street_number} {postal_code} {locality} {region}"
        except :
            address = None
        
        try:  
            telephone_section = main_info_section.find(class_="nr")

            telephone_number = "".join(
                s for s in telephone_section.find_all(text=True, recursive=True) if s.parent.get('class') != ['hide']
            ).replace("…", "")
        except:
            telephone_number = None
            
        
        buttons_section = main_info_section.find(class_="buttons")
        
        try:
            
            website_link = buttons_section.find('a', rel="noopener")
            if website_link:
                website_address = website_link["href"]
            else:
                website_address = None
        except:
            website_address = None
        
        
        try: 
            email_icon = buttons_section.find(class_="icon icon_email")
            if email_icon:
                email_section = email_icon.parent
                email_address = email_section["href"].replace("mailto:", "")
                if email_address.startswith('/cdn-cgi/l/email-protection'):
                    email_address = email_address.replace(
                        "/cdn-cgi/l/email-protection#", ""
                    )

                    email_address = self.decode_cloudflare_email(email_address)
            else:
                email_address = None
        except:
            email_address = None
            
        return name, address, telephone_number, website_address, email_address

    def parse_content(self, tag, class_name=None):
        if self.soup:
            if class_name:
                return self.soup.find_all(tag, class_=class_name)
            else:
                return self.soup.find_all(tag)
        else:
            print("Soup object not initialized. Call fetch_page() first.")
            return None
