#!/usr/bin/env python3

import socket as real_socket
import random
import struct
from time import sleep, time

# from https://stackoverflow.com/questions/45207430/extending-socket-socket-with-a-new-attribute
class socket(real_socket.socket):
	'''Extension of socket.socket that intercepts send*() and recv*() in order to add or remove RTP headers'''
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
		self.send_header = send_header()

	def send(self, *args, **kwargs):
		super(socket, self).send(*args, **kwargs)
		print("RTP-send()")
	def sendall(self, *args, **kwargs):
		super(socket, self).sendall(*args, **kwargs)
		print("RTP-sendall()")
	def sendto(self, *args, **kwargs):
		print("RTP-sendto()")
		if len(args) > 0:
			args = (self.send_header.pack() + args[0], args[1])
		elif len(kwargs):
			raise RuntimeError("WOAH! sendto has kwargs?? Far out. {}".format(str(kwargs)))
		super(socket, self).sendto(*args, **kwargs)
		self.send_header.increment()
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
		self.sequence_number=sequence_number
		self.sequence_number_start=None
		self.timedistorter=timedistorter
		self.timestamp = self.timestamp_start = None
		self.ssrc=ssrc
		self.csrc=csrc
		self.header_extension=header_extension
		if self.header_extension is None:
			self.extension = False
		else:
			self.extension = True


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
	def make_timestamp(self):
		'''
RTP timestamps SHOULD have a random starting point, but I'd like to make them aas easy to use as just calling time(). Also, how the 32 bits is actually interpretted is defined in the media profile. We don't have one of those for RGB lights, so hereby let it be known that the value is in milliseconds. If this implemetnation ever moves beyond a a simple RGB light sync application, the issue of media types will have to be dealt with proper abstractions.
		'''
		# convert seconds to milliseconds, add in the "randomness" and  truncate to 32 bits.
		return (round(time()*1000)+ self.timedistorter)&0xffffffff 
		# consider using clock.CLOCK_MONOTONIC to avoid time going
		# backward due to wall clock corrections

	def pack(self):

		now = self.make_timestamp()
		if self.timestamp_start is None:
			self.timestamp_start = now
		if self.timestamp is None or now > self.timestamp:
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

class send_header(header):

	def __init__(self, *args, **kwargs):
		super(send_header, self).__init__(*args, **kwargs)

		# defaults to None in header() constructor
		if self.sequence_number is None:
			self.sequence_number=random.randrange(0xefff)
		# defaults to None in header() constructor
		if self.sequence_number_start is None:
			sequence_number_start=self.sequence_number
		# defaults to None in header() constructor
		if self.ssrc is None:
			self.ssrc = random.randrange(0xffffffff)
		# defaults to 0 in header() constructor, so if it's None, the uuser wants us to make up a random time distortion
		if self.timedistorter is None:
			self.timedistorter=random.randint(0,0xffffffff)

	def increment(self):
		self.sequence_number += 1
		if self.sequence_number >= 65536:
			self.sequence_number = 0

class recv_header(header):
	def validate(self):
		# when validating a received seq_no, 
		# wraparound needs to be considered
		pass
