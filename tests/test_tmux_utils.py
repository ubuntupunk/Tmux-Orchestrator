
import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
import os

# Add the parent directory to the Python path to allow importing tmux_utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tmux_utils import TmuxOrchestrator, TmuxSession, TmuxWindow

class TestTmuxOrchestrator(unittest.TestCase):

    @patch('subprocess.run')
    def test_get_tmux_sessions(self, mock_subprocess_run):
        # Mock the output of the tmux list-sessions command
        mock_sessions_output = '''
session1:1
session2:0
'''
        # Mock the output of the tmux list-windows command
        mock_windows_output_s1 = '''
0:window1:1
1:window2:0
'''
        mock_windows_output_s2 = '''
0:window3:1
'''

        # Configure the mock to return different values for different calls
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=mock_sessions_output, stderr='', check_returncode=lambda: None),
            MagicMock(stdout=mock_windows_output_s1, stderr='', check_returncode=lambda: None),
            MagicMock(stdout=mock_windows_output_s2, stderr='', check_returncode=lambda: None)
        ]

        orchestrator = TmuxOrchestrator()
        sessions = orchestrator.get_tmux_sessions()

        # Assertions
        self.assertEqual(len(sessions), 2)

        # Check session 1
        self.assertEqual(sessions[0].name, 'session1')
        self.assertTrue(sessions[0].attached)
        self.assertEqual(len(sessions[0].windows), 2)
        self.assertEqual(sessions[0].windows[0].window_name, 'window1')
        self.assertTrue(sessions[0].windows[0].active)
        self.assertEqual(sessions[0].windows[1].window_name, 'window2')
        self.assertFalse(sessions[0].windows[1].active)

        # Check session 2
        self.assertEqual(sessions[1].name, 'session2')
        self.assertFalse(sessions[1].attached)
        self.assertEqual(len(sessions[1].windows), 1)
        self.assertEqual(sessions[1].windows[0].window_name, 'window3')
        self.assertTrue(sessions[1].windows[0].active)



    @patch('subprocess.run')
    def test_capture_window_content(self, mock_subprocess_run):
        mock_capture_output = 'Line 1\nLine 2\nLine 3'
        mock_subprocess_run.return_value = MagicMock(stdout=mock_capture_output, stderr='', check_returncode=lambda: None)

        orchestrator = TmuxOrchestrator()
        content = orchestrator.capture_window_content('session1', 0)

        self.assertEqual(content, mock_capture_output)
        mock_subprocess_run.assert_called_with(['tmux', 'capture-pane', '-t', 'session1:0', '-p', '-S', '-50'], capture_output=True, text=True, check=True)

    @patch('subprocess.run')
    def test_get_window_info(self, mock_subprocess_run):
        mock_display_message_output = 'window1:1:1:layout'
        mock_capture_output = 'Line 1\nLine 2\nLine 3'

        mock_subprocess_run.side_effect = [
            MagicMock(stdout=mock_display_message_output, stderr='', check_returncode=lambda: None),
            MagicMock(stdout=mock_capture_output, stderr='', check_returncode=lambda: None)
        ]

        orchestrator = TmuxOrchestrator()
        info = orchestrator.get_window_info('session1', 0)

        self.assertEqual(info['name'], 'window1')
        self.assertTrue(info['active'])
        self.assertEqual(info['panes'], 1)
        self.assertEqual(info['layout'], 'layout')
        self.assertEqual(info['content'], mock_capture_output)



    @patch('builtins.input', return_value='yes')
    @patch('subprocess.run')
    def test_send_keys_to_window_confirmed(self, mock_subprocess_run, mock_input):
        orchestrator = TmuxOrchestrator()
        orchestrator.safety_mode = True
        result = orchestrator.send_keys_to_window('session1', 0, 'echo "Hello"')

        self.assertTrue(result)
        mock_subprocess_run.assert_called_with(['tmux', 'send-keys', '-t', 'session1:0', 'echo "Hello"'], check=True)

    @patch('builtins.input', return_value='no')
    @patch('subprocess.run')
    def test_send_keys_to_window_cancelled(self, mock_subprocess_run, mock_input):
        orchestrator = TmuxOrchestrator()
        orchestrator.safety_mode = True
        result = orchestrator.send_keys_to_window('session1', 0, 'echo "Hello"')

        self.assertFalse(result)
        mock_subprocess_run.assert_not_called()

    @patch.object(TmuxOrchestrator, 'send_keys_to_window', return_value=True)
    @patch('subprocess.run')
    def test_send_command_to_window(self, mock_subprocess_run, mock_send_keys):
        orchestrator = TmuxOrchestrator()
        result = orchestrator.send_command_to_window('session1', 0, 'echo "Hello"')

        self.assertTrue(result)
        mock_send_keys.assert_called_with('session1', 0, 'echo "Hello"', True)
        mock_subprocess_run.assert_called_with(['tmux', 'send-keys', '-t', 'session1:0', 'C-m'], check=True)

    @patch.object(TmuxOrchestrator, 'get_tmux_sessions')
    @patch.object(TmuxOrchestrator, 'get_window_info')
    def test_get_all_windows_status(self, mock_get_window_info, mock_get_tmux_sessions):
        mock_get_tmux_sessions.return_value = [
            TmuxSession(name='session1', windows=[TmuxWindow(session_name='session1', window_index=0, window_name='w1', active=True)], attached=True)
        ]
        mock_get_window_info.return_value = {'name': 'w1', 'active': True, 'panes': 1, 'layout': 'layout', 'content': 'content'}

        orchestrator = TmuxOrchestrator()
        status = orchestrator.get_all_windows_status()

        self.assertIn('timestamp', status)
        self.assertEqual(len(status['sessions']), 1)
        self.assertEqual(status['sessions'][0]['name'], 'session1')
        self.assertEqual(len(status['sessions'][0]['windows']), 1)
        self.assertEqual(status['sessions'][0]['windows'][0]['name'], 'w1')

    @patch.object(TmuxOrchestrator, 'get_tmux_sessions')
    def test_find_window_by_name(self, mock_get_tmux_sessions):
        mock_get_tmux_sessions.return_value = [
            TmuxSession(name='session1', windows=[TmuxWindow(session_name='session1', window_index=0, window_name='w1', active=True)], attached=True),
            TmuxSession(name='session2', windows=[TmuxWindow(session_name='session2', window_index=1, window_name='w2', active=False)], attached=False)
        ]

        orchestrator = TmuxOrchestrator()
        matches = orchestrator.find_window_by_name('w1')

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], ('session1', 0))

    @patch.object(TmuxOrchestrator, 'get_all_windows_status')
    def test_create_monitoring_snapshot(self, mock_get_all_windows_status):
        mock_get_all_windows_status.return_value = {
            'timestamp': '2025-07-29T12:00:00',
            'sessions': [
                {
                    'name': 'session1',
                    'attached': True,
                    'windows': [
                        {
                            'index': 0,
                            'name': 'w1',
                            'active': True,
                            'info': {'content': 'line1\nline2'}
                        }
                    ]
                }
            ]
        }

        orchestrator = TmuxOrchestrator()
        snapshot = orchestrator.create_monitoring_snapshot()

        self.assertIn('Tmux Monitoring Snapshot', snapshot)
        self.assertIn('session1', snapshot)
        self.assertIn('w1', snapshot)
        self.assertIn('line1', snapshot)


    @patch('subprocess.run')
    def test_get_tmux_sessions_with_empty_lines(self, mock_subprocess_run):
        mock_sessions_output = '''
session1:1

session2:0
'''
        mock_windows_output = '''
0:window1:1

1:window2:0
'''
        mock_subprocess_run.side_effect = [
            MagicMock(stdout=mock_sessions_output, stderr='', check_returncode=lambda: None),
            MagicMock(stdout=mock_windows_output, stderr='', check_returncode=lambda: None),
            MagicMock(stdout=mock_windows_output, stderr='', check_returncode=lambda: None)
        ]
        orchestrator = TmuxOrchestrator()
        sessions = orchestrator.get_tmux_sessions()
        self.assertEqual(len(sessions), 2)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd'))
    def test_get_tmux_sessions_error(self, mock_subprocess_run):
        orchestrator = TmuxOrchestrator()
        sessions = orchestrator.get_tmux_sessions()
        self.assertEqual(sessions, [])

    @patch('subprocess.run')
    def test_capture_window_content_max_lines(self, mock_subprocess_run):
        orchestrator = TmuxOrchestrator()
        orchestrator.max_lines_capture = 10
        orchestrator.capture_window_content('session1', 0, num_lines=20)
        mock_subprocess_run.assert_called_with(['tmux', 'capture-pane', '-t', 'session1:0', '-p', '-S', '-10'], capture_output=True, text=True, check=True)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd'))
    def test_capture_window_content_error(self, mock_subprocess_run):
        orchestrator = TmuxOrchestrator()
        content = orchestrator.capture_window_content('session1', 0)
        self.assertIn('Error capturing window content', content)

    @patch('subprocess.run')
    def test_get_window_info_empty_output(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(stdout='', stderr='', check_returncode=lambda: None)
        orchestrator = TmuxOrchestrator()
        info = orchestrator.get_window_info('session1', 0)
        self.assertIsNone(info)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd'))
    def test_get_window_info_error(self, mock_subprocess_run):
        orchestrator = TmuxOrchestrator()
        info = orchestrator.get_window_info('session1', 0)
        self.assertIn('error', info)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd'))
    def test_send_keys_to_window_error(self, mock_subprocess_run):
        orchestrator = TmuxOrchestrator()
        orchestrator.safety_mode = False # Disable safety mode for this test
        result = orchestrator.send_keys_to_window('session1', 0, 'echo "Hello"', confirm=False)
        self.assertFalse(result)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'cmd'))
    def test_send_command_to_window_error(self, mock_subprocess_run):
        orchestrator = TmuxOrchestrator()
        orchestrator.safety_mode = False # Disable safety mode for this test
        result = orchestrator.send_command_to_window('session1', 0, 'echo "Hello"', confirm=False)
        self.assertFalse(result)


from tmux_utils import main as tmux_main

class TestTmuxUtilsMain(unittest.TestCase):

    @patch('tmux_utils.TmuxOrchestrator')
    def test_main(self, MockTmuxOrchestrator):
        mock_orchestrator_instance = MockTmuxOrchestrator.return_value
        mock_orchestrator_instance.get_all_windows_status.return_value = {'sessions': []}
        with patch('builtins.print') as mock_print:
            tmux_main()
            mock_print.assert_called_with(json.dumps({'sessions': []}, indent=2))

if __name__ == '__main__':
    unittest.main()

