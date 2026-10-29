struct Empty {}; template<class T> struct Special { T value; }; template<> struct Special<Empty> { long long cookie; }; using A=Special<int>; using B=Special<Empty>;
