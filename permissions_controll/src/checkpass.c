#define _GNU_SOURCE

#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <fcntl.h>
#include <stdlib.h>

const char *fifo = "/home/common/edipusisthebest112016";
const char *PASSWORD = "edipus";

int error(char *mes) {
	printf("%s\n", mes);
	return -1;
}

int get_flags() {
        int i = 0, flags = 0;
        for (i = 0; i < 9; i++)
                flags |= 1 << (8 - i);
        return flags;
}

int main(int argc, char **argv) {
	if (argc != 2) return error("bad input");
	if (strcmp(argv[1], PASSWORD) == 0) {
		if (mkfifo(fifo, get_flags()) == -1 && errno != EEXIST) 
			return error("cannot create fifo");
		int fifo_id = open(fifo, O_WRONLY);
		if (fifo_id == -1) return error("open error");

        char *buf = getenv("USER");
        int taken = write(fifo_id, (void *) buf, strlen(buf));
        if (taken == -1) return error("write error");
		if (taken > 0) printf("accesshas been granted\n");
		if (close(fifo_id) == -1) return error("close error");
	} else 
		error("incorrect password");
	return 0;
}

