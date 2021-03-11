asect 0x00

ldi r0, bat
start:
ld r0, r1
inc r1
st r0, r1
br start

asect 0xf8
bx:

asect 0xf9
by:

asect 0xfA
vx:

asect 0xfB
vy:

asect 0xff
bat:

end