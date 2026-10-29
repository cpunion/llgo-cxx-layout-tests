struct Nontrivial { int value; ~Nontrivial(); }; extern "C" unsigned long long accept_nontrivial(Nontrivial x);
