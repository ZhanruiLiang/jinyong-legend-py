# version 330 core

uniform vec2 screenSize;
uniform sampler2D textureSampler;
uniform float zoomRate;

in vec2 vertexPosition;
in vec2 vertexUV;

out vec2 uv;

void main() {
    ivec2 tSize = textureSize(textureSampler, 0);
    gl_Position = vec4(
        + float(vertexPosition.x) * 2 / screenSize.x,
        - float(vertexPosition.y) * 2 / screenSize.y, 
        0, 1
    ) * zoomRate;
    uv = vec2(float(vertexUV.s) / tSize.x, float(vertexUV.t) / tSize.y);
}
