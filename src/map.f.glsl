# version 330 core

uniform sampler2D textureSampler;

in vec2 uv;
out vec4 fragColor;

void main() {
    vec4 color = texture(textureSampler, uv);
    const float a0 = .0;
    fragColor = vec4(color.rgb, a0 + (1-a0) * color.a);
    /*fragColor = vec4(texture(textureSampler, uv));*/
}
