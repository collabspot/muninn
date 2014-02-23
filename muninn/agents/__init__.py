import json
import jsonpath
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
    def run(cls, events, store):
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
        for agent in agents:
            parsed_agents.append(cls._agent_class_name(agent))
        return parsed_agents

    @classmethod
    def _agent_class_name(cls, agent):
        if isinstance(agent, (str, unicode)):
            return agent
        elif isinstance(agent, AgentStore):
            return agent.type
        elif issubclass(agent, cls):
            return agent.fully_qualified_name()
        return None

    @classmethod
    def fully_qualified_name(cls):
        return cls.__module__ + '.' + cls.__name__



class URLFetchAgent(Agent):
    @classmethod
    def _read_json(cls, result, config):
        data = json.loads(result.content)
        responses = []
        #return data
        extract_config = config["extract"]
        logging.info(type(extract_config))

        if type(extract_config) is unicode:
            return jsonpath.jsonpath(data, extract_config)
        else:
            tmp_responses = {}
            for key, expression in extract_config.items():
                tmp_responses[key] = jsonpath.jsonpath(data, extract_config[key])

            keys = tmp_responses.keys()


            if len(keys) > 0 and len(tmp_responses[keys[0]]):
                for i in range(0, len(tmp_responses[keys[0]])):
                    response = dict()
                    for key in keys:
                        response[key] = tmp_responses[key][i]
                    responses.append(response)
            return responses

    @classmethod
    def _read_xml(cls, result, config):
        raise NotImplementedError()

    @classmethod
    def run(cls, events, config, store):
        method = urlfetch.GET if config.get("method", "GET").upper() == "GET" else urlfetch.POST
        response_kind = config.get("type", "JSON").upper()

        result = urlfetch.fetch(url=config["url"],
                                method=method)

        if result.status_code != 200:
            logging.error('FETCH failed: %s' % result.status_code)
            return

        if response_kind == "JSON":
            new_events = cls._read_json(result, config)
        else:
            new_events = cls._read_xml(result, config)

        for event in new_events:
            store.add_event(event)


class PrintEventsAgent(Agent):
    can_generate_events = False

    @classmethod
    def run(cls, events, config, last_run):
        for event in events:
            logging.info(event.data)


class MailAgent(Agent):
    can_generate_events = False

    @classmethod
    def run(cls, events, config, last_run):
        template = Template(config.get("template_body"))
        body = template.render(events=events)
        template = Template(config.get("template_subject", "New events"))
        subject = template.render(events=events)

        mail.send_mail(sender=config.get("sender", "jeremi@collabspot.com"),
              to=config.get("to", "john@collabspot.com"),
              subject=subject,
              body=body)
