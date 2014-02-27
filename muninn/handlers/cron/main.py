import logging
import datetime
import webapp2

from google.appengine.ext import ndb
from muninn.models import AgentStore


class BaseHandler(webapp2.RequestHandler):
    pass


class RunAgents(BaseHandler):
    def get(self):
        now = datetime.datetime.now()
        agents = AgentStore.due(now)
        for agent in agents:
            agent.run_taskqueue()


class RunAgentTaskHandler(BaseHandler):
    def get(self, key):
        agent = ndb.Key(urlsafe=str(key)).get()
        logging.debug('Running ' + agent.name)
        agent.run()
        logging.debug('Done')


app = webapp2.WSGIApplication([
    ('/cron/agents/run/?', RunAgents),
    ('/cron/agents/(.*)/run/?', RunAgentTaskHandler)
])
