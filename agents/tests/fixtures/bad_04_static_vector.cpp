// Pre-C++26: boost::container::static_vector instead of std::inplace_vector.
// Expected Pass-1 finding: paper P0843.
#include <boost/container/static_vector.hpp>

void batch_packets() {
    boost::container::static_vector<int, 64> buffer;
    for (int i = 0; i < 50; ++i) {
        buffer.push_back(i);
    }
}
