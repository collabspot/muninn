import webapp2

from muninn.agents import Agent, URLFetchAgent, PrintEventsAgent
from muninn.models import AgentStore


class BaseHandler(webapp2.RequestHandler):
    pass



class TestAgents(BaseHandler):
    def get(self):
        urlfetchagent = URLFetchAgent.new(
            'IP Fetcher',
            config={
                'url': 'http://ip.jsontest.com'
            })

        printagent = PrintEventsAgent.new(
            'Print Agent',
            source_agents=[urlfetchagent])


class RunAllAgents(BaseHandler):
    def get(self):
        agents = AgentStore.all()
        self.response.content_type = 'text/plain'
        for agent in agents:
            self.response.out.write('Running ' + agent.name + '\n')
            agent.run()


app = webapp2.WSGIApplication([
    ('/agents/test/?', TestAgents),
    ('/agents/all/run/?', RunAllAgents),
], debug=True)
