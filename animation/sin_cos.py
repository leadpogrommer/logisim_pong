import math


def write_image(filename, arr):
    f = open(filename, mode='wb')
    f.write(bytes("v2.0 raw\n", 'UTF-8'))
    for byte in arr:
        f.write(bytes('%08x' % byte + '\n', 'UTF-8'))
    f.close()


speed = 1
max_angle = 0.906 # max angle that does not cause overflows (~ 52 deg)
sins = []
for i in range(0, 128):
    s = math.sin(i / 127 * max_angle) * speed
    # print(round(s*128))
    sins.append(round(s*128))
write_image('sin.img', sins)


coss = []
for i in range(0, 128):
    s = math.cos(i / 127 * max_angle) * speed
    # print(round(s*128))
    coss.append(round(s*128))
write_image('cos.img', coss)



for i in range(0, 128):
    print(((sins[i]/128)**2 + (coss[i]/128)**2)**0.5)
