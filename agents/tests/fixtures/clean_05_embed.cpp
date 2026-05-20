// C++26 #embed (P1967). No objcopy comments; no incbin include.
#include <array>

inline constexpr std::array<unsigned char, /* deduced */ > kIcon = {
    #embed "assets/icon.png" if_empty(0)
};

static_assert(kIcon.size() > 0);
