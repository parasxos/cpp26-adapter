// C++26 reflection-based enum_name. Uses P2996 (reflection) + P1306
// (template for). No anti-patterns.
#include <meta>
#include <string_view>
#include <type_traits>

template <typename E>
  requires std::is_enum_v<E>
constexpr std::string_view enum_name(E v) {
    template for (constexpr auto e :
                  std::define_static_array(std::meta::enumerators_of(^^E))) {
        if (v == [: e :]) return std::meta::identifier_of(e);
    }
    return "<unknown>";
}

enum class Color { Red, Green, Blue };
static_assert(enum_name(Color::Green) == "Green");
