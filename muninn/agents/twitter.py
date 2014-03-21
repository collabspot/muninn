import json
import logging
from config import TWITTER_SECRET_KEY, TWITTER_CLIENT_KEY
from muninn.agents import Agent
from muninn.agents.default import ReadFormat
from muninn.models import Credential
from requests_oauthlib import OAuth1Session


class TwitterAgent(Agent, ReadFormat):
    def do_request(self, event=None):
        config = self.config
        result = self.oauth.get("https://api.twitter.com/1.1/statuses/user_timeline.json")

        if result.status_code != 200:
            logging.error('FETCH failed: %s' % result.status_code)
            return

        for event in json.loads(result.content):
            logging.info(event)
            self.store.add_event(event)

    def run(self, events):
        credentials = Credential.query(Credential.name == "Twitter").get().data
        self.oauth = OAuth1Session(TWITTER_CLIENT_KEY,
                          client_secret=TWITTER_SECRET_KEY,
                          resource_owner_key=credentials["resource_owner_key"],
                          resource_owner_secret=credentials["resource_owner_secret"])

        if len(events) == 0:
            self.do_request()
        else:
            for event in events:
                self.do_request(event.data)
                event.done()