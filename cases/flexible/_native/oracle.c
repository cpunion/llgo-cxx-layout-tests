#include "../input.h"
unsigned long long audit_fact(int i) {
 const unsigned long long v[] = {sizeof(struct Flexible), __builtin_offsetof(struct Flexible,data)}; return v[i];
}
