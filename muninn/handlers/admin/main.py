import logging
import os
import json
from google.appengine.ext import ndb

import webapp2
import jinja2

from muninn.agents.default import EmailAgent, URLFetchAgent, PrintEventsAgent, WebhookAgent
from muninn.agents.google_spreadsheet import GoogleSpreadsheetAgent
from muninn.agents.hipchat import HipchatAgent
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
                logging.info('Running %s (%s) ...' % (agent.name, agent.key.id()))
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

class RedirectHandler(BaseHandler):
    def get(self):
        self.redirect("/admin/")

class ResetDedupHandler(BaseHandler):
    def get(self):
        agents = AgentStore.all()
        for agent in agents:
            if agent.dedup_hashs is not None:
                agent.dedup_hashs = []
                agent.put()


class AddAgent(BaseHandler):
    def get(self):
        # TODO: don't hard code this dict
        registered_agents = {
            'URL Fetch': URLFetchAgent,
            'Print Events console': PrintEventsAgent,
            'Mail': EmailAgent,
            'Webhook': WebhookAgent,
            "Google Spreadsheet": GoogleSpreadsheetAgent,
            "Hipchat": HipchatAgent
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
        sources = self.request.get_all('sources')
        config = self.request.get('config')
        cron = self.request.get('cron')
        deduplicate_output_events = self.request.get('deduplicate_output_events') == "1"
        if not config or len(config) == 0:
            config = "{}"
        config = json.loads(config)
        source_keys = [ndb.Key(urlsafe=source) for source in sources]
        source_agents = ndb.get_multi(source_keys)
        agent_cls = cls_from_name(agent_type)
        agent = agent_cls.new(name,
                              source_agents=source_agents,
                              config=config,
                              cron_entry=cron,
                              deduplicate_output_events=deduplicate_output_events)
        template = templates.get_template('add_agent.html')
        return self.response.out.write(template.render({
            'agent': agent,
            'page_title': 'Add Agent'
        }))

app = webapp2.WSGIApplication([
    ('/admin/run/?', RunAllAgents),
    ('/admin/?', ListAllAgents),
    ('/admin/add/?', AddAgent),
    ('/admin/reset_dedup/?', ResetDedupHandler),
    ('/', RedirectHandler),
], debug=True)
