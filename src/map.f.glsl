# version 330 core

uniform sampler2D textureSampler;

in vec2 uv;
out vec4 fragColor;

void main() {
    fragColor = vec4(texture(textureSampler, uv));
}
