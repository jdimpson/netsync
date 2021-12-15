#!/usr/bin/env python3

import socket as real_socket
import random
import struct
from time import sleep, time

# from https://stackoverflow.com/questions/45207430/extending-socket-socket-with-a-new-attribute
class socket(real_socket.socket):
	def __init__(self, *args, **kwargs):
		if len(args) > 0:
			if  args[1] != real_socket.SOCK_DGRAM:
				raise RuntimeError("RTP only valid over datagrams")
		elif len(kwargs) > 0 and 'type' in kwargs:
			if  kwargs['type'] != real_socket.SOCK_DGRAM:
				raise RuntimeError("RTP only valid over datagrams")
		else:
			# assume default is SOCK_STREAM
			raise RuntimeError("RTP only valid over datagrams")

		super(socket, self).__init__(*args, **kwargs)
		self.header = header()

	def send(self, *args, **kwargs):
		super(socket, self).send(*args, **kwargs)
		print("RTP-send()")
	def sendall(self, *args, **kwargs):
		super(socket, self).sendall(*args, **kwargs)
		print("RTP-sendall()")
	def sendto(self, *args, **kwargs):
		print("RTP-sendto()")
		if len(args) > 0:
			#args[0] = self.header.pack() + args[0]
			args = (self.header.pack() + args[0], args[1])
		elif len(kwargs):
			raise RuntimeError("WOAH! sendto has kwargs?? Far out. {}".format(str(kwargs)))
		super(socket, self).sendto(*args, **kwargs)
		self.header.increment()
	#def sendmsg(self, *args, **kwargs):
	#	super(socket, self).sendmsg(*args, **kwargs)
	#	print("RTP-sendmsg()")
	#def sendmsg_afalg(self, *args, **kwargs):
	#	super(socket, self).sendmsg_afalg(*args, **kwargs)
	#	print("RTP-sendmsg_afalg()")

	@classmethod
	def copy(cls, sock):
		fd = real_socket.dup(sock.fileno())
		copy = cls(sock.family, sock.type, sock.proto, fileno=fd)
		copy.settimeout(sock.gettimeout())
		print("I copied a socket, RTP-style!")
		return copy

# from https://en.wikipedia.org/wiki/Real-time_Transport_Protocol#Packet_header
class header(object):
	def __init__(self, version=2, padding=False, marker=False, payload_type=96, sequence_number=None, ssrc=None, csrc=[], header_extension=None,timedistorter=0):
		self.version=version
		self.padding=padding
		self.marker=marker
		self.payload_type=payload_type
		if sequence_number is None:
			self.sequence_number=random.randrange(0xefff)
		else:
			self.sequence_number=sequence_number
		self.sequence_number_base=self.sequence_number
		self.timedistorter=timedistorter
		self.timestamp = self.timestamp_base = None
		if ssrc is None:
			#self.ssrc = random.randbytes(4)
			self.ssrc = random.randrange(0xffffffff)
		else:
			self.ssrc=ssrc
		self.csrc=csrc
		self.header_extension=header_extension
		if self.header_extension is None:
			self.extension = False
		else:
			self.extension = True

	def increment(self):
		self.sequence_number += 1
		if self.sequence_number >= 65536:
			self.sequence_number = 0
			# when validating a received seq_no, 
			# wraparound needs to be considered

	def parse(self,buffer):
		pass
	#	Offsets	Octet	0								1								2								3
	#	Octet	Bit [a]	0	1	2	3	4	5	6	7	8	9	10	11	12	13	14	15	16	17	18	19	20	21	22	23	24	25	26	27	28	29	30	31
	#	0	0	Version	P	X	CC	M	PT	Sequence number
	#	4	32	Timestamp
	#	8	64	SSRC identifier
	#	12	96	CSRC identifiers
	#			...
	#	12+4×CC	96+32×CC	Profile-specific extension header ID	Extension header length
	#	16+4×CC	128+32×CC	Extension header
	#				...
	def pack(self):

		now = (round(time()*1000)+ self.timedistorter)&0xffffffff 
		if self.timestamp_base is None:
			self.timestamp_base = now
		self.timestamp = now	

		version = self.version & 0b11
		if self.padding: padding = 0b1 
		else: padding = 0b0
		if self.extension: extension = 0b1 
		else: extension = 0b0
		if self.marker: marker = 0b1 
		else: marker = 0b0
		csrc_cnt = len(self.csrc) & 0b1111
		pt = self.payload_type & 0b1111111
		sixteen = (version<<14)+(padding<<13) + (extension << 12) + (csrc_cnt << 8) + (marker << 7) + ( pt )

		#print(type(sixteen),sixteen)
		buffer = bytearray(4 + 4 +4 + ( 4 * csrc_cnt))
		fmt = '!HH'
		struct.pack_into('!HH',buffer,0, sixteen, self.sequence_number)
		struct.pack_into('!L',buffer, 4, self.timestamp)
		struct.pack_into('!L',buffer, 8, self.ssrc)
		for i in range(csrc_cnt):
			struct.pack_into('!L',buffer, 12 + (4*i), self.csrc[i])
		return buffer
