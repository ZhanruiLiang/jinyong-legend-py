# version 330 core

uniform ivec2 bigImgSize;
uniform ivec2 screenSize;

in vec2 vertexPosition;
in vec2 vertexUV;

out vec2 uv;

void main() {
    gl_Position = vec4(
        + float(vertexPosition.x) * 2/ screenSize.x,
        - float(vertexPosition.y) * 2/ screenSize.y, 
        0, 1
    );
    uv = vec2(float(vertexUV.s) / bigImgSize.x, float(vertexUV.t) / bigImgSize.y);
}
