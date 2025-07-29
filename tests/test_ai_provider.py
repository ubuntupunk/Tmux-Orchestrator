
import unittest
from unittest.mock import patch, MagicMock, mock_open
import yaml
import sys
import os
import subprocess

# Add the parent directory to the Python path to allow importing ai_provider
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_provider import AIOrchestrator, AIProvider, AIConfig

class TestAIOrchestrator(unittest.TestCase):

    def setUp(self):
        # Create a dummy config file for testing
        self.config_data = {
            'default_provider': 'gemini',
            'providers': {
                'claude': {'type': 'interactive'},
                'rovodev': {'type': 'cli', 'command': 'acli rovodev run'},
                'gemini': {'type': 'cli', 'command': 'gemini'}
            },
            'sessions': {
                'session1:0': {'provider': 'claude'}
            }
        }
        self.config_file = 'test_ai_config.yml'
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config_data, f)

    def tearDown(self):
        # Remove the dummy config file
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_load_config(self):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        self.assertEqual(orchestrator.config, self.config_data)

    def test_get_provider_for_session(self):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        
        # Test session with a specific provider
        provider = orchestrator.get_provider_for_session('session1', 0)
        self.assertEqual(provider, AIProvider.CLAUDE)

        # Test session without a specific provider (should use default)
        provider = orchestrator.get_provider_for_session('session2', 1)
        self.assertEqual(provider, AIProvider.GEMINI)


    @patch('subprocess.run')
    def test_send_message_claude(self, mock_subprocess_run):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        orchestrator.send_message_claude('session1', 0, 'Hello Claude')
        self.assertEqual(mock_subprocess_run.call_count, 2)

    @patch('subprocess.run')
    def test_send_message_rovodev(self, mock_subprocess_run):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        orchestrator.send_message_rovodev('session1', 0, 'Hello Rovodev')
        self.assertEqual(mock_subprocess_run.call_count, 2)

    @patch('subprocess.run')
    def test_send_message_gemini(self, mock_subprocess_run):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        orchestrator.send_message_gemini('session1', 0, 'Hello Gemini')
        self.assertEqual(mock_subprocess_run.call_count, 2)

    @patch.object(AIOrchestrator, 'send_message_claude', return_value=True)
    def test_send_message_dispatcher_claude(self, mock_send_message_claude):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        orchestrator.send_message('session1', 0, 'test', AIProvider.CLAUDE)
        mock_send_message_claude.assert_called_with('session1', 0, 'test')

    def test_configure_session(self):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        orchestrator.configure_session('session2', 1, AIProvider.ROVODEV)
        self.assertEqual(orchestrator.config['sessions']['session2:1']['provider'], 'rovodev')


    def test_list_sessions(self):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        sessions = orchestrator.list_sessions()
        self.assertEqual(sessions, self.config_data['sessions'])

    @patch('subprocess.run')
    def test_start_interactive_session(self, mock_subprocess_run):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        orchestrator.start_interactive_session('session1', 0, AIProvider.GEMINI)
        mock_subprocess_run.assert_called_with(['tmux', 'send-keys', '-t', 'session1:0', 'gemini', 'Enter'], check=True)


    @patch('subprocess.run')
    def test_send_message_rovodev_options(self, mock_subprocess_run):
        self.config_data['providers']['rovodev']['options'] = {
            'shadow': True,
            'verbose': True,
            'yolo': True,
            'restore': True
        }
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config_data, f)
        orchestrator = AIOrchestrator(config_file=self.config_file)
        orchestrator.send_message_rovodev('session1', 0, 'Hello Rovodev')
        self.assertEqual(mock_subprocess_run.call_count, 2)
        # Check that the options were included in the command string
        self.assertIn('--shadow', mock_subprocess_run.call_args_list[0].args[0][-1])

    @patch('subprocess.run')
    def test_send_message_gemini_options(self, mock_subprocess_run):
        self.config_data['providers']['gemini']['options'] = {
            'model': 'gemini-pro',
            'sandbox': True,
            'all_files': True,
            'yolo': True
        }
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config_data, f)
        orchestrator = AIOrchestrator(config_file=self.config_file)
        orchestrator.send_message_gemini('session1', 0, 'Hello Gemini')
        self.assertEqual(mock_subprocess_run.call_count, 2)
        # Check that the options were included in the command string
        self.assertIn('-m gemini-pro', mock_subprocess_run.call_args_list[0].args[0][-1])

    def test_load_default_config(self):
        # Test the case where the config file does not exist
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        orchestrator = AIOrchestrator(config_file=self.config_file)
        self.assertEqual(orchestrator.config['default_provider'], 'claude')

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd'))
    def test_send_message_claude_error(self, mock_subprocess_run):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        result = orchestrator.send_message_claude('session1', 0, 'Hello Claude')
        self.assertFalse(result)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd'))
    def test_send_message_rovodev_error(self, mock_subprocess_run):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        result = orchestrator.send_message_rovodev('session1', 0, 'Hello Rovodev')
        self.assertFalse(result)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd'))
    def test_send_message_gemini_error(self, mock_subprocess_run):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        result = orchestrator.send_message_gemini('session1', 0, 'Hello Gemini')
        self.assertFalse(result)

    def test_send_message_unknown_provider(self):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        result = orchestrator.send_message('session1', 0, 'test', 'unknown')
        self.assertFalse(result)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd'))
    def test_start_interactive_session_error(self, mock_subprocess_run):
        orchestrator = AIOrchestrator(config_file=self.config_file)
        result = orchestrator.start_interactive_session('session1', 0, AIProvider.GEMINI)
        self.assertFalse(result)

from ai_provider import main

class TestAIProviderMain(unittest.TestCase):

    @patch('ai_provider.AIOrchestrator')
    def test_main_success(self, MockAIOrchestrator):
        # Mock the orchestrator instance and its send_message method
        mock_orchestrator_instance = MockAIOrchestrator.return_value
        mock_orchestrator_instance.send_message.return_value = True

        with self.assertRaises(SystemExit) as cm:
            main(['ai_provider.py', 'session1:0', 'Hello', 'gemini'])
        self.assertEqual(cm.exception.code, 0)

    def test_main_unknown_provider(self):
        with self.assertRaises(SystemExit) as cm:
            main(['ai_provider.py', 'session1:0', 'Hello', 'unknown'])
        self.assertEqual(cm.exception.code, 1)

    def test_main_invalid_session_format(self):
        with self.assertRaises(SystemExit) as cm:
            main(['ai_provider.py', 'session1', 'Hello'])
        self.assertEqual(cm.exception.code, 1)

    def test_main_not_enough_args(self):
        with self.assertRaises(SystemExit) as cm:
            main(['ai_provider.py'])
        self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
