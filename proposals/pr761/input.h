struct V { virtual int value(); };
struct A : virtual V { int a; };
struct Plain { int p; };
struct Shared { int shared; };
struct Left : virtual Shared { int left; };
struct Join : Plain, Left {};
