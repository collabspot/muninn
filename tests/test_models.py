from __future__ import absolute_import
import datetime
import random
import unittest

from google.appengine.ext import testbed
from models import Agent, Event, AgentStore, SourceAgent


class TestAgent(Agent):
    @classmethod
    def run(cls, data):
        print data
        return {'event_data': data}


class MuteAgent(Agent):
    can_generate_events = False

    @classmethod
    def run(cls, data):
        return None


class AgentTestCase(unittest.TestCase):
    '''Tests for Agent model'''
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env('muninn')
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_create_agent(self):
        name = 'My Agent'
        agent = Agent.new(name=name)
        self.assertIsInstance(agent, AgentStore)
        self.assertEqual(agent.type, 'models.Agent')
        agent2 = TestAgent.new(name=name)
        self.assertEqual(agent2.type, 'tests.test_models.TestAgent')
        agents = AgentStore.all(name=name,
                                type=agent.type)
        self.assertEqual(len(agents), 1)
        agents = AgentStore.all(name=name)
        self.assertEqual(len(agents), 2)

    def test_parse_agents_class_name(self):
        agents = ['Foo', 'Bar', Agent]
        self.assertEqual(['Foo', 'Bar', 'models.Agent'],
                         Agent._parse_agents_class_name(agents))


class AgentStoreTestCase(unittest.TestCase):
    '''Tests for Agent model'''
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env('muninn')
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_list_agents(self):
        for i in range(10):
            agent = AgentStore()
            agent.put()
        agent = AgentStore.query().get()
        agent.is_active = False
        agent.put()
        agents = AgentStore.all()
        self.assertEqual(len(agents), 9)

    def test_agent_events(self):
        source_agent = Agent.new(name='Source Agent')
        listening_agent = Agent.new(name='Listening Agent',
                                    source_agents=[source_agent])
        listening_agent_2 = Agent.new(name='Listening Agent 2',
                                      source_agents=None)
        source_agent.queue_event({'event_field': 'event_value'})
        self.assertIn(listening_agent,
                      SourceAgent.get_listening_agents(source_agent))
        events = listening_agent.check_events()
        self.assertEqual(len(events), 1)
        events = listening_agent_2.check_events()
        self.assertEqual(len(events), 0)

    def test_agent_sources(self):
        source_agent1 = TestAgent.new(name='Source Agent 1')
        source_agent2 = TestAgent.new(name='Source Agent 2')
        mute_agent = MuteAgent.new(name='Mute Agent')
        agent = TestAgent.new(name='Test Agent',
                              source_agents=[source_agent1, source_agent2, mute_agent])
        self.assertEqual(SourceAgent.get_source_agents(agent),
                         [source_agent1, source_agent2])

    def test_agent_run(self):
        source_agent1 = TestAgent.new(name='Source Agent 1')
        source_agent2 = TestAgent.new(name='Source Agent 2')
        agent = TestAgent.new(name='Test Agent',
                              source_agents=[source_agent1, source_agent2])
        listening_agent = TestAgent.new(name='Listening Agent',
                                        source_agents=[agent])
        source_agent1.queue_event(1)
        source_agent2.queue_event(2)
        agent.run()
        generated_events = Event.from_agent(agent)
        self.assertEqual([e.data for e in generated_events],
                         [{'event_data': 1}, {'event_data': 2}])
        self.assertEqual([e.target for e in generated_events],
                         [listening_agent.key, listening_agent.key])

if __name__ == '__main__':
    unittest.main()
