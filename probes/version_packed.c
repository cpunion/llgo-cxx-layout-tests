// Minimal cross-version ABI counterexample, valid as both C and C++ extension code.
struct PackedABI { char lead; unsigned a:3; unsigned :0; unsigned short b:9; int value; } __attribute__((packed));
#ifdef __cplusplus
extern "C"
#endif
const unsigned long long audit_version_facts[]={sizeof(struct PackedABI),__alignof__(struct PackedABI),__builtin_offsetof(struct PackedABI,value)};
