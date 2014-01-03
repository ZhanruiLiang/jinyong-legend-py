target = parse_rle.so
src = parse_rle.pyx
flags = -O0

${target}: ${src}
	cython ${src} -o tmp.c
	gcc -shared -fPIC -I/usr/include/python3.3m/ ${flags} tmp.c -o ${target}

clean:
	-rm ${target} tmp.c
