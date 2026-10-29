struct alignas(16) Aligned { int x; }; struct AlignedBox { char prefix; Aligned value; char suffix; };
