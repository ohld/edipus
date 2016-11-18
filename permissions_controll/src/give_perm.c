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
const int MES_SIZE = 100;

int error(char *mes) {
	printf("%s\n", mes);
	return -1;
}

int main() {
 	int fifo_id = 0;
	for (;;) {
		fifo_id = open(fifo, O_RDONLY);
		if (fifo_id == -1) {
			sleep(1);
			continue;
		}
        	
		if (unlink(fifo) == -1) return error("unlink error");
        
        	char *buf = (char *) calloc(MES_SIZE, sizeof(char));
		char command[1000] = {};
        	int taken = 0;
		memset((void *) buf, 0, MES_SIZE);
		taken  = read(fifo_id, (void *) buf, MES_SIZE);
		printf("%d\n", taken);
		if (taken > 0) {
			snprintf(command, 1000, "usermod -a -G secret %s", buf);
			system(command);
		}
	
        	if (close(fifo_id) == -1) return error("close error");
		free(buf);
	}
	return 0;
}

