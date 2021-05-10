import os
import sys
import math
from PIL import Image
import random
sys.path.append(os.path.join(sys.path[0], 'third_party'))
import cocas




def write_image(filename, arr):
    f = open(filename, mode='wb')
    f.write(bytes("v2.0 raw\n", 'UTF-8'))
    for byte in arr:
        f.write(bytes('%08x' % byte + '\n', 'UTF-8'))
    f.close()


def asm():
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd, 'third_party'))



    with open('../ai.asm') as asm_file:
        obj_code, _, err_msg = cocas.compile_asm(asm_file)  # type: (str, str, str)
    os.chdir(cwd)
    if err_msg is not None:
        print("COMPILE ERROR: ", err_msg)
        return
    # print(obj_code)

    rom = [0] * 256

    for line in obj_code.splitlines():
        if 'ABS' in line:
            mem_addr, mem_content = line.removeprefix("ABS").strip().split(':')
            mem_addr = int(mem_addr, 16)
            mem_content = list(map(lambda a: int(a, 16), mem_content.split()))  # type: [int]
            for byte in mem_content:
                if mem_addr > 255:
                    print("LINK ERROR: program too large")
                    return
                rom[mem_addr] = byte
                mem_addr += 1
    write_image('firmware/ai.img', rom)


def sin_cos():
    speed = 1
    max_angle = 0.906  # max angle that does not cause overflows (~ 52 deg)
    sins = []
    for i in range(0, 128):
        s = math.sin(i / 127 * max_angle) * speed
        # print(round(s*128))
        sins.append(round(s * 128))
    write_image('firmware/sin.img', sins)

    cos = []
    for i in range(0, 128):
        s = math.cos(i / 127 * max_angle) * speed
        # print(round(s*128))
        cos.append(round(s * 128))
    write_image('firmware/cos.img', cos)


def animations():
    os.chdir(os.path.join(os.getcwd(), 'animation'))
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

    def new_img() -> Image:
        return Image.new("1", (32, 32), 255)  # type: Image.Image

    def file_image(s: str) -> Image:
        return Image.open(s).convert('1')

    def scroll_down(a: Image, b: Image, frames: int) -> [Image]:
        res = []
        for d in range(0, 33, round(32 / frames)):
            ni = new_img()
            ni.paste(a, (0, -d))
            ni.paste(b, (0, 32 - d))
            res.append(ni)
        return res

    def still_image(a: Image, frames: int) -> [Image]:
        return [a.copy() for _ in range(frames)]

    def fade(a: Image, b: Image, frames: int):
        different_pixels = []
        for x in range(32):
            for y in range(32):
                if a.getpixel((x, y)) != b.getpixel((x, y)):
                    different_pixels.append((x, y))
        random.shuffle(different_pixels)
        im = a.copy()
        ret = [a.copy()]
        for i in range(frames - 1):
            to_take = len(different_pixels) // (frames - 1)
            to_process = different_pixels[i * to_take:(i + 1) * to_take] if i != frames - 1 else different_pixels[
                                                                                                 i * to_take:]
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
    print("End intro:", hex(len(bin_arr) - 1))

    print("Start win:", hex(len(bin_arr)))
    bin_arr += process(fade(file_image('black.png'), file_image('winner.png'), 16))
    print("End win:", hex(len(bin_arr) - 1))

    print("Start loose:", hex(len(bin_arr)))
    bin_arr += process(fade(file_image('black.png'), file_image('looser.png'), 16))
    print("End loose:", hex(len(bin_arr) - 1))

    f = open('../firmware/animation.img', mode='wb')
    f.write(bytes("v2.0 raw\n", 'UTF-8'))
    for byte in bin_arr:
        f.write(bytes('%08x' % byte + '\n', 'UTF-8'))
    f.close()


if __name__ == "__main__":
    os.chdir(sys.path[0])
    os.makedirs('firmware', exist_ok=True)
    os.makedirs('animation/frames', exist_ok=True)

    asm()
    sin_cos()
    animations()

