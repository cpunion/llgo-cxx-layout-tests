#include "../input.h"
unsigned long long audit_fact(int i) {
 const unsigned long long v[] = {sizeof(struct Packet), __builtin_offsetof(struct Packet,payload)}; return v[i];
}
