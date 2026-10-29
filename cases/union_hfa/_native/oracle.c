#include "../input.h"
union FloatUnion round_union(union FloatUnion x) { x.a.x+=1; x.a.y+=2; return x; }
unsigned long long audit_fact(int i) { const unsigned long long v[]={sizeof(union FloatUnion), __alignof__(union FloatUnion)}; return v[i]; }
