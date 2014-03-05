from __future__ import absolute_import
import datetime
import time
import random
import unittest

from google.appengine.ext import testbed
from google.appengine.api import taskqueue
from muninn.models import Event, AgentStore, SourceAgent
from muninn.agents import Agent
from muninn.tests.test_agents import TestAgent, MuteAgent


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
        source_agent = Agent.new('Source Agent')
        listening_agent = Agent.new('Listening Agent',
                                    source_agents=[source_agent])
        listening_agent_2 = Agent.new('Listening Agent 2',
                                      source_agents=None)
        source_agent.add_event({'event_field': 'event_value'})
        source_agent._put_events_queue()
        self.assertIn(listening_agent,
                      SourceAgent.get_listening_agents(source_agent))
        events = listening_agent.receive_events()
        self.assertEqual(len(events), 1)
        events = listening_agent_2.receive_events()
        self.assertEqual(len(events), 0)

    def test_agent_properties(self):
        agent = TestAgent.new('Agent', config={'foo': 'bar'})
        self.assertEqual(agent.config, {'foo': 'bar'})
        self.assertTrue(agent.can_receive_events)
        self.assertTrue(agent.can_generate_events)

    def test_agent_sources(self):
        source_agent1 = TestAgent.new('Source Agent 1')
        source_agent2 = TestAgent.new('Source Agent 2')
        mute_agent = MuteAgent.new('Mute Agent')
        agent = TestAgent.new('Test Agent',
                              source_agents=[source_agent1, source_agent2, mute_agent])
        self.assertEqual(SourceAgent.get_source_agents(agent),
                         [source_agent1, source_agent2])

    def test_agent_due(self):
        in_two_hours = datetime.datetime.now() + datetime.timedelta(hours=2)

        agent1 = TestAgent.new('Agent 1', cron_entry='*/10 * * * *')
        agent2 = TestAgent.new('Agent 2', cron_entry='%s %s * * *' % (in_two_hours.minute, in_two_hours.hour))
        d1 = datetime.datetime.now() + datetime.timedelta(seconds=601)
        d2 = datetime.datetime.now() + datetime.timedelta(hours=3)
        d3 = datetime.datetime.now() - datetime.timedelta(seconds=10)
        a1 = AgentStore.due(d1)
        a2 = AgentStore.due(d2)
        a3 = AgentStore.due(d3)
        self.assertEqual(len(a1), 1)
        self.assertEqual(len(a2), 2)
        self.assertEqual(len(a3), 0)

    def test_agent_run(self):
        source_agent1 = TestAgent.new('Source Agent 1')
        source_agent2 = TestAgent.new('Source Agent 2')
        agent = TestAgent.new('Test Agent',
                              source_agents=[source_agent1, source_agent2])
        listening_agent = TestAgent.new('Listening Agent',
                                        source_agents=[agent])
        source_agent1.add_event(1)
        source_agent2.add_event(2)
        source_agent1._put_events_queue()
        source_agent2._put_events_queue()
        self.assertFalse(agent.last_run)
        agent.run()
        generated_events = Event.from_agent(agent)
        print generated_events
        self.assertEqual(generated_events[0].data,
                         {'event_data': [1, 2]})
        self.assertTrue(agent.last_run)

    def test_agent_run_taskqueue(self):
        source_agent1 = TestAgent.new('Source Agent 1')
        source_agent1.run_taskqueue()
        queue = taskqueue.Queue(name='agents')
        stats = queue.fetch_statistics()
        self.assertEqual(stats.tasks, 1)


if __name__ == '__main__':
    unittest.main()
