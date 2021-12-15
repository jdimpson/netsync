#!/usr/bin/env python3

from time import sleep
import socket
import netsync
import netsync.rtp

cast = "broad"
print("{}cast".format(cast))
if   cast == "uni":
	group = "10.0.0.150"
elif cast == "broad":
	group = "255.255.255.255"
elif cast == "multi":
	group="224.69.69.1"
	ttl  = 1
port = 6969

sock = netsync.rtp.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 2)
if   cast == "multi":
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
elif cast == "broad":
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

#sock.connect((group,port))
for t in range(10):
	o=str(t).encode()
	print("sending {}".format(t))
	sock.sendto(o,(group,port))
	sleep(0.1)

# send(bytes, flags)
# sendall(bytes, flags)
# sendto(bytes, address)
# sendto(bytes, flags, address)
# sendmsg(buffers, ancdata, flags, address)
