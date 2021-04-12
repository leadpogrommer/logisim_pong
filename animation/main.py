from PIL import Image
import os
import random

random.seed(228)


def process(imgs: [Image]) -> list[int]:
    arr = []
    for img in imgs:
        for col in range(32):
            i = 0
            for row in range(32):
                pixel = img.getpixel((col, row))
                if pixel != 0:
                    i = i | (1 << (31 - row))
            arr.append(i)
    return arr


def generate():
    win = Image.open("god_inv.png").convert('1')  # type: Image.Image
    for i in range(32):
        ni = Image.new("1", (32, 32))  # type: Image.Image
        ni.paste(win, (31 - i, 0))
        ni.save('frames/%03d.png' % i)
    for j in range(30):
        i = j**2
        ni = Image.new("1", (32, 32))  # type: Image.Image
        ni.paste(win.resize((32+i, 32+i)), (-i//2, -i//2))
        ni.save('frames/%03d.png' % (j+32))


# generate()


def new_img()-> Image:
    return Image.new("1", (32, 32), 255)  # type: Image.Image


def file_image(s: str) -> Image:
    return Image.open(s).convert('1')


def scroll_down(a: Image, b: Image, frames: int) -> [Image]:
    res = []
    for d in range(0, 33, round(32 / frames)):
        ni = new_img()
        ni.paste(a, (0, -d))
        ni.paste(b, (0, 32-d))
        res.append(ni)
    return res


def still_image(a: Image, frames: int) -> [Image]:
    return [a.copy() for _ in range(frames)]


def fade(a: Image, b: Image, frames: int):
    different_pixels = []
    for x in range(32):
        for y in range(32):
            if a.getpixel((x,y)) != b.getpixel((x, y)):
                different_pixels.append((x, y))
    random.shuffle(different_pixels)
    im = a.copy()
    ret = [a.copy()]
    for i in range(frames - 1):
        to_take = len(different_pixels) // (frames-1)
        to_process = different_pixels[i*to_take:(i+1)*to_take] if i != frames - 1 else different_pixels[i*to_take:]
        for pos in to_process:
            im.putpixel(pos, b.getpixel(pos))
        ret.append(im.copy())
    ret.append(b.copy())
    return ret


def generate_intro():
    frames = []
    team = file_image('team_logo.png')
    thanks = file_image('thanks.png')
    god = file_image('god.png')
    logo = file_image('logo.png')
    frames += still_image(team, 3)
    frames += scroll_down(team, thanks, 16)
    frames += fade(thanks, god, 10)
    frames += still_image(god, 10)
    frames += fade(god, logo, 10)
    frames += still_image(logo, 1)

    for i, f in enumerate(frames):
        f.save('frames/%03d.png' % i)
    return process(frames)


bin_arr = []

print("Start intro:", hex(len(bin_arr)))
bin_arr += generate_intro()
print("Start intro:", hex(len(bin_arr)-1))

print("Start win:", hex(len(bin_arr)))
bin_arr += process(fade(file_image('black.png'), file_image('winner.png'), 16))
print("Start win:", hex(len(bin_arr)-1))

print("Start loose:", hex(len(bin_arr)))
bin_arr += process(fade(file_image('black.png'), file_image('looser.png'), 16))
print("Start loose:", hex(len(bin_arr)-1))





f = open('anim.bin', mode='wb')
f.write(bytes("v2.0 raw\n", 'UTF-8'))
for byte in bin_arr:
    f.write(bytes('%08x' % byte + '\n', 'UTF-8'))
f.close()
