#define _GNU_SOURCE

#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <fcntl.h>
#include <stdlib.h>

const char *fifo1 = "/home/common/edipusisthebest1120161";
const char *fifo2 = "/home/common/edibusisthebest1120162";
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
		if (mkfifo(fifo1, get_flags()) == -1 && errno != EEXIST) 
			return error("cannot create fifo");
		if (mkfifo(fifo2, get_flags()) == -1 && errno != EEXIST) 
			return error("cannot create fifo");
		
		int fifo1_id = open(fifo1, O_WRONLY);
		if (fifo1_id == -1) return error("open error");
		int fifo2_id = open(fifo2, O_RDONLY);
		if (fifo2_id == -1) return error("open error");

        	char *buf = getenv("USER");
		if (strlen(buf) == 0) return error("bas username");
        	if (write(fifo1_id, (void *) buf, strlen(buf)) != strlen(buf))
			return error("write error");
		char sym = 0;
		if (read(fifo2_id, (void *) &sym, 1) != 1)
			return error("read error");
		system("sg secret -c \"subl /home/secret_docs/*\"");
		if (write(fifo1_id, (void *) &sym, 1) != 1)
			return error("read error");
		
		if (close(fifo1_id) == -1) return error("close error");
		if (close(fifo2_id) == -1) return error("close error");
	} else 
		error("incorrect password");
	return 0;
}

