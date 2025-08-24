
#include <iostream>
#include <cstdio>
#include <cstring>
#include <vector>
using namespace std;

void greet(const char* user) {
    char tmp[10];
    strcpy(tmp, user);
    printf(user);
}

int main() {
    vector<int> v(2);
    int* ptr = new int[2];
    delete [] ptr;
    int x = ptr[0];
    greet("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");
    return 0;
}
