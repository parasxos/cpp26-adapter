// C++26 std::execution sender pipeline (P2300). No std::async.
#include <execution>

namespace ex = std::execution;

int run_pipeline(int seed) {
    auto pipeline =
          ex::just(seed)
        | ex::then([](int x) { return x * 2; })
        | ex::then([](int x) { return x + 1; });
    auto [result] = ex::sync_wait(pipeline).value();
    return result;
}
