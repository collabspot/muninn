import logging
import os
import json

import webapp2
import jinja2

from muninn.agents.default import EmailAgent, URLFetchAgent, PrintEventsAgent, WebhookAgent
from muninn.models import AgentStore, cls_from_name


templates = jinja2.Environment(loader=jinja2.FileSystemLoader(
    os.path.join(os.path.dirname(__file__), 'templates')
))

class BaseHandler(webapp2.RequestHandler):
    pass


class TestAgents(BaseHandler):
    def get(self):
        #urlfetchagent = URLFetchAgent.new(
        #    'IP Fetcher',
        #    config={
        #        'url': 'http://ip.jsontest.com',
        #        'extract': {
        #            'ip': '$.ip',
        #            'titi': '$.ip'
        #        }
        #    })
#
        #printagent = PrintEventsAgent.new(
        #    'Print Agent',
        #    source_agents=[urlfetchagent])
#
        #spreadsheet_agent = GoogleSpreadsheetAgent.new("plop", config={
        #    'login': '',
        #    'password': '',
        #    'spreadsheet_key': '0Apa92hFWvHrldGs4akk4b2ZmU2ZZQnhQbVVuRnBqQ2c'
        #})

        urlfetchagent = URLFetchAgent.new(
            'IP Fetcher',
            config={
                'url': 'http://xkcd.com',
                'type': 'html',
                'extract': {
                    'url': {
                        'selector': "#comic img",
                        'attr': "src"
                    },
                    'title': {
                        'selector': "#comic img",
                        'attr': "title"
                    }
                }
            })
        printagent = PrintEventsAgent.new(
            'Print Agent',
            source_agents=[urlfetchagent])

        #HipchatAgent.new(
        #    'Hipchat Agent',
        #    config={
        #        'token': '',
        #        'template_message': 'Value of \'a\' is {{ data.a }}',
        #        'room_id': '122790'
        #    },
        #    source_agents=[spreadsheet_agent])
        #EmailAgent.new(
        #    'Summary Agent',
        #    config = {
        #        'to': 'jeremi23@gmail.com',
        #        'digest': '1',
        #        'template_message': """
        #            Youpi
        #            {% for event in data %}
        #                {{ event.a }} - {{ event.b }}
        #            {% endfor %}
        #        """
        #    },
        #    source_agents=[spreadsheet_agent]
        #)


class RunAllAgents(BaseHandler):
    def get(self):
        agents = AgentStore.all()
        self.response.content_type = 'text/plain'
        for agent in agents:
            try:
                self.response.out.write('Running ' + agent.name + '...')
                agent.run()
            except Exception, e:
                logging.exception(e)
                self.response.out.write('Failed. See logs.\n')
            else:
                self.response.out.write('Done.\n')


class ListAllAgents(BaseHandler):
    def get(self):
        agents = AgentStore.all()
        template = templates.get_template('list_all_agents.html')
        return self.response.out.write(template.render({'agents': agents, 'page_title': 'All Agents'}))


class AddAgent(BaseHandler):
    def get(self):
        # TODO: don't hard code this dict
        registered_agents = {
            'URL Fetch Agent': URLFetchAgent,
            'Print Events Agent': PrintEventsAgent,
            'Mail Agent': EmailAgent,
            'Webhook Agent': WebhookAgent
        }
        agents = AgentStore.all()
        template = templates.get_template('add_agent.html')
        return self.response.out.write(template.render({
            'registered_agents': registered_agents,
            'agents': agents,
            'page_title': 'Add Agent'
        }))

    def post(self):
        agent_type = self.request.get('agent_type')
        name = self.request.get('name')
        sources = self.request.get('sources')
        config = self.request.get('config')
        config = json.loads(config)
        sources = sources.split(',')
        sources = [s.strip() for s in sources]
        source_agents = AgentStore.query(
            AgentStore.name.IN(sources),
            AgentStore.is_active == True
        ).fetch()
        agent_cls = cls_from_name(agent_type)
        agent = agent_cls.new(name,
                              source_agents=source_agents,
                              config=config)
        template = templates.get_template('add_agent.html')
        return self.response.out.write(template.render({
            'agent': agent,
            'page_title': 'Add Agent'
        }))

app = webapp2.WSGIApplication([
    ('/muninn/admin/agents/test/?', TestAgents),
    ('/muninn/admin/agents/all/run/?', RunAllAgents),
    ('/muninn/admin/agents/all/?', ListAllAgents),
    ('/muninn/admin/agents/add/?', AddAgent),
], debug=True)
