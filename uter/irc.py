"""
Core IRC functionality
"""
import asyncio
import logging

from datetime import datetime
from enum import Enum
from configparser import ConfigParser

from uter.commands import *
from uter.messages import *
from uter.handlers.default import *
from uter.handlers.ameno import *

LOGGER = logging.getLogger(__name__)

CRLF = "\r\n"

CONFIG = ConfigParser()
CONFIG.read('uter/default.cfg')

class BaseHandler:
	def __init__(self, check=None, execute=None):
		self.methods = {
			'check'  : check or (lambda _: True),
			'execute': execute or (lambda _: None)
		}

	def accept(self, message):
		if self.methods['check'](message):
			return self.methods['execute'](message)
		else:
			return None

class IRCProtocol(asyncio.Protocol):
	def quote(self, message):
		print(">> {0}".format(message.strip()))
		self.transport.write(message.encode())

	def add(self, command):
		self.quote(command.quote())

	def add_all(self, commands):
		if commands is None:
			return
		elif isinstance(commands, Command):
			self.add(commands)
		else:
			for command in commands:
				self.add(command)

	def __init__(self, loop):
		self.loop = loop
		self.handlers = [
			BaseHandler(lambda m: PingMessage in m.types, lambda m: PongCommand()),
			BaseHandler(lambda m: WelcomeMessage in m.types, lambda m: JoinCommand(CONFIG["Basic"]["AutoJoinChannels"].split())),
			JoinPartHandler()
		]

	def connection_made(self, transport):
		print('Connection established')
		self.transport = transport

		name = CONFIG["Basic"]["BotName"]

		self.add(UserCommand(name))
		self.add(NickCommand(name))

	def data_received(self, data):
		for line in data.decode().split(CRLF):
				if (line.strip() != ""):
					msg = parse_message(line)
					if (msg is not None):
						self.handle(msg)

	def handle(self, message):
		print(message.raw)
		for handler in self.handlers:
			self.add_all(handler.accept(message))

	def connection_lost(self, exc):
		print('The server closed the connection')
		print('Stop the event loop')
		self.loop.stop()

class IRCConnection():
	def __init__(self):
		self.loop = asyncio.get_event_loop()

	def start(self):
		self.coro = self.loop.create_connection(lambda: IRCProtocol(self.loop), CONFIG["Basic"]["HostName"], CONFIG["Basic"]["Port"])
		self.loop.run_until_complete(self.coro)
		self.loop.run_forever()
		self.loop.close()
