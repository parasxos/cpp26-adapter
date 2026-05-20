// C++26 contracts (P2900): pre / post / contract_assert. Replaces the old
// `assert` macro with three semantically distinct checking constructs.
#include <contracts>

int divide(int a, int b)
  pre (b != 0)
  post (r : r * b == a)
{
    contract_assert(a >= 0);
    return a / b;
}

int safe_size(int n)
  pre (n >= 0)
{
    return n + 1;
}
