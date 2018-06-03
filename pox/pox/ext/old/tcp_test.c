#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define SERVER_IP "10.0.20.2"
#define SERVER_PORT 9999

int main(int argc, char *argv[]) {
  if(argc != 2) {
    printf("Error: expected either `-s` or `-c` as a parameter, got nothing.\n");
    return -1;
  }

  if(strcmp(argv[1], "-s") == 0) { // Server, h0 = 10.0.0.1:9999
    int server_sock = socket(AF_INET, SOCK_STREAM, 0);

    int opt = 1;
    setsockopt(server_sock, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt));

    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(SERVER_PORT);

    bind(server_sock, (struct sockaddr *)&address, sizeof(address));
    listen(server_sock, 1);

    int addrlen = sizeof(address);
    int in_sock = accept(server_sock, (struct sockaddr *)&address, (socklen_t *)&addrlen);
    // wait for boop
    char data[4096000] = {0};
    read(in_sock, data, 4096000);

    FILE *fp;
    fp = fopen("/dev/urandom", "r");
    
    while (1) {
      fread(&data, 1, 4096000, fp);
      send(in_sock, data, 4096000, 0);
    }

  } else if (strcmp(argv[1], "-c") == 0) { // Client, h11 = 10.0.20.2:12345
    int sock = socket(AF_INET, SOCK_STREAM, 0);

    struct sockaddr_in server_address;
    memset(&server_address, '0', sizeof(server_address));
    server_address.sin_family = AF_INET;
    server_address.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_address.sin_addr);

    connect(sock, (struct sockaddr *)&server_address, sizeof(server_address));
    char *boop = "boop";
    send(sock, boop, strlen(boop), 0);


    char buf[4096000] = {0};
    while (1) {
      printf("Client received %d bytes.\n", read(sock, buf, 4096000));
      memset(buf, 0, 4096000);
    }

  } else {
    printf("Error: expected either `-s` or `-c` as a parameter, got `%s`.\n", argv[1]);
    return -1;
  }

  return 0;
}

