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
    default_config = {}

    @classmethod
    def new(cls, name, config=None, source_agents=None):
        if config is None:
            config = cls.default_config
        return AgentStore.new(
            name, cls, source_agents=source_agents,
            config=config)

    @classmethod
    def run(cls, data, **kwargs):
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
