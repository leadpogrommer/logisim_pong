from PIL import Image
import os


def process(filename: str) -> list[int]:
    img = Image.open(filename)  # type: Image.Image
    img = img.convert('1')
    arr = []
    for col in range(32):
        i = 0
        for row in range(32):
            pixel = img.getpixel((col, row))
            if pixel != 0:
                i = i | (1 << (31 - row))
        arr.append(i)
    return arr


def generate():
    win = Image.open("win.png").convert('1')  # type: Image.Image
    for i in range(32):
        ni = Image.new("1", (32, 32))  # type: Image.Image
        ni.paste(win, (31 - i, 0))
        ni.save('frames/%03d.png' % i)
    for j in range(30):
        i = j**2
        ni = Image.new("1", (32, 32))  # type: Image.Image
        ni.paste(win.resize((32+i, 32+i)), (-i//2, -i//2))
        ni.save('frames/%03d.png' % (j+32))


generate()

a = []
for f in sorted(os.listdir('frames')):
    a += process(f'frames/{f}')


f = open('anim.bin', mode='wb')
f.write(bytes("v2.0 raw\n", 'UTF-8'))
for byte in a:
    f.write(bytes('%08x' % byte + '\n', 'UTF-8'))
f.close()
