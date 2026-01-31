#include "Renderer.h"
#include "Palettes.h"
#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <ctime>

std::string _PATH = "../_frames/";

void
Renderer::_memory_render(uint8_t* lut_values) {
    // 3 bytes per pixel.
    const uint8_t bytes_per_pixel = 3;
    // FIXME
    // Not actual pixels, theyre LUT values.
    for (int y = 0; y < 240; y++) {
        // Go row by row.
        for (int x = 0; x < 256; x++) {
            // Each column in the row.
            uint64_t input_idx = x + y * 256;
            uint8_t pixel_lookup = lut_values[input_idx];
            // Draw a debug grid over the output.
            // if (x % 8 == 0 || y % 8 == 0) {
            //     // Debug nametable grid with yellow.
            //     pixel_lookup = 0x37;
            // }
            // if (x % 0x20 == 0 || y % 0x20 == 0) {
            //     // Debug attribute grid with red.
            //     pixel_lookup = 0x16;
            // }
            // if (x % 0x10 == 0 || y % 0x10 == 0) {
            //     // Debug attributes quadrants with pink.
            //     pixel_lookup = 0x25;
            // }

            uint64_t output_idx = x * bytes_per_pixel + y * 256 * bytes_per_pixel;
            pixels[output_idx] = LUT[pixel_lookup][0];
            pixels[output_idx + 1] = LUT[pixel_lookup][1];
            pixels[output_idx + 2] = LUT[pixel_lookup][2];
        }
    }
}

void
Renderer::_file_render(uint8_t* lut_values) {
    std::string filepath = "-frame_" + std::to_string(_frames) + ".ppm";
    if (file_prefix != "") {
        filepath = file_prefix + filepath;
    } else {
        filepath = std::to_string(std::time(nullptr)) + filepath;
    }
    filepath = _PATH + filepath;

    // printf("%s\n", filepath.c_str());
    FILE* f = fopen(filepath.c_str(), "a+");
    if (NULL == f) {
        printf("Failed to render to file at path %s\n", filepath.c_str());
        return;
    }

    fprintf(f, "P3\n");
    fprintf(f, "256 240\n");
    fprintf(f, "255\n");
    for (int y = 0; y < 240; y++) {
        // Go row by row.
        for (int x = 0; x < 256; x++) {
            // Each column in the row.
            uint64_t idx = x + y * 256;
            uint8_t pixel_lookup = lut_values[idx];

            // Draw a debug grid over the output.
            // if (x % 8 == 0 || y % 8 == 0) {
            //     // Debug nametable grid with yellow.
            //     pixel_lookup = 0x37;
            // }
            // if (x % 0x20 == 0 || y % 0x20 == 0) {
            //     // Debug attribute grid with red.
            //     pixel_lookup = 0x16;
            // }
            // if (x % 0x10 == 0 || y % 0x10 == 0) {
            //     // Debug attributes quadrants with pink.
            //     pixel_lookup = 0x25;
            // }
            fprintf(f, "%d %d %d ",
                LUT[pixel_lookup][0],
                LUT[pixel_lookup][1],
                LUT[pixel_lookup][2]
            );
        }
        fprintf(f, "\n");
    }
    fclose(f);
}

void
Renderer::render(uint8_t* pixels) {
    _frames++;
    // Did 1 second elapse?
    time_t now = time(nullptr);
    double delta_seconds = difftime(now, _time);
    // TODO
    // Find a better way to compute FPS.
    if (delta_seconds >= 1) {
        // Around 1 second has elapsed, how many frames were
        // made in that time?
        uint64_t fps = _frames - _last_frames;
        _time = now;
        _last_frames = _frames;
        // TODO
        // Temp.
        printf("FPS: %llu %lf\n", fps, delta_seconds);
    }
    switch (render_type) {
        case RenderType::MEMORY:
            return _memory_render(pixels);
        case RenderType::FILE:
            return _file_render(pixels);
        case RenderType::NONE:
            printf("frame %llu\n", _frames);
            return;
    }
}
