// Pre-C++26: magic_enum library for enum_name.
// Expected Pass-1 finding: paper P2996.
#include <magic_enum.hpp>
#include <string_view>

enum class Color { Red, Green, Blue };

std::string_view color_name(Color c) {
    return magic_enum::enum_name(c);
}
