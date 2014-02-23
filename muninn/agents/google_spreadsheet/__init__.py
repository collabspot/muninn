from muninn.agents import Agent
import gspread


class GoogleSpreadsheetAgent(Agent):

    @classmethod
    def run(cls, events, config, store):
        gc = gspread.login(config.get("login"), config.get("password"))

        sheet = gc.open_by_key(config.get("spreadsheet_key"))
        worksheet = sheet.get_worksheet(config.get("worksheet", 0))
        for record in worksheet.get_all_records():
            store.add_event(record)