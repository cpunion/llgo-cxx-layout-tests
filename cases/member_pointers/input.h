struct Object { int value; virtual int f(); }; struct Holder { int Object::*data; int (Object::*function)(); };
