#include "../input.h"
static ReturnDerived result;
ReturnBase* FactoryBase::make() { return &result; }
int FactoryBase::base_after() { return 11; }
ReturnDerived* FactoryDerived::make() { return &result; }
int FactoryDerived::derived_after() { return 22; }
extern "C" FactoryDerived* get_factory() { static FactoryDerived f; return &f; }
extern "C" ReturnDerived* get_result() { return &result; }
