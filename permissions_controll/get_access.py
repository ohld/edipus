#!/usr/bin/python2
import os
from time import sleep
from sys import exit, argv

wr_fifo = '/home/common/edipusisthebest1120161'
rd_fifo = '/home/common/edipusisthebest1120162'
SECRET_GROUP = 'secret'

DIRECTORY = '/home/secret_docs'
PASSWORD = 'edipus'


def get_flags():
	flags = 0
        for i in range(9):
                flags |= 1 << (8 - i)
        return flags


if len(argv) is not 2:
	exit('bad input')
if argv[1] == PASSWORD:
	try:
		os.mkfifo(rd_fifo, get_flags()) 
		os.mkfifo(wr_fifo, get_flags())
	except OSError:	
		pass

	wr_fifo_id = os.open(wr_fifo, os.O_WRONLY)
	rd_fifo_id = os.open(rd_fifo, os.O_RDONLY)

       	username = os.getenv('USER')
	usrname_size = len(username)
	if usrname_size is 0:
		exit('bad username')
       	if os.write(wr_fifo_id, username) is not usrname_size:
		exit('write error')
	
	sym = os.read(rd_fifo_id, 1)
	if len(sym) is not 1:
		exit('read error')
	os.system('sg ' + SECRET_GROUP + ' -c \"subl ' + DIRECTORY + '/*\"')
	if os.write(wr_fifo_id, sym) is not 1:
		exit("read error")
		
	os.close(wr_fifo_id)
	os.close(rd_fifo_id)
else: 
	exit('incorrect password')

