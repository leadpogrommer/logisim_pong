asect 0x00
# 0xCD - undocummented instruction that sets SP to it's operrand
dc 0xcd, 0xdf

# CDM-8 mark 5 doesn't have reset pin, so we will use interrupts instead of it
# the following block of code enables interrupts
ldi r0, start   
push r0			# rti will jump to this address
ldi r0, 0x80	# rti will set PS to 0x80, so interrupts will be enabled
push r0
rti


# main logic goes here
# it computes the following formula: by + (228 - bx)*vy/vx
# 228 = x coordinate of our bat
# all numbers are 16-bit fixed-point (fractional part is stored in 7 least significant bits) big-endian
start:
ldi r0, bx		# load x coordinate of the ball into r2 and r3
ld r0, r2			
inc r0
ld r0, r3
not r2			# now we have -bx-1 in registers
not r3


ldi r1, 0x01    # add 228 + 1
add r1, r3
ldi r1, 0x72
addc r1, r2
# now we have 228 - bx in r2 and r3


# now multiply by vy
# since cdm-8 isn't powerful enough, we use hardware multiplier and divisor
# op  - operation code
# op1 - first operand
# op2 - second operand when writing, result when reading
ldi r0, op1		# set operand 1 to 228-bx
st r0, r2
inc r0
st r0, r3

# set operand 2 to vy
ldi r0, vy
ldi r1, op2
jsr mvnum

# set operation to multiplication (operation 0)
ldi r0, 0
ldi r1, op
st r1, r0

# we cannot just copy result to operand 1
# because when first byte of result is written to operand, result will immediately change
# so we store the product in memory
# TODO: rewrite it using registers only
ldi r0, op2
ldi r1, 0xc0
jsr mvnum

# now divide by vx
ldi r0, 0xc0		# set operand 1 to (228-bx)*vy
ldi r1, op1
jsr mvnum

ldi r0, vx			# set operand 2 to vx
ldi r1, op2
jsr mvnum

ldi r0, 1			# set operation to division (operation 1)
ldi r1, op
st r1, r0



# load y coorinate of the ball into r2, r3
ldi r0, by			
ld r0, r2
inc r0
ld r0, r3

# load (228-bx)*vy/vx into r0, r1
ldi r1, op2
ld r1, r0
inc r1
ld r1, r1

# add them and store result in r2, r3
add r1, r3
addc r0, r2

# now we only need contents of r2 since bat position are 5 bit
# if bit 7 of r2 is set, the ball was reflected either from top or from bottom
tst r2
bpl ready
# if reflection occured, we need to know was it top or bootom
# the following block of code handles it, but i cannot remember how
# TODO: understand my code	
ldi r0, vy
ld r0, r0
bmi low_negate 
# high_add_128
ldi r0, 127		
add r0, r2		
br ready
low_negate:
neg r2

# now we have our answer - bat coordinate
ready:
shl r2								# it was shifted right
ldi r0, 0b11111000					# we need only 5 high bits
and r0, r2

# in kinematic controller, bat coordinate represents it's lowest pixel
# but we want to reflect ball with central pixel
# so we decrease r2 if it is not zero
tst r2 								# probably unnecessary tst
bz do_write
ldi r0, 0b00001000
sub r2, r0
move r0, r2

# finally move bat
do_write:
ldi r0, bat
st r0, r2

# wait for reset interrupt in infinite loop
# TODO: figure out if wait or halt can be used here
endless_torture:br endless_torture

# this subroutine moves 16-bit numbers
# prameters:
# r0 - source addres
# r1 - destination address
mvnum:
ld r0, r2
st r1, r2
inc r0
inc r1 
ld r0, r2
st r1, r2
rts



# here defined addresses of io devices
# dc directives are for debugging
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

# This is the
end
# my only friend