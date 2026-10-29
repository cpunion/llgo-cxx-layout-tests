// GNU C extension, deliberately separate from the C++ empty-class rules.
struct EmptyC {};
struct EmptyMemberC { struct EmptyC e; int x; };
const unsigned long long audit_c_facts[] = {
 sizeof(struct EmptyC), _Alignof(struct EmptyC),
 sizeof(struct EmptyMemberC), __builtin_offsetof(struct EmptyMemberC,x)
};
#ifdef AUDIT_NATIVE
#include <stdio.h>
int main(void) { for(unsigned i=0;i<4;++i) printf("%llu%s",audit_c_facts[i],i==3?"\n":" "); return 0; }
#endif
