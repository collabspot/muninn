from muninn.models import AgentStore

# conditions for an agent to run.
# e.g. if an agent requires ALL_SOURCE_EVENTS, then it can only run
# once all of its sources have queued events
ALL_SOURCE_EVENTS = 1
ANY_SOURCE_EVENTS = 2
NO_SOURCE_EVENTS = 3


class Agent(object):
    can_generate_events = True
    can_receive_events = True

    def __init__(self, agent):
        self.store = agent
        self.config = agent.config or {}

    @classmethod
    def new(cls, name, cron_entry=None, config=None, source_agents=None, deduplicate_output_events=False):
        if config is None:
            config = {}
        return AgentStore.new(
            name, cls, cron_entry,
            source_agents=source_agents,
            config=config, deduplicate_output_events=deduplicate_output_events)

    def run(self, events):
        '''
        Implement logic here for running an agent.
        Any return values will be used as event data to be queued
        if the agent's `can_generate_events' is set to True.
        '''
        raise NotImplementedError()

    def receive_webhook(self, request, response):
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
