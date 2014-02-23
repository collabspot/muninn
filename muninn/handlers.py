import webapp2
import jinja2
import os

from muninn.agents import Agent, URLFetchAgent, PrintEventsAgent,\
     MailAgent
from muninn.agents.hipchat import HipchatAgent
from muninn.models import AgentStore


templates = jinja2.Environment(loader=jinja2.FileSystemLoader(
    os.path.join(os.path.dirname(__file__), 'templates')
))

class BaseHandler(webapp2.RequestHandler):
    pass


class TestAgents(BaseHandler):
    def get(self):
        urlfetchagent = URLFetchAgent.new(
            'IP Fetcher',
            config={
                'url': 'http://ip.jsontest.com',
                'extract': {
                    'ip': '$.ip',
                    'titi': '$.ip'
                }
            })

        printagent = PrintEventsAgent.new(
            'Print Agent',
            source_agents=[urlfetchagent])

        #HipchatAgent.new(
        #    'Hipchat Agent',
        #    config={
        #        'token': 'XYZ',
        #        'template_message': 'The IP is {{ data[0].ip }}',
        #        'room_id': '122569'
        #    },
        #    source_agents=[urlfetchagent])


class RunAllAgents(BaseHandler):
    def get(self):
        agents = AgentStore.all()
        self.response.content_type = 'text/plain'
        for agent in agents:
            self.response.out.write('Running ' + agent.name + '\n')
            agent.run()


class ListAllAgents(BaseHandler):
    def get(self):
        agents = AgentStore.all()
        template = templates.get_template('list_all_agents.html')
        return self.response.out.write(template.render({'agents': agents}))


class AddAgent(BaseHandler):
    def get(self):
        # TODO: don't hard code this dict
        registered_agents = {
            'URL Fetch Agent': Agent._agent_class_name(URLFetchAgent),
            'Print Events Agent': Agent._agent_class_name(PrintEventsAgent),
            'Mail Agent': Agent._agent_class_name(MailAgent)
        }


app = webapp2.WSGIApplication([
    ('/agents/test/?', TestAgents),
    ('/agents/all/run/?', RunAllAgents),
    ('/agents/all/?', ListAllAgents),
    ('/agents/add/?', AddAgent),
], debug=True)
