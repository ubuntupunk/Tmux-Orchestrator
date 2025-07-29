#!/usr/bin/env python3

import subprocess
import json
import yaml
import os
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class AIProvider(Enum):
    CLAUDE = "claude"
    ROVODEV = "rovodev" 
    GEMINI = "gemini"

@dataclass
class AIConfig:
    provider: AIProvider
    session_name: str
    window_index: int
    provider_options: Dict = None
    
    def __post_init__(self):
        if self.provider_options is None:
            self.provider_options = {}

class AIOrchestrator:
    def __init__(self, config_file: str = "ai_config.yml"):
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load AI provider configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default configuration
            default_config = {
                'default_provider': 'claude',
                'providers': {
                    'claude': {
                        'type': 'interactive',
                        'command': None,  # Uses tmux send-keys
                        'options': {}
                    },
                    'rovodev': {
                        'type': 'cli',
                        'command': 'acli rovodev run',
                        'options': {
                            'shadow': False,
                            'verbose': False,
                            'yolo': False,
                            'restore': False
                        }
                    },
                    'gemini': {
                        'type': 'cli', 
                        'command': 'gemini',
                        'options': {
                            'model': 'gemini-2.5-pro',
                            'sandbox': False,
                            'all_files': False,
                            'yolo': False
                        }
                    }
                },
                'sessions': {}
            }
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def get_provider_for_session(self, session_name: str, window_index: int) -> AIProvider:
        """Determine which AI provider to use for a given session/window"""
        session_key = f"{session_name}:{window_index}"
        
        # Check if specific session has a configured provider
        if session_key in self.config.get('sessions', {}):
            provider_name = self.config['sessions'][session_key]['provider']
            return AIProvider(provider_name)
        
        # Use default provider
        default_provider = self.config.get('default_provider', 'claude')
        return AIProvider(default_provider)
    
    def send_message_claude(self, session_name: str, window_index: int, message: str) -> bool:
        """Send message to Claude using tmux send-keys (existing behavior)"""
        try:
            window_target = f"{session_name}:{window_index}"
            
            # Send the message
            cmd = ["tmux", "send-keys", "-t", window_target, message]
            subprocess.run(cmd, check=True)
            
            # Wait for UI to register
            time.sleep(0.5)
            
            # Send Enter
            cmd = ["tmux", "send-keys", "-t", window_target, "Enter"]
            subprocess.run(cmd, check=True)
            
            print(f"Message sent to Claude at {window_target}: {message}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error sending message to Claude: {e}")
            return False
    
    def send_message_rovodev(self, session_name: str, window_index: int, message: str) -> bool:
        """Send message to RovoDev using acli rovodev run"""
        try:
            window_target = f"{session_name}:{window_index}"
            provider_config = self.config['providers']['rovodev']
            options = provider_config.get('options', {})
            
            # Build command
            cmd = ["acli", "rovodev", "run"]
            
            # Add options
            if options.get('shadow', False):
                cmd.append("--shadow")
            if options.get('verbose', False):
                cmd.append("--verbose")
            if options.get('yolo', False):
                cmd.append("--yolo")
            if options.get('restore', False):
                cmd.append("--restore")
            
            # Add message
            cmd.append(message)
            
            # Send command to tmux window
            cmd_str = " ".join(cmd)
            tmux_cmd = ["tmux", "send-keys", "-t", window_target, cmd_str]
            subprocess.run(tmux_cmd, check=True)
            
            # Send Enter
            time.sleep(0.5)
            enter_cmd = ["tmux", "send-keys", "-t", window_target, "Enter"]
            subprocess.run(enter_cmd, check=True)
            
            print(f"RovoDev command sent to {window_target}: {cmd_str}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error sending message to RovoDev: {e}")
            return False
    
    def send_message_gemini(self, session_name: str, window_index: int, message: str) -> bool:
        """Send message to Gemini using gemini CLI"""
        try:
            window_target = f"{session_name}:{window_index}"
            provider_config = self.config['providers']['gemini']
            options = provider_config.get('options', {})
            
            # Build command
            cmd = ["gemini"]
            
            # Add options
            if 'model' in options:
                cmd.extend(["-m", options['model']])
            if options.get('sandbox', False):
                cmd.append("-s")
            if options.get('all_files', False):
                cmd.append("-a")
            if options.get('yolo', False):
                cmd.append("-y")
            
            # Add prompt
            cmd.extend(["-p", message])
            
            # Send command to tmux window
            cmd_str = " ".join(cmd)
            tmux_cmd = ["tmux", "send-keys", "-t", window_target, cmd_str]
            subprocess.run(tmux_cmd, check=True)
            
            # Send Enter
            time.sleep(0.5)
            enter_cmd = ["tmux", "send-keys", "-t", window_target, "Enter"]
            subprocess.run(enter_cmd, check=True)
            
            print(f"Gemini command sent to {window_target}: {cmd_str}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error sending message to Gemini: {e}")
            return False
    
    def send_message(self, session_name: str, window_index: int, message: str, provider: Optional[AIProvider] = None) -> bool:
        """Send message using the appropriate AI provider"""
        if provider is None:
            provider = self.get_provider_for_session(session_name, window_index)
        
        if provider == AIProvider.CLAUDE:
            return self.send_message_claude(session_name, window_index, message)
        elif provider == AIProvider.ROVODEV:
            return self.send_message_rovodev(session_name, window_index, message)
        elif provider == AIProvider.GEMINI:
            return self.send_message_gemini(session_name, window_index, message)
        else:
            print(f"Unknown provider: {provider}")
            return False
    
    def configure_session(self, session_name: str, window_index: int, provider: AIProvider, options: Dict = None):
        """Configure a specific session to use a particular AI provider"""
        session_key = f"{session_name}:{window_index}"
        
        if 'sessions' not in self.config:
            self.config['sessions'] = {}
        
        self.config['sessions'][session_key] = {
            'provider': provider.value,
            'options': options or {}
        }
        
        self._save_config(self.config)
        print(f"Configured {session_key} to use {provider.value}")
    
    def list_sessions(self) -> Dict:
        """List all configured sessions and their providers"""
        return self.config.get('sessions', {})
    
    def start_interactive_session(self, session_name: str, window_index: int, provider: AIProvider):
        """Start an interactive AI session in a tmux window"""
        window_target = f"{session_name}:{window_index}"
        
        try:
            if provider == AIProvider.CLAUDE:
                # Start Claude interactive session
                cmd = ["tmux", "send-keys", "-t", window_target, "claude", "Enter"]
                subprocess.run(cmd, check=True)
                
            elif provider == AIProvider.ROVODEV:
                # Start RovoDev interactive session
                cmd = ["tmux", "send-keys", "-t", window_target, "acli rovodev run", "Enter"]
                subprocess.run(cmd, check=True)
                
            elif provider == AIProvider.GEMINI:
                # Start Gemini interactive session
                cmd = ["tmux", "send-keys", "-t", window_target, "gemini", "Enter"]
                subprocess.run(cmd, check=True)
            
            print(f"Started {provider.value} session in {window_target}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error starting {provider.value} session: {e}")
            return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python3 ai_provider.py <session:window> <message> [provider]")
        print("Example: python3 ai_provider.py project:0 'Hello AI!' rovodev")
        sys.exit(1)
    
    # Parse arguments
    session_window = sys.argv[1]
    message = sys.argv[2]
    provider = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        session_name, window_index = session_window.split(':')
        window_index = int(window_index)
    except ValueError:
        print("Error: session:window format required (e.g., 'project:0')")
        sys.exit(1)
    
    # Initialize orchestrator
    orchestrator = AIOrchestrator()
    
    # Convert provider string to enum if provided
    provider_enum = None
    if provider:
        try:
            provider_enum = AIProvider(provider.lower())
        except ValueError:
            print(f"Error: Unknown provider '{provider}'. Available: claude, rovodev, gemini")
            sys.exit(1)
    
    # Send message
    success = orchestrator.send_message(session_name, window_index, message, provider_enum)
    sys.exit(0 if success else 1)