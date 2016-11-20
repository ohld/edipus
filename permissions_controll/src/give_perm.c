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
const int MES_SIZE = 100;

int error(char *mes) {
	printf("%s\n", mes);
	return -1;
}

int main() {
	for (;;) {
		int fifo1_id = open(fifo1, O_RDONLY);
		if (fifo1_id == -1) {
			sleep(1);
			continue;
		}
		int fifo2_id = open(fifo2, O_WRONLY);
		if (fifo2_id == -1) return error("open error");
        	
		if (unlink(fifo1) == -1) return error("unlink error");
		if (unlink(fifo2) == -1) return error("unlink error");
        
        	char *buf = (char *) calloc(MES_SIZE, sizeof(char));
		char command[1000] = {};
		int taken = read(fifo1_id, (void *) buf, MES_SIZE);
		if (taken  > 0) {
			snprintf(command, 1000, "usermod -a -G secret %s", buf);
			system(command);
		} else return error("read error");
		if (write(fifo2_id, (void *) buf, 1) != 1)
			return error("write error");
		if (read(fifo1_id, (void *) buf, 1) == 1) {
			system("/home/edipus/permissions_controll/reset_secret_group.bash");
		} else return error("read error");
	
        	if (close(fifo1_id) == -1) return error("close error");
        	if (close(fifo2_id) == -1) return error("close error");
		free(buf);
	}
	return 0;
}

