import webapp2

from muninn.models import Agent


class BaseHandler(webapp2.RequestHandler):
    pass


class RunAllAgents(BaseHandler):
    def get(self):
        agents = Agent.all()
        self.response.content_type = 'text/plain'
        for agent in agents:
            self.response.out.write('Running ' + agent.name + '\n')
            agent.run()


app = webapp2.WSGIApplication([
    ('/agents/all/run/?', RunAllAgents),
], debug=True)
