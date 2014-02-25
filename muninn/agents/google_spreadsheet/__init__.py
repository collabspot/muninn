from lib import add_lib_path
add_lib_path()

import gspread
from muninn.agents import Agent



class GoogleSpreadsheetAgent(Agent):

    def run(self, events):
        config = self.config
        gc = gspread.login(config.get("login"), config.get("password"))

        sheet = gc.open_by_key(config.get("spreadsheet_key"))
        worksheet = sheet.get_worksheet(config.get("worksheet", 0))
        for record in worksheet.get_all_records():
            self.agent.add_event(record)
