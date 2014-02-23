import json
from google.appengine.api import urlfetch
from google.appengine.api import mail
from muninn.models import AgentStore
import logging
from jinja2 import Template

# conditions for an agent to run.
# e.g. if an agent requires ALL_SOURCE_EVENTS, then it can only run
# once all of its sources have queued events
ALL_SOURCE_EVENTS = 1
ANY_SOURCE_EVENTS = 2
NO_SOURCE_EVENTS = 3

class Agent(object):
    can_generate_events = True
    can_receive_events = True
    default_config = {}

    @classmethod
    def new(cls, name, config=None, source_agents=None):
        if config is None:
            config = cls.default_config
        return AgentStore.new(
            name, cls, source_agents=source_agents,
            config=config)

    @classmethod
    def run(self, events, config, last_run):
        '''
        Implement logic here for running an agent.
        Any return values will be used as event data to be queued
        if the agent's `can_generate_events' is set to True.
        '''
        raise NotImplementedError()

    @classmethod
    def _parse_agents_class_name(cls, agents):
        '''
        Returns a list of Agents' fully qualified class names.
        '''
        parsed_agents = []
        print type(cls)
        for agent in agents:
            if isinstance(agent, (str, unicode)):
                parsed_agents.append(agent)
            elif isinstance(agent, AgentStore):
                parsed_agents.append(agent.type)
            elif issubclass(agent, cls):
                parsed_agents.append(agent.__module__ + '.' + agent.__name__)
        return parsed_agents



class URLFetchAgent(Agent):
    def _extract_json_data(self, data, expression):
        jsonpath_expr = parse(expression)
        return jsonpath_expr.find(data)

    def _read_json(self, result, config):
        data = json.loads(result.content)
        return data
        extract_config = config["extract"]

        if type(extract_config) is basestring:
            return self._extract_json_data(data, extract_config)
        else:
            tmp_responses = {}
            for key, expression in extract_config:
                tmp_responses[key] = self._extract_json_data(data, expression)


    def read_xml(self, result, config):
        raise NotImplementedError()

    @classmethod
    def run(self, events, config, last_run):
        method = urlfetch.GET if config.get("method", "GET").upper() == "GET" else urlfetch.POST
        response_kind = config.get("type", "JSON").upper()

        result = urlfetch.fetch(url=config["url"],
                                method=method)

        if result.status_code != 200:
            logging.error('FETCH failed: %s' % result.status_code)
            return

        if response_kind == "json":
            return self._read_json(result, config)
        else:
            return self._read_xml(result, config)


class PrintEventsAgent(Agent):
    can_generate_events = False

    @classmethod
    def run(self, events, config, last_run):
        for event in events:
            logging.info(event.data)


class MailAgent(Agent):
    can_generate_events = False

    @classmethod
    def run(self, events, config, last_run):
        template = Template(config.get("template_body"))
        body = template.render(events=events)
        template = Template(config.get("template_subject", "New events"))
        subject = template.render(events=events)

        mail.send_mail(sender=config.get("sender", "jeremi@collabspot.com"),
              to=config.get("to", "john@collabspot.com"),
              subject=subject,
              body=body)
