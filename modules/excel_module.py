# excel_module.py

import openpyxl

class ExcelModule:
    def __init__(self, filename):
        self.filename = filename 
        self.workbook = openpyxl.Workbook()
        self.sheet = self.workbook.active

    def add_headers(self, headers):
        self.sheet.append(headers)

    def add_row(self, data):
        self.sheet.append(data)

    def save_file(self):
        self.workbook.save(self.filename)
