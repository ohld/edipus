import os
fifo = "/home/common/edipusisthebest112016"

def get_flags():
    i = 0
    flags = 0
    while i < 9:
        flags |= 1 << (8 - i)
        i+=1
    return flags


def permission_control(check):
    if check is True:
        os.mkfifo(fifo, get_flags())
        fifo_id = os.open(fifo, os.O_WRONLY)
        if (fifo_id is not -1):
            buf = os.getenv("USER")
            taken = os.write(fifo_id, buf)
            os.close(fifo_id)