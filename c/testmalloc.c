#include <stdio.h>
#include <stdlib.h>
int
main(int argc, char **argv)
{
    for (int i=322; i<600; i++)
    {
	char *buf = malloc(i);
	memset(buf, 0, i);
	printf("buf:%x\n", buf);
	free(buf);
    }
}
