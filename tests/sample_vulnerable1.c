
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char name[16];
    printf("Enter name: ");
    gets(name);
    char greeting[32];
    sprintf(greeting, "Hello %s", name);

    char *p = (char*)malloc(8);
    strcpy(p, name);
    free(p);
    printf("Still here: %c\n", p[0]);
    printf(name);

    char buf[8];
    scanf("%s", buf);
    system(name);

    return 0;
}
