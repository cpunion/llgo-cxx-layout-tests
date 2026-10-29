struct __attribute__((aligned(8))) Floats { float x, y; };
union FloatUnion { struct Floats a, b; };
