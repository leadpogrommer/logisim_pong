asect 0x00
# 0xCD - undocummented instruction that sets SP to it's operrand
dc 0xcd, 0xdf

ldi r0, start
push r0
ldi r0, 0x80
push r0
rti



start:

ldi r0, op
ldi r1, 0b00000010
st r0, r1
xor r1,r1
st r0,r1




ldi r0, bx
ld r0, r2
not r2
inc r0
ld r0, r3
not r3
# r2 - high, r3 - low
# use w + 1
ldi r1, 0x01
add r1, r3
ldi r1, 0x72
addc r1, r2
# now multiply by vy
ldi r0, op1
st r0, r2
inc r0
st r0, r3

# set second operand to vy
ldi r0, vy
ldi r1, op2
jsr mvnum

#set operation to multiplication
ldi r0, 0
ldi r1, op
st r1, r0

# now begin division
ldi r0, op2
ldi r1, 0xc0
jsr mvnum

ldi r0, 0xc0
ldi r1, op1
jsr mvnum

ldi r0, vx
ldi r1, op2
jsr mvnum

#set operation to division
ldi r0, 1
ldi r1, op
st r1, r0


#ldi r0, op2
#ldi r1, 0xc3
#jsr mvnum


ldi r0, by
ld r0, r2
inc r0
ld r0, r3
# r2 - high, r3 - low
ldi r1, op2
ld r1, r0
inc r1
ld r1, r1


add r1, r3
addc r0, r2
# now we need r2

#ldi r0, 0xc6
#st r0, r2
#inc r0
#st r0, r3


tst r2
bpl ready
ldi r0, vy
ld r0, r0
bmi low_negate 
# high_add_128
ldi r0, 127
add r0, r2
br ready

low_negate:
neg r2

ready:
shl r2
# now we need only 5 high bits
ldi r0, 0b11111000
and r0, r2

tst r2 # probably unnecessary tst
bz do_write
ldi r0, 0b00001000
sub r2, r0
move r0, r2

do_write:
ldi r0, bat
st r0, r2


finish:br finish


mvnum:
# r0 - source
# r1 - destination
ld r0, r2
st r1, r2
inc r0
inc r1 
ld r0, r2
st r1, r2
rts






asect 0xe0
varA: ds 2
w: dc 0x80, 0x00


asect 0xf2
bx: dc 0x19, 0x80

asect 0xf4
by:

asect 0xf6
vx: dc 0x13,0x37

asect 0xf8
vy:

asect 0xfa
op1:

asect 0xfc
op2:

asect 0xfe
op:

asect 0xff
bat:


end