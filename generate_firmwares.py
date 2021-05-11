import os
import sys
import math
from PIL import Image
import random
sys.path.append(os.path.join(sys.path[0], 'third_party'))
import cocas

# This code is badly structured because it was merged from three different files
# Yes, I know about midules


def write_image(filename: str, arr: list):
    """
    Write the contents or array into file in logisim-compatible format

    :param filename: Path to output file
    :param arr: Array to be written
    """
    f = open(filename, mode='wb')
    f.write(bytes("v2.0 raw\n", 'UTF-8'))
    for byte in arr:
        f.write(bytes('%08x' % byte + '\n', 'UTF-8'))
    f.close()


def asm():
    """
    Compile ai.asm and write resulting code to firmware/ai.img
    """
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd, 'third_party'))

    with open('../ai.asm') as asm_file:
        # we use cocas from CocoIDE distribution
        obj_code, _, err_msg = cocas.compile_asm(asm_file)  # type: (str, str, str)
    os.chdir(cwd)
    if err_msg is not None:
        print("COMPILE ERROR: ", err_msg)
        return

    rom = [0] * 256

    # this primitive linker ignores code overlapping
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
    """
    Write sin(a) and cos(a) for 127 different values of a in [0; max_angle]
    into corresponding roms
    """
    speed = 1
    max_angle = 0.906  # max angle that does not cause overflows (~ 52 deg)
    sins = []
    for i in range(0, 128):
        s = math.sin(i / 127 * max_angle) * speed
        sins.append(round(s * 128))
    write_image('firmware/sin.img', sins)

    cos = []
    for i in range(0, 128):
        s = math.cos(i / 127 * max_angle) * speed
        # print(round(s*128))
        cos.append(round(s * 128))
    write_image('firmware/cos.img', cos)


def animations():
    """
    Create startup and game over animations
    convert them into binary format that video_player chip uses
    and write it to firmware/animation.img
    """
    os.chdir(os.path.join(os.getcwd(), 'animation'))
    # Needed for fade effect to be the same every run
    random.seed(228)


    def process(imgs: [Image]) -> list[int]:
        """
        Convert list of images into animation for video chip.
        Every image is represented as 32 32-bit integers,
        where each integer represents one column on display

        :param imgs: List of PIL images
        :return: List of 32 bit numbers
        """
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
        """
        :return: Empty white image
        """
        return Image.new("1", (32, 32), 255)  # type: Image.Image


    def file_image(s: str) -> Image:
        """
        :param s: Path to image file
        :return: Image from file converted to 1-bit format
        """
        return Image.open(s).convert('1')



    def scroll_down(a: Image, b: Image, frames: int) -> [Image]:
        """
        Create sliding transition from first image to second.
        Resulting animation will take specified amount of frames (not really accurate)

        :param a: First image
        :param b: Second Image
        :param frames: Number of frames
        :return: List of images - resulting animation
        """
        res = []
        for d in range(0, 33, round(32 / frames)):
            ni = new_img()
            ni.paste(a, (0, -d))
            ni.paste(b, (0, 32 - d))
            res.append(ni)
        return res

    def still_image(a: Image, frames: int) -> [Image]:
        """Repeat still image for specified amount of frames"""
        return [a.copy() for _ in range(frames)]


    def fade(a: Image, b: Image, frames: int):
        """
        Create fading transition from first image to second.
        Resulting animation will take specified amount of frames (not really accurate)

        :param a: First image
        :param b: Second Image
        :param frames: Number of frames
        :return: List of images - resulting animation
        """

        # we only need to change pixels with different colors
        different_pixels = []
        for x in range(32):
            for y in range(32):
                if a.getpixel((x, y)) != b.getpixel((x, y)):
                    different_pixels.append((x, y))

        # we will change them in random order
        random.shuffle(different_pixels)
        im = a.copy()
        ret = [a.copy()]
        for i in range(frames - 1):
            # Each frame we will change equal amount of pixels
            to_take = len(different_pixels) // (frames - 1)
            # last frame is special case - since to_take was rounded down, there will be more pixels
            # so we change all remaining pixels
            to_process = different_pixels[i * to_take:(i + 1) * to_take] if i != frames - 1 else different_pixels[
                                                                                                 i * to_take:]
            for pos in to_process:
                im.putpixel(pos, b.getpixel(pos))
            ret.append(im.copy())
        ret.append(b.copy())
        return ret

    def generate_intro():
        """Generate animation that will play on system start"""
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
            # All frames of animation are saved for debugging purposes
            f.save('frames/%03d.png' % i)
        return process(frames)

    bin_arr = []

    # Addresses printed here must be manually put into video_chip constants
    # so it will know where every animation starts and ends
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

