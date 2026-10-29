#include "../input.h"
int V::value() {return 7;}
extern "C" unsigned long long virtual_fact(int i) {
 A a; Join j;
 const unsigned long long v[]={sizeof(A),sizeof(Join),
 (unsigned long long)((char*)(V*)&a-(char*)&a),
 (unsigned long long)((char*)(Plain*)&j-(char*)&j),
 (unsigned long long)((char*)&j.left-(char*)&j),
 (unsigned long long)((char*)(Shared*)&j-(char*)&j)};
 return v[i];
}
