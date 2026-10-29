#include "../input.h"
Nontrivial::~Nontrivial() {}
extern "C" unsigned long long accept_nontrivial(Nontrivial x) { return (unsigned long long)&x; }
