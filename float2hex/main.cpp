#include <stdio.h>
#include <unistd.h>
#include <string>

int main(int argc, char* argv[]) {
  if (argc != 2) {
    printf("%s <float-value>\n", argv[0]);
    exit(1);
  }

  float fv = std::stof(argv[1]);
  printf("0x%08x\n", *(int*)(&fv));
}

