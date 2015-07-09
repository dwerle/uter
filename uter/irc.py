"""
Core IRC functionality
"""
import asyncio
import logging

from datetime import datetime
from enum import Enum
from configparser import ConfigParser

LOGGER = logging.getLogger(__name__)
CLRF = "\r\n"

MESSAGE_INFO = {
	'unparsed': {},
	'message': {'identifier': 'PRIVMSG'},
	'motd': {'identifier': '372'},
	'end_motd': {'identifier': '376'},
	'welcome': {'identifier': '001'},
	'ping': {}
}

CONFIG = ConfigParser()
CONFIG.read('uter/default.cfg')

MessageType = Enum('MessageType', list(MESSAGE_INFO.keys()))

IDENTIFIER_TO_TYPE = dict((v['identifier'], MessageType[k]) for k, v in MESSAGE_INFO.items() if 'identifier' in v)

print(MessageType)
print(IDENTIFIER_TO_TYPE)

class MessageParser:
	def parse_type(type_string):
		return IDENTIFIER_TO_TYPE.get(type_string, MessageType.unparsed)

	def parse_sender(sender_string):
		return sender_string

	def parse_message(message):
		result = {'time':datetime.now(), 'raw_message':message, 'message_type':MessageType.unparsed}

		splitted = message.split()

		if (splitted[0] == "PING"):
			result.update(message_type=MessageType.ping, time=datetime.now(), sender=splitted[1])
		elif (message[0] == ":"):
			result.update(message_type=MessageParser.parse_type(splitted[1]), sender=MessageParser.parse_sender(splitted[0][1:]))

		return result

class IRCProtocol(asyncio.Protocol):
	def _user(self, username, mode=[], realname=''):
		self.quote("USER {0} 0 * :{1}".format(username, realname))

	def _nick(self, nick):
		self.quote("NICK {0}".format(nick))

	def _join(self, channel):
		self.quote("JOIN {0}".format(channel))

	def _pong(self):
		self.quote("PONG")

	def quote(self, message):
		print(">> {0}".format(message))
		self.transport.write("{0}{1}".format(message, CLRF).encode())

	def __init__(self, loop):
		self.loop = loop

	def connection_made(self, transport):
		print('Connection established')
		self.transport = transport


		name = CONFIG["Basic"]["BotName"]
		self._user(name, [], name)
		self._nick(name)

	def data_received(self, data):
		for line in data.decode().split(CLRF):
				if (line.strip() != ""):
					self.handle(MessageParser.parse_message(line))

	def handle(self, message):
		print('<< {0}'.format(message))
		if (message['message_type'] is MessageType.welcome):
			for channel in CONFIG["Basic"]["AutoJoinChannels"].split():
				self._join(channel)
		elif (message['message_type'] is MessageType.ping):
			self._pong()
		

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
