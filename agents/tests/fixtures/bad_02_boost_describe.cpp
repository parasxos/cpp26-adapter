// Pre-C++26: Boost.Describe macro for struct introspection.
// Expected Pass-1 finding: paper P2996.
#include <boost/describe.hpp>

struct Point {
    int x;
    int y;
};
BOOST_DESCRIBE_STRUCT(Point, (), (x, y));

struct Edge {
    int a;
    int b;
};
BOOST_DESCRIBE_STRUCT(Edge, (), (a, b));
