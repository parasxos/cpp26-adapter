// Pre-C++26: assert() instead of contract_assert / pre / post.
// Expected Pass-1 finding: paper P2900.
#include <cassert>

int divide(int a, int b) {
    assert(b != 0);              // ← anti-pattern: should be contract or pre
    assert(a >= 0);              // ← anti-pattern: should be contract_assert
    int r = a / b;
    assert(r * b == a);          // ← post-condition, expressed as in-body assert
    return r;
}
