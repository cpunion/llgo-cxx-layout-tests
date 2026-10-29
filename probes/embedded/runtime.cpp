#include "../layout.cpp"
#if defined(__wasm__)
struct Iovec { const char* data; unsigned size; };
extern "C" __attribute__((import_module("wasi_snapshot_preview1"),import_name("fd_write"))) int fd_write(int,const Iovec*,int,unsigned*);
extern "C" __attribute__((import_module("wasi_snapshot_preview1"),import_name("proc_exit"),noreturn)) void proc_exit(int);
void write(const char *s) { unsigned n=0,done; while(s[n])++n; Iovec v={s,n};fd_write(1,&v,1,&done); }
void finish(unsigned code) { proc_exit(code); }
#else
static unsigned hostcall(unsigned op, const void *arg) {
#if defined(__arm__)
 register unsigned r0 asm("r0")=op;
 register const void *r1 asm("r1")=arg;
 asm volatile("bkpt 0xab" : "+r"(r0) : "r"(r1) : "memory");return r0;
#else
 register unsigned a0 asm("a0")=op;
 register const void *a1 asm("a1")=arg;
 asm volatile(".balign 16\n.option push\n.option norvc\nslli zero,zero,0x1f\nebreak\nsrai zero,zero,7\n.option pop" : "+r"(a0) : "r"(a1) : "memory");return a0;
#endif
}
void write(const char *s) {hostcall(4,s);}
void finish(unsigned code) { unsigned arg[]={0x20026,code};hostcall(0x20,arg); for(;;){} }
#endif
void number(unsigned x) { char s[12]; unsigned n=11; s[n]=0;do{s[--n]='0'+x%10;x/=10;}while(x);write(s+n); }
template<class T,class U> unsigned delta(T*p,U*q) {return (__UINTPTR_TYPE__)p-(__UINTPTR_TYPE__)q;}
__attribute__((noinline)) int dispatch(V *v) { return v->value(); }
extern "C" void audit_start() {
 write("{\"facts\":[");
 for(unsigned i=0;i<sizeof(audit_facts)/sizeof(*audit_facts);++i){if(i)write(",");number((unsigned)audit_facts[i]);}
 L l; D d; E e; VirtualPrimary v; PrimaryOrder p; PlainD n; TwoSame t;
 write("],\"dynamic\":{\"L.A\":");number(delta((A*)&l,&l));
 write(",\"D.L.A\":");number(delta((A*)(L*)&d,(L*)&d));
 write(",\"E.L.A\":");number(delta((A*)(L*)&e,(L*)&e));
 write(",\"D.R.A\":");number(delta((A*)(R*)&d,&d));
 write(",\"VirtualPrimary.V\":");number(delta((V*)&v,&v));
 write(",\"PrimaryOrder.Other\":");number(delta((Other*)&p,&p));
 write(",\"PrimaryOrder.L\":");number(delta((L*)&p,&p));
 write("}}\n");
 unsigned failed= ((A*)(L*)&d!=(A*)(R*)&d) || ((A*)(PlainL*)&n==(A*)(PlainR*)&n) || (&t.a==&t.b) || (dispatch(&v)!=7);
 finish(failed);
}
#if defined(__wasm__)
extern "C" void _start() { audit_start(); }
#endif
extern "C" void *memset(void*p,int c,__SIZE_TYPE__ n){volatile char*s=(char*)p;while(n--)*s++=c;return p;}
extern "C" void *memcpy(void*p,const void*q,__SIZE_TYPE__ n){volatile char*d=(char*)p;const volatile char*s=(const char*)q;while(n--)*d++=*s++;return p;}
extern "C" void __aeabi_memclr4(void*p,unsigned n){memset(p,0,n);}
extern "C" void __aeabi_memcpy(void*p,const void*q,unsigned n){memcpy(p,q,n);}
