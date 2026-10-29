struct Packet {
    unsigned a : 1;
    unsigned b : 3;
    union { int x; float f; } payload;
};
