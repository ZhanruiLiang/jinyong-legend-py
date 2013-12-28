import os

for f in os.listdir('.'):
    name, ext = os.path.splitext(f)
    if ext == '.mid' and not os.path.exists(name + '.ogg'):
        os.system('timidity {} -Ov'.format(f))
