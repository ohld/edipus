#!/usr/bin/python2
from access_data import wr_fifo, rd_fifo, SECRET_GROUP
import os
from time import sleep
from sys import exit

MES_SIZE = 100

while True:
	try:
		rd_fifo_id = os.open(wr_fifo, os.O_RDONLY)
	except OSError:
		sleep(1) 
		continue

	wr_fifo_id = os.open(rd_fifo, os.O_WRONLY)
	os.unlink(rd_fifo)
	os.unlink(wr_fifo)
        
	username = os.read(rd_fifo_id, MES_SIZE)
	if len(username)  > 0:
		os.system('gpasswd --add ' + username + ' ' + SECRET_GROUP + ' > /dev/null')
	else:
		exit('read error')
	sym = '0'
	os.write(wr_fifo_id, sym)
	sym = os.read(rd_fifo_id, 1)
	if len(sym) is 1:
		os.system('gpasswd --delete ' + username + ' ' + SECRET_GROUP + ' > /dev/null')
	else:
		exit('read error')
	
       	os.close(rd_fifo_id)
       	os.close(wr_fifo_id)

