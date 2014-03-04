import logging
from google.appengine.api import urlfetch
from lib import add_lib_path
from muninn.utils import slugify, force_unicode

add_lib_path()

import gspread
from muninn.agents import Agent


urlfetch.set_default_fetch_deadline(30)

class GoogleSpreadsheetAgent(Agent):
    """
    Example of configuration:
    {
        "login": "jeremi@collabspot.com",
        "password": "MY_PWD",
        "spreadsheet_key": "1pygz4jIJgAtUOkTAN8cUReWFwbJuF4W8bL13MKFXIZY"
    }

    """

    def run(self, events):
        config = self.config
        gc = gspread.login(config.get("login"), config.get("password"))

        sheet = gc.open_by_key(config.get("spreadsheet_key"))
        worksheet = sheet.get_worksheet(config.get("worksheet", 0))
        for record in worksheet.get_all_records():
            updated_records = {}
            #
            for key, value in record.items():
                updated_records[slugify(force_unicode(key))] = force_unicode(value)

            self.store.add_event(updated_records)
