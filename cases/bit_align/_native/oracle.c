#include "../input.h"
unsigned long long audit_fact(int i) {
 const unsigned long long v[] = {sizeof(struct Flags16), __alignof__(struct Flags16), sizeof(struct Container), __builtin_offsetof(struct Container,flags), __builtin_offsetof(struct Container,suffix)}; return v[i];
}
