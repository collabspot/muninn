import webapp2

from muninn.models import Agent


class BaseHandler(webapp2.RequestHandler):
    pass


class RunAllAgents(BaseHandler):
    def get(self):
        agents = Agent.all()
        for agent in agents:
            agent.run()


app = webapp2.WSGIApplication([
    ('/agents/all/run/?', RunAllAgents),
], debug=True)
