asect 0x00
# 0xCD - undocummented instruction that sets SP to it's operrand
dc 0xcd, 0xfb    


start:
ldi r3, vx
ld r3, r3
tst  r3
bmi start	# ball is moving towards player

ldi r3, bx
ld r3, r3
not r3
xor r0, r0
shr r3

ldi r2, vy
ld r2, r2
tst r2
bpl nonneg
neg r3
nonneg:
# r3 now contains dy of ball



ldi r2, bat
st r2, r3



br start

asect 0xfb
vx:

asect 0xfc
vy:dc -1

asect 0xfd
bx: dc 100

asect 0xfe
by:

asect 0xff
bat:ds 1

end