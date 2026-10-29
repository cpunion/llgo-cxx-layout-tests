#include "../input.h"
int V::value() {return 7;}
extern "C" unsigned long long virtual_fact(int i) {
 A a; Join j;
 const unsigned long long v[]={sizeof(A),sizeof(Join),
 (unsigned long long)((__UINTPTR_TYPE__)(V*)&a-(__UINTPTR_TYPE__)&a),
 (unsigned long long)((__UINTPTR_TYPE__)(Plain*)&j-(__UINTPTR_TYPE__)&j),
 (unsigned long long)((__UINTPTR_TYPE__)&j.left-(__UINTPTR_TYPE__)&j),
 (unsigned long long)((__UINTPTR_TYPE__)(Shared*)&j-(__UINTPTR_TYPE__)&j)};
 return v[i];
}
