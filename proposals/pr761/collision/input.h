struct Shared { int shared; };
struct Left : virtual Shared { int value; };
struct Right : virtual Shared { int value; };
struct Join : Left, Right {};
