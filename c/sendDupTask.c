#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <math.h>
#include <linux/sockios.h>

#include <sched.h>
#include <pthread.h>

#define REQUEST_BUFFER_SIZE (40)
#define RECV_BUFFER_SIZE (103)


static unsigned long __inline__ rdtscp(void)
{
  unsigned int tickl, tickh;
  __asm__ __volatile__("rdtscp":"=a"(tickl),"=d"(tickh)::"%ecx");
  return ((uint64_t)tickh << 32)|tickl;
}


static void __inline__ bind_processor(int cpu)
{
  cpu_set_t cpuset;
  CPU_ZERO(&cpuset);
  CPU_SET(cpu, &cpuset);
  pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset);
}

double ranExpo(double lambda)
{
    double u;
    u = rand() / (RAND_MAX + 1.0);
    return -log(1 - u) / lambda;
}


char * helpMessage = "sendTask qps iteration taskFile hostname portnumber";

struct task
{
    int id;
    char term[REQUEST_BUFFER_SIZE];
    char response[RECV_BUFFER_SIZE + 1];
    uint64_t sendTimestamp;
    uint64_t receiveTimestamp;
};

struct command
{
    int iteration;
    int qps;
    int nrTask;
    struct task *tasks;
    int sockfd;
    char *ipaddress;
    int portno;
};

volatile int startflag = 0;

pthread_t senderThread;

#define RDTSCP_GRAN (2100 * 1000 * 1000)
#define RDTSCP_GRAN_US (2100 * 1000)
void *sender(void *arg)
{
    bind_processor(0);
    struct command * exp = (struct command *) arg;
    // wait for the flag
    double avgQPS = (double)(exp->qps);
    while (startflag == 0)
	;
    // start issuing the request;
    unsigned long startTimestamp = rdtscp();
    for (int i=0; i<exp->nrTask; i++)
    {
	double intervalTime = ranExpo(avgQPS);
	unsigned long now = rdtscp();
	if (now < startTimestamp)
	{
	    now = startTimestamp;
	}

	unsigned long intervalStamp = intervalTime * RDTSCP_GRAN;
	unsigned long usecond;
	if (now < startTimestamp + intervalStamp)
	{
	    usecond = ((startTimestamp + intervalStamp) - now) / (2100);
	    usleep(usecond);
	}
	/* if (i == 999) */
	/* { */
	/*     unsigned long t = rdtscp(); */
	/*     fprintf(stderr, "%lu, %lu, %lu, %f, %lu\n", startTimestamp, now, t, intervalTime, usecond); */
	/* } */
	startTimestamp = now;
	struct task * t = exp->tasks + i;
	t->sendTimestamp = rdtscp();
	unsigned long write_start = t->sendTimestamp;	
	int nr_write = write(exp->sockfd, t->term, REQUEST_BUFFER_SIZE);
	unsigned long write_end = rdtscp();	
//	printf("%lu: Write %s, %d, %lu, %lu, %lu, %lu\n", t->sendTimestamp, t->term, nr_write, startTimestamp, (write_end - write_start)/2100, usecond, intervalStamp );
//	usleep(1000);
    }
    while(1);
}

pthread_t receiverThread;
void *receiver(void *arg)
{
    bind_processor(1);
    startflag = 1;
    struct command * exp = (struct command *) arg;
    int nrIteration = exp->iteration;
    struct task* tasks = exp->tasks;
    char buf[RECV_BUFFER_SIZE + 1];
    memset(buf, 0, RECV_BUFFER_SIZE);
    unsigned int *receiveOrder = calloc(exp->nrTask, sizeof(unsigned int));
    int nr_receive = 0;
    char dummyResponse[REQUEST_BUFFER_SIZE] = "#dummy";
    printf("#taskid:hit:receiveStamp:queuetime(ns):executeTime(ns):cycles:instructions:clientLatnecy: clientSendStamp:clientReceiveStamp\n");
    while(1)
    {
//	ioctl(exp->sockfd, FIONREAD, &nr_receive);	
	int nr_read = read(exp->sockfd, buf, RECV_BUFFER_SIZE);
//	write(exp->sockfd, dummyResponse, REQUEST_BUFFER_SIZE);
	buf[RECV_BUFFER_SIZE] = 0;
	unsigned long receiveStamp = rdtscp();
	int taskId = strtol(buf, NULL, 10);
	if (taskId >= 0 && taskId < exp->nrTask)
	{
	    struct task *t = &(tasks[taskId]);
	    t->receiveTimestamp = receiveStamp;
	    memcpy(t->response, buf, RECV_BUFFER_SIZE + 1);
	    receiveOrder[nr_receive] = taskId;
	    nr_receive += 1;
//	    printf("%lu: %s, %lu, %lu\n", receiveStamp, buf, t->receiveTimestamp - t->sendTimestamp, nr_receive);
	}
	if (nr_receive == (exp->nrTask))
	{
	    for (int i=0; i<exp->nrTask; i++)
	    {
		unsigned int taskId = receiveOrder[i];
		struct task *t = &(tasks[taskId]);
		printf("%s: %.3f : %lu: %lu\n",t->response, (t->receiveTimestamp - t->sendTimestamp)/(2100.0), t->sendTimestamp, t->receiveTimestamp);
	    }
	    exit(0);
	}

    }
}


#define handle_error(msg) \
    do { perror(msg); exit(EXIT_FAILURE); } while (0)


int runExperiment(struct command *exp)
{
    fprintf(stderr, "Play %lu, %d tasks\n", sizeof(exp->tasks), exp->nrTask);
    // create the socket
    int sockfd;
    struct sockaddr_in serv_addr;

    // get address
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(exp->portno);
    int getAddr = inet_aton(exp->ipaddress, &(serv_addr.sin_addr));
    if (getAddr == 0)
    {
	fprintf(stderr, "Can't get address of IP %s\n", exp->ipaddress);
	return -1;
    }
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd == -1)
    {
	handle_error("Can't create socket.");
    }
    exp->sockfd = sockfd;
    if (connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0)
    {
	fprintf(stderr, "Can't connect to the server.\n");
	return -1;
    }
    int one = 1;
    setsockopt(sockfd, SOL_TCP, TCP_NODELAY, &one, sizeof(one));
    fprintf(stderr, "Connect to %s at fd %d\n", exp->ipaddress, exp->sockfd);
    // create two threads and pin them to two different CPUs
    int senderId = pthread_create(&senderThread, NULL, &sender, (void *)exp);
    int receiverId = pthread_create(&receiverThread, NULL, &receiver, (void *)exp);
    fprintf(stderr, "Sender:%d, receiver:%d\n", senderId, receiverId);
    pthread_exit(NULL);
}


struct command *loadCommand(int argc, char **argv)
{
    struct command * comm = calloc(1, sizeof(struct command));
    comm->qps = strtol(argv[1], NULL, 10);
    comm->iteration = strtol(argv[2], NULL, 10);
    comm->portno = strtol(argv[5], NULL, 10);
    comm->ipaddress = argv[4];
   
    char * taskFileName = argv[3];
    fprintf(stderr, "Play tasks in file %s at QPS %d with %d iterations\n", taskFileName, comm->qps, comm->iteration);
    FILE *taskF = fopen(taskFileName, "r");
    if (taskF == NULL) {
	fprintf(stderr, "Can't open file %s\n", taskFileName);
	exit(1);
    }
//    char buf[100];
//    fprintf(stderr, "Read %d bytes %s\n", read(fileno(taskF), buf, 100), buf);
    char **lines = calloc(10000, sizeof(char *));
    int nr_lines = 0;
    if (lines == NULL)
    {
	fprintf(stderr, "Can't allocate memory for all lines.");
	return NULL;
    }


    for (int i=0; i<10000; i++)
    {
	char * l = NULL;
	size_t len = 0;
	int s = getline(&l, &len, taskF);
	if (s == -1 || l[0] == '#')
	{
	    break;
	}
	lines[i] = l;
	nr_lines += 1;
    }
    fprintf(stderr, "Read %d lines from the task file\n", nr_lines);

    struct task * tasks = calloc(nr_lines, sizeof(struct task));
    for (int i=0; i<nr_lines; i++)
    {
	struct task * t = tasks + i;
	t->id = i;
	char * l = lines[i];
	if (l[0] == '#')
	{
	    fprintf(stderr, "Ignore %s\n", l);
	}
	/* fprintf(stderr, "Processing %s\n", l); */
	/* char *type = strtok(l, ":"); */
	/* char *term = strtok(NULL, ":"); */
	/* if (type == NULL || term == NULL) */
	/* { */
	/*     fprintf(stderr, "Can't parse task %s\n", l); */
	/*     return NULL; */
	/* } */
	/* // strip the space */
	/* while (*term == ' ') */
	/* { */
	/*     term += 1; */
	/* } */
	memset(t->term, 0, REQUEST_BUFFER_SIZE);
	sprintf(t->term, "%s;%d", l, i);
	for (int j=0; j<REQUEST_BUFFER_SIZE; j++)
	{
	    if (t->term[j] == '\0' || t->term[j] == '\n')
		t->term[j] = ' ';
	}
	
	/* char *cursor = l; */
	/* while(*cursor) */
	/* { */
	/*     if (*cursor == '\n') */
	/*     { */
	/* 	*cursor = ' '; */
	/*     } */
	/*     cursor += 1; */
	/* } */

        //	strncpy(t->term, term, 70);
    }
    comm->tasks = tasks;
    comm->nrTask = nr_lines;
    return comm;
}


int main(int argc, char **argv)
{
    if (argc != 6)
    {
	fprintf(stderr, "%s\n", helpMessage);
	exit(0);
    }
    struct command * exp = loadCommand(argc, argv);
    runExperiment(exp);
    exit(0);
}
