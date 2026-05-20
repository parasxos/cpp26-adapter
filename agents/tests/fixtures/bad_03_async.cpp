// Pre-C++26: std::async for async pipelines.
// Expected Pass-1 finding: paper P2300.
#include <future>

int run_pipeline(int seed) {
    auto fa = std::async(std::launch::async, [seed] { return seed * 2; });
    auto fb = std::async(std::launch::async, [seed] { return seed + 1; });
    return fa.get() + fb.get();
}
