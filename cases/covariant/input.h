struct ReturnBase { int base; };
struct ReturnOther { int other; };
struct ReturnDerived : ReturnOther, ReturnBase { int derived; };
struct FactoryBase { virtual ReturnBase* make(); virtual int base_after(); };
struct FactoryDerived : FactoryBase { ReturnDerived* make() override; virtual int derived_after(); };
