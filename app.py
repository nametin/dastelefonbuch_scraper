from modules.selenium_module import SeleniumModule
from modules.beautifulsoup_module import BeautifulSoupModule
from modules.excel_module import ExcelModule

class Main:

    bot = SeleniumModule()
    elements = bot.find_entry_elements()
    links = bot.get_links(elements)

    bot.close()

    extracted_data = []

    bs = BeautifulSoupModule()
    for link in links :
        extracted_data.append(bs.find_info(link))

    em = ExcelModule("data.xlsx")
    em.add_headers(["Name", "Address", "Telephone Number", "Website Address", "Email Address"])

    for data in extracted_data:
        em.add_row(data)

    em.save_file()


if __name__ == "__main__":
    main = Main()
