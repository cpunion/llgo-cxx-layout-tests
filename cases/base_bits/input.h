struct Base { int value; };
struct Derived : Base { unsigned a : 1; unsigned b : 3; int tail; };
