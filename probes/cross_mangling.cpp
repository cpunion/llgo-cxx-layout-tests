#include "cross_mangling.h"
extern "C" int audit_symbol(int value) { return value + 1; }
