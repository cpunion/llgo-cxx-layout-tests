struct __attribute__((aligned(16))) Flags16 {
    unsigned a : 3;
    unsigned b : 5;
};
struct Container { char prefix; struct Flags16 flags; char suffix; };
