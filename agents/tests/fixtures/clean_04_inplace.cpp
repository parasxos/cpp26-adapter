// C++26 std::inplace_vector<T, N> (P0843). Replaces the third-party
// fixed-capacity vector containers with a standard form.
#include <inplace_vector>

void batch(int /*fd*/) {
    std::inplace_vector<int, 64> buffer;
    for (int i = 0; i < 50; ++i) {
        buffer.push_back(i);
    }
    auto* maybe = buffer.try_push_back(50);
    (void)maybe;
}
