#ifndef RENDERER_H
#define RENDERER_H

#include <ctime>
#include <string>
#include <stdint.h>


enum class RenderType {
    // Default
    MEMORY,
    // A file per frame. This should only be used for short test runs
    // not for a real ROM run.
    FILE,
    // No rendering.
    NONE,
};

class Renderer {
private:
    uint64_t _frames = 0;
    uint64_t _last_frames = 0;
    time_t _time = time(nullptr);
public:
    RenderType render_type = RenderType::MEMORY;
    std::string file_prefix = "";
    // TODO
    // Not sure if this architecture makes sense - these are the
    // actual pixel lookups.
    // The actual RGB values.
    uint8_t pixels[256 * 240 * 3] = { 0 };
private:
    void _memory_render(uint8_t* lut_values);
    void _file_render(uint8_t* lut_values);
public:
    void render(uint8_t* lut_values);
};

#endif
