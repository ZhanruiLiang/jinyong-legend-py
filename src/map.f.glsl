# version 330 core

uniform sampler2D textureSampler;

in vec2 uv;
out vec4 fragColor;

void main() {
    /*fragColor = vec4(1., 0, 0, 1) * .99 + .01 * vec4(texture(textureSampler, uv));*/
    fragColor = vec4(texture(textureSampler, uv));
}
