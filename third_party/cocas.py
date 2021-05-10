#!/usr/bin/env python3
# CdM8 assembler

# V1 (c) Prof. Alex Shaferenko.  July 2015
# V1.1. Some modifications by M L Walters, August/Sept 2015
# V2 Adapted for cocideV0.8 Oct 2016
# V2.3: Error message bug fixed for cocoideV0.9
# V2.4: Macro compile bug fixed for CocoIDEV0.992+

# Python 2 and 3 compatibility
from __future__ import absolute_import, division, print_function
try:
    input=raw_input # Python 3 style input()
except:
    pass


asmver="2.3"

import os,sys
import time
import argparse


###################### C D M 8  A S S E M B L E R  Facilities
#

# Variables and dictionaries

text=[]
PC=0
Rel=False
rellist = {}
exts = {}
ents = {}
abses= {}
labels = {}
rsects = {}
macros = {}
labels["$abs"]={}
ents["$abs"]={}
tpls={}
Tpl=False
DsIns=False
tplName=""
generated=[]
args=None
gotminus=False
errorMsg=""
"""
global SectName=None
global mname
global mcalls
global marity
global mcount
global macdef
global pars
"""




# Used by CocoIDE when imported
retError=False
errorMsg=""
errLine=None
# Instruction set

bi=2   # binary arithmetic/logic & ld/st ops
un=1    # unary arithmetic/logic & stack/immediate ops
zer=0   # 0-addr commands
br=-1   # branches
spmove=-2 # stack setting and offsetting
bbne=-2 # branch back
osix=-3 # osix, extended OS interrupt
spec=-4 # special assembler instructions
mc=-5   # assembler macro/mend commands
mi=-6   # macro instruction

iset={
# binary
    "move": (0x00,bi),
    "add":  (0x10,bi),
    "addc": (0x20,bi),
    "sub": (0x30,bi),
    "and":  (0x40,bi),
    "or":   (0x50,bi),
    "xor":  (0x60,bi),
    "cmp":  (0x70,bi),
# unary
    "not":  (0x80,un),
    "neg":  (0x84,un),
    "dec":  (0x88,un),
    "inc":  (0x8C,un),
    "shr":  (0x90,un),
    "shla": (0x94,un),
    "shra": (0x98,un),
    "rol":  (0x9C,un),
# memory
    "st":   (0xA0,bi),
    "ld":   (0xB0,bi),
    "ldc":  (0xF0,bi),
# stack
    "push": (0xC0,un),
    "pop":  (0xC4,un),
#    "stsp": (0xC8,un),  # mark 3 Architecture # Not needed as macro replacements done: Mick June 2018
#    "ldsp": (0xCC,un),  # mark 3 Architecture
    "ldsa": (0xC8,un),      # mark 4 architecture
    "addsp": (0xCC,spmove),      # mark 4 architecture
    "setsp": (0xCD,spmove),      # mark 4 architecture
    "pushall": (0xCE,zer),      # mark 4 architecture
    "popall": (0xCF,zer),      # mark 4 architecture

# load immediate
    "ldi":  (0xD0,un),

# clock control
    "halt":  (0xD4,zer),
    "wait":  (0xD5,zer),

# immediate address
    "jsr": (0xD6,br),
    "rts": (0xD7,zer),
    
# interrupts
    "ioi":  (0xD8,zer),
    "rti":  (0xD9,zer),
    "crc":  (0xDA,zer),
    "osix": (0xDB,osix),

# branches
    "beq": (0xE0,br),
    "bz":  (0xE0,br),
    "bne": (0xE1,br),
    "bnz": (0xE1,br),
    "bhs": (0xE2,br),
    "bcs": (0xE2,br),
    "blo": (0xE3,br),
    "bcc": (0xE3,br),
    "bmi": (0xE4,br),
    "bpl": (0xE5,br),
    "bvs": (0xE6,br),
    "bvc": (0xE7,br),
    "bhi": (0xE8,br),
    "bls": (0xE9,br),
    "bge": (0xEA,br),
    "blt": (0xEB,br),
    "bgt": (0xEC,br),
    "ble": (0xED,br),
    "br":  (0xEE,br),
    "nop": (0xEF,br),
    "lchk": (0,br),


#
# assembler commands
    "asect":    (0,spec),
    "rsect":    (0,spec),
    "tplate":    (0,spec),
    "ext":      (0,spec),
    "ds":       (0,spec),
    "dc":       (0,spec),
#
# macro facilities
    "macro":    (0,mc),
    "mend":     (0,mc),
#
    "end":      (0,spec)


}


class LE(Exception):
    def __init__(self,i,m):
        global errLine
        #errLine = i
        print("LE",i,m)#debug
        global retError, errorMsg
        #print("**", retError)
        #if retError:
        #    errorMsg = "LINE "+ str(i) +": "+m
        #else:
        errorMsg = m
        #errorMsg += "\n"+m
        self.ind=i
        self.msg=m

class SE(Exception):
    def __init__(self,i,m):
        global retError, errorMsg
        #print("SE",i,m)#debug
        #if retError:
        #    errorMsg = "LINE "+ str(i) +": "+m
        #else:
        if not macdef:
            errorMsg = m
        #errorMsg += "\n"+m
        self.ind=i
        self.msg=m



def lex(s):
    global gotminus
    def hexbyte(s):
        w=s
        w=w.lower()
        k="0123456789abcdef".find(w[0])
        m="0123456789abcdef".find(w[1])
        if m<0 or k<0: return -1
        return 16*k+m
    ln=len(s)
    if ln==0: return ["emp",-1,0]
    i=0
    while s[i]==' ' or s[i]=='\t' or s[i]=='#':
        if i==ln-1 or s[i]=='#': return ["emp",-1,0]
        else: i=i+1
    x=s[i]
    if x.isalpha() or x=="_": CAT="id"
    elif x.isdigit(): CAT="num"
    elif x==":" or x=="," or x=="+" or x=="-" or x==">" or x=="/" or x=="'" or x=="?" or x=="!" or x==".":  CAT=x
    elif x=='\"': CAT="str"
    elif x=='$': CAT="par"
    else: raise   LE(i, "Illegal character \'"+x+"\'")

    if CAT=="ws":
        while x==' ' or x=="\t":
            if i== ln-1:
                i=-1
                break
            i=i+1
            x=s[i]
        return [CAT, i, 0]
    elif CAT=="id":
        VAL=""
        while x.isalnum() or x=="_":
            VAL=VAL+x
            if i== ln-1:
                i=-1
                break
            i=i+1
            x=s[i]
        if len(VAL)==1 : return [CAT,i,VAL]
        if (VAL[0]=="r" or VAL[0]=="R") and VAL[1].isdigit():
            CAT="reg"
            VAL=int(VAL[1])
            if VAL > 3:
                raise LE(i,"Illegal register number "+str(VAL))
        return [CAT, i, VAL]
    elif CAT=="par":
        if i < ln-1:
            if not s[i+1].isdigit():
                raise LE(i,"Expect a digit after a $")
            return (CAT,i+2,int(s[i+1]))
    elif CAT=="num":
        if ln-1>=i+1 and s[i:i+2]=="0x":
            if gotminus:
                raise   LE(i, "Signed hexadecimal not allowed")
            if ln-1<i+3:
                raise   LE(i, "Illegal hexadecimal")
            k=hexbyte(s[i+2:i+4])
            if k<0:
                raise   LE(i, "Illegal hexadecimal")
            if ln-1>i+3:
                return [CAT,i+4,k]
            else:
                return [CAT,-1,k]

        if ln-1>=i+1 and s[i:i+2]=="0b":
            if gotminus:
                raise   LE(i, "Signed binary not allowed")
            if ln-1<i+9:
                raise   LE(i, "Illegal binary")
            k=0
            for x in s[i+2:i+10]:
                if "01".find(x)<0: raise   LE(i, "Illegal binary")
                k=k*2+int(x)
            if ln-1>i+9:
                return [CAT,i+10,k]
            else:
                return [CAT,-1,k]

        k=0
        gotminus=False
        while x.isdigit():
            k=10*k+int(x)
            if i==ln-1:
                if k>255:
                    raise LE(i,"Decimal out of range")
                return [CAT,-1,k]
            else:
                i=i+1
                x=s[i]
        if k>255:
            raise LE(i,"Decimal out of range")
        return [CAT,i,k]
    elif CAT=="str":
        w=""
        x=''
        while x!='\"':
            if i==ln-1: raise LE(i, "Runaway string")
            if x!='\\' :
                w=w+x
                i=i+1
            elif s[i+1]=='\\':
                w=w+x
                i=i+2
            elif s[i+1]=='\"':
                w=w+'\"'
                i=i+2
            else:
                raise   LE(i, "Unknown escape character \\"+s[i+1])
            x=s[i]
        if i==ln-1:
            return [CAT,-1,w]
        else:
            return [CAT,i+1,w]

    else:
        if ln==1:
            i=-1
        else: i=i+1
        if CAT=="-":
            gotminus=True
        else:
            gotminus=False
        return [CAT,i,0]

def lexline(linum,s):
    global gotminus, errLine
    gotminus=False
    s0=s
    r=[]
    ind=0
    ptr=0
    while ind>=0:
        cat=None
        val=None
        ind=None
        try:
            [cat,ind,val]=lex(s)
            #print("**", cat)# debug
        except LE as e:
            errLine = linum # Picked up by cocoide
            #EP( "On line "+str(linum)+" \n"+str(s0)+"\nERROR: "+e.msg)
            e.msg.strip("\n")
            EP("ERROR On line "+str(linum)+": "+str(s0[0:ptr+e.ind])+str(s0[ptr+e.ind:])+"\n "+e.msg)
        #if not cat or not ind or not val:
        #    errLine = linum # Picked up by cocoide
        #    EP( "On line "+str(linum)+ "ERROR: Bad OP Code" )
        if (cat == "emp" and len(r)==0) or cat!="emp":
            r=r+[(cat,val,ptr)]
        if ind>=0: ptr+= ind
        s=s[ind:]
    return r

def asmline(s, linum, passno):
    global SectName
    global rellist
    global exts
    global ents
    global abses
    global labels
    global rsects
    global PC
    global Rel
    global mname
    global mcalls
    global marity
    global mcount
    global macdef
    global pars
    global DsIns
    global tpls
    global Tpl
    global tplName
    global errorMsg

    def parse_exp(lst):
        opsynt=[lst[j][0] for j in range(3)]
        if (opsynt[0:2]== ["num","end"]):
            return lst[0][1]
        if opsynt[0]=="id":
            lbl=lst[0][1]
            if SectName != -1 and lbl in labels[SectName]:
                Value=labels[SectName][lbl]
            elif lbl in abses:
                Value=abses[lbl]
            else:
                if opsynt[1]==":":
                    raise SE(-1,lst[2][1])
                raise SE(lst[0][2],"Label "+lbl+" not found")
            if opsynt[1]=="end" or opsynt[1]==":":
                return Value
            if opsynt[1]=="+":
                sign=1
            elif opsynt[1]=="-":
                sign=-1
            else:
                raise SE(lst[1][2],"Only + or - allowed here")
            if opsynt[2]!="num":
                raise SE(lst[2][2],"Illegal offset")
            return ((Value+sign*lst[2][1])+256) % 256
        elif (opsynt[0:3]== ['-',"num","end"]):
            if lst[1][1]>128:
                raise SE(lst[1][2],"Negative out of range")
            return ((lst[1][1]^0xff)+1) % 256
        else:
            raise SE(lst[0][2],"Label or number expected")

    def test_end(item):
        if (item[0]!="end"):
            raise SE(item[2],"Unexpected text")
        return 0

    cmd=lexline(linum,s)+[('end',0,0)]*3
    if errorMsg !="": return
    if cmd[0][0]=="emp": return ("",0,[])
    if cmd[0][0]!="id":
        raise SE(cmd[0][2],"Label or opcode expected")
    else:
        next=1
        label=""
        opcode=cmd[0][1]
        pos=cmd[0][2]
        if cmd[1][0]==':' or cmd[1][0]=='>':
            if cmd[2][0]=="id" or cmd[2][0]=="end":
                next=3
                if cmd[1][0]==':' :
                    label=cmd[0][1]
                else:
                    label='>'+cmd[0][1]
                opcode=cmd[2][1]
                pos=cmd[2][2]
                if cmd[2][0]=="end":
                    return (label,0,[])
            else:
                raise SE(cmd[2][2], "Illegal opcode")
        if opcode not in iset:
            #print(pos, "Invalid opcode: "+opcode)#debug
            raise SE(pos, "Invalid opcode: "+opcode)
        (bincode,cat)=iset[opcode]
        if cat==bi:
            if (cmd[next][0]!= "reg"): raise SE(cmd[next][2],"Register expected")
            if (cmd[next+1][0]!= ","): raise SE(cmd[next][2],"Comma expected")
            if (cmd[next+2][0]!= "reg"): raise SE(cmd[next+2][2],"Register expected")
            test_end(cmd[next+3])
            x=bincode+4*cmd[next][1]+cmd[next+2][1]
            return(label,1,[x])
        if cat==un:
            #print("*", args.v3)#debug
            #if opcode in ("ldsp","stsp") and not args.v3: raise SE(cmd[next][2],"Use option -v3 to compile Mark 3 instructions")
            if opcode in ("ldsa","addsp","setsp","pushall","popall") and args.v3: raise SE(cmd[next][2],"option -v3 forbids use of Mark 4 instructions")
            if cmd[next][0]!= "reg": raise SE(cmd[next][2],"Register expected")

            if cmd[next][0]!= "reg": raise SE(cmd[next][2],"Register expected")
            x=bincode+cmd[next][1]
            if opcode=="ldi" or opcode=="ldsa":
                if (cmd[next+1][0]!= ","): raise SE(cmd[next+1][2],"Comma expected")
                if passno==1:
                        return (label,2,[x,0])
                elif cmd[next+2][0]=="str":
                    strVal=cmd[next+2][1]
                    if len(strVal)>1:
                        raise SE(cmd[next+2][2],"Single character expected")
                    if opcode=="ldsa":
                        raise SE(cmd[next+2][2],"ldsa requires a number or a template field")
                    return(label,2,[x,ord(strVal[0])])
                elif cmd[next+3][0]==".":  # template reference
                    if cmd[next+2][0]!="id":
                        raise SE(cmd[next+2][2],"Template name expected")
                    if cmd[next+2][1] not in tpls:
                        raise SE(cmd[next+2][2],"Unknown template")
                    tn=cmd[next+2][1]
                    if cmd[next+4][0]!="id":
                        raise SE(cmd[next+4][2],"Field name expected")
                    if cmd[next+4][1] not in tpls[tn]:
                        raise SE(cmd[next+4][2],"Unknown field name")
                    if cmd[next+5][0]!="end":
                        raise SE(cmd[next+5][2],"unexpected token after template field")
                    y=tpls[tn][cmd[next+4][1]]
                    return (label,2,[x,y])
                else:
                    Value=parse_exp(cmd[next+2:next+5])
                    test_end(cmd[next+5])
                    lbl=cmd[next+2][1]
                    if Rel and cmd[next+2][0]=="id" and lbl not in abses and lbl not in exts:
                        rellist[SectName]+=[PC+1]
                    if cmd[next+2][0]=="id" and cmd[next+2][1] in exts and not macdef:
                        exts[cmd[next+2][1]] += [(SectName,PC+1)]
                    return (label,2,[x,Value])
            else:
                if cmd[next+1][0]!="end":
                    raise SE (cmd[next+1][2],"Only one operand expected")
                return (label,1,[x])

        if cat==br:
                if passno==1:
                    if opcode=="lchk":
                        return(label,0,[])
                    return(label,2,[bincode,0])
                else:
                    if opcode=="ldsa" and cmd[next+2][0] not in ("num","-"):
                        raise SE(cmd[next+2][2],"ldsa requires a number or a template field")
                    Value=parse_exp(cmd[next:next+3])
                    test_end(cmd[next+3])
                    lbl=cmd[next][1]
                    if Rel and opcode!="lchk" and lbl not in abses and lbl not in exts:
                        rellist[SectName]+=[PC+1]
                    if cmd[next][0]=="id" and cmd[next][1] in exts and not macdef:
                        exts[cmd[next][1]] += [(SectName,PC+1)]
                    if opcode=="lchk":
                        return(label,0,[])
                    return (label,2,[bincode,Value])
        if cat==osix:
                if cmd[next][0]!="num":
                    raise SE(cmd[next][2],"Number expected")
                test_end(cmd[next+1])
                return (label,2,[bincode,cmd[next][1]])

        if cat==zer:
                return(label,1,[bincode])

        if cat==spmove:             # addsp/setsp
                if passno==1:
                        return (label,2,[0,0])
                mynext=next
                mymult=1
                if cmd[mynext][0]=="-":
                    mynext=next+1
                    mymult=-1
                if cmd[mynext][0]=="num":
                    test_end(cmd[mynext+1])
                    return (label,2,[bincode,mymult*cmd[mynext][1]])

                if cmd[mynext][0]!="id" or cmd[mynext+1][0]!="." or cmd[mynext+2][0]!="id":
                    raise SE(cmd[mynext][2],"addsp/setsp instructions require a number or a template field operand")
                if cmd[mynext][1] not in tpls:
                        raise SE(cmd[mynext][2],"Unknown template '"+cmd[mynext][1]+"'")
                test_end(cmd[mynext+3])
                tn=cmd[mynext][1]
                return(label,2,[bincode,mymult*tpls[tn][cmd[mynext+2][1]]])

        ################################################## M A C R O FACILITIES
        if cat==mc:
            if opcode =="macro":
                if macdef:
                    return ["",-3,0]
                if label!="":
                   raise SE(0,"Label not allowed")
                if cmd[next][0]!="id":
                    raise SE(cmd[next][2],"Name expected")
                mname=cmd[next][1]
                if mname in iset:
                    if iset[mname][1]!=mi:
                        raise SE(cmd[next][2],"Opcode '"+mname+"' reserved by assembler")
                if cmd[next+1][0]!="/":
                    raise SE(cmd[next+1][2],"/ expected")
                if cmd[next+2][0]!="num":
                    raise SE(cmd[next+2][2],"Number expected")
                test_end(cmd[next+3])
                marity=cmd[next+2][1]
                return ["",-3,0]
            elif opcode =="mend":
                test_end(cmd[next])
                return ["",-4,0]
        if cat==mi:
            if passno==2 or macdef:
                return ["",0,[]]
            mcalls += 1
            if mcalls > 800:
                raise SE(0,"Too many macro expansions [>800]")
            pars=commasep(cmd[next:])
            parno=len(pars)
            if opcode+"/"+str(parno) not in macros:
                raise SE(cmd[next][2],"Number of params ("+str(parno)+") does not match definition of macro "+opcode)

            if label=="":
                ll=[]
            elif label[0]==">":
                ll=[label[1:]+">"]
            else:
                ll=[label+":"]

            mbody=["# >>>>>>"]+ll+macros[opcode+"/"+str(parno)]+["# <<<<<<"]
            newbody=[]
            for s1 in mbody:
                if args != None and args.dbg: print("before => "+s1+" ******* pars= "+str(pars)+"mvars="+str(mvars))
                rslt= mxpand(s1,0,parno)
                if args != None and args.dbg: print("after  => "+str(rslt))
                if not ismstack(linum,rslt):
                    newbody += [rslt+"#"+chr(1)]
            mcount += 1
            return ["",-5,newbody]
        ################################################## END OF MACRO FACILITIES

        if macdef:
            return ["",0,0]
        if cat==spec:
            if opcode=="ds":
                if (cmd[next][0]!="num"):
                    raise SE(cmd[next][2],"Number expected")
                test_end(cmd[next+1])
                DsIns=True
                return (label,cmd[next][1],[0]*cmd[next][1])
            if opcode=="dc":
                img=[]
                empty=True
                DsIns=True
                while cmd[next][0]!="end":
                    empty=False
                    if cmd[next][0]=="num":
                        img+=[cmd[next][1]]
                    elif cmd[next][0]=="-" and cmd[next+1][0]=="num":
                        if cmd[next+1][1]>128:
                            raise SE(cmd[next+1][2],"Negative out of range")
                        img+=[ ( (cmd[next+1][1]^255) +1) % 256 ]
                        next+=1
                    elif cmd[next][0]=="str":
                        for c in cmd[next][1]:
                            img+=[ord(c)]
                    elif cmd[next][0]=="id":
                        if passno==1:
                            img+=[0]
                            if cmd[next+1][0]=='+' or cmd[next+1][0]=='-':
                                next+=2
                        else:
                            exp=cmd[next:next+3]
                            exp = [x if x[0]!="," else ["end",0,0] for x in exp]
                            Value=parse_exp(exp)
                            if Rel and exp[0][1] not in abses and exp[0][1] not in exts:
                                rellist[SectName]+=[PC+len(img)]
                            if cmd[next][0]=="id" and cmd[next][1] in exts and not macdef:
                                exts[cmd[next][1]] += [(SectName,PC+len(img))]

                            img+=[Value]

                            if cmd[next+1][0]=='+' or cmd[next+1][0]=='-':
                                next+=2

                    else:
                        raise SE(cmd[next][2],"Illegal constant")

                    if cmd[next+1][0]==',':
                        empty=True
                        next+=2
                    elif cmd[next+1][0]!='end':
                        raise SE(cmd[next+1][2],"Illegal separator")
                    else:
                        return (label,len(img),img)
                if empty:
                    raise SE(cmd[next][2],"Data expected")

            if opcode=="asect":
                if label!="":
                   raise SE(0,"Label not allowed")
                if (cmd[next][0]!="num"):
                    raise SE(cmd[next][2],"Numerical address expected")
                addr=cmd[next][1]
                if addr<0:
                    raise SE(cmd[next][2],"Illegal number")
                test_end(cmd[next+1])
                if Rel:
                    rsects[SectName]=PC
                    Rel=False
                if Tpl:
                    Tpl=False
                    tpls[tplName]["_"]=PC
                PC=addr
                SectName="$abs"
                return ("",-1,0)
            if opcode=="tplate":
                if label!="":
                   raise SE(0,"Label not allowed")
                if (cmd[next][0]!="id"):
                    raise SE(cmd[next][2],"Name expected")
                if Rel:
                    rsects[SectName]=PC
                Rel=False
                if cmd[next][1] in tpls and passno==1:
                    raise SE(cmd[next][2],"Template already defined")
                PC=0
                Tpl=True
                tplName = cmd[next][1]
                if tplName not in tpls:
                    tpls[tplName]={}
                SectName=-1
                return("",-1,0)
            if opcode=="rsect":
                if label!="":
                   raise SE(0,"Label not allowed")
                if (cmd[next][0]!="id"):
                    raise SE(cmd[next][2],"Name expected")
                test_end(cmd[next+1])
                if Rel:
                    rsects[SectName]=PC
                Rel=True
                if Tpl:
                    Tpl=False
                    tpls[tplName]["_"]=PC
                SectName=cmd[next][1]
                if SectName not in rsects:
                    rsects[SectName]=0
                    PC=0
                    labels[SectName]={}
                    ents[SectName]={}
                    rellist[SectName]=[]
                else:
                    PC=rsects[SectName]
                return(label,-1,cmd[next][1])
            if opcode=="ext":
                test_end(cmd[next])
                if label not in exts or label not in labels[SectName]:
                    exts[label]=[]
                    return('!'+label,0,cmd[next][1])
                return("",0,0)
            if opcode=="end":
                if label!="":
                    raise SE(0,"Illegal label")
                if Rel==True:
                    rsects[SectName]=PC
                if passno==1:
                    if Tpl:
                        tpls[tplName]["_"]=PC
                        Tpl=False
                    for name in rsects:
                        rsects[name]=0
                Rel=False
                return("$$$",-2,0)
        else:
            errLine = linum
            EP("Internal error: "+opcode+' '+str(cat)+str(linum))

def asm(assmtext=None):
    global SectName
    global rellist
    global exts
    global ents
    global abses
    global labels
    global rsects
    global PC
    global text
    global macdef
    global mname
    global Tpl
    global tpls
    global DsIns
    global tplName
    global generated
    global errLine

    if assmtext != None:
        text=assmtext

    output=[]
    generated=len(text)*[False]
    for passno in [1,2]:
        linum=0
        linind=0
        ready=False
        finished=False
        size=0
        label=""
        code=[]
        while True:
            if linind <= len(text)-1:
                s = text[linind]
                if not generated[linind]:
                    linum+=1
                linind+=1
            else:
                break

            try:
                #try:
                    (label, size, code) = asmline(s, linum, passno)
                    # if passno==1: print linum, ":", (label,size,code), s
                #except TypeError:
                    #if errorMsg != "":return
            except SE as e:
                if not macdef:
                        if e.ind>=1:
                            EP (s[0:e.ind]+s[e.ind:], term=False)
                            #EP (" "*(e.ind))
                        elif e.ind!=-1:
                            EP(s, term=False)
                        errLine = linum
                        EP("On line "+str(linum)+" ERROR: "+e.msg)
                        return
                else:
                    size=0
            except TypeError:
                errline = linum
                return

            if macdef and size!=-4 and size!=-3:     # accumulate macro definition
                if passno==1:
                    mbody += [s];
                continue
            if size == -1:      # sects
                ready=True
                continue
            elif size == -2:    # end
                if macdef:
                    EP("ERROR: 'end' encountered while processing macro definition")
                    quit(-1)
                finished=True
                break
            elif size == -3:    # macro
                if macdef:
                    EP("ERROR: macro definition inside macro")
                    quit(-1)
                macdef=True
                mbody=[]
                continue
            elif size == -4:    # mend
                if not macdef:
                    EP("ERROR: mend before macro")
                    quit(-1)
                macdef=False
                if passno==1:
                    macros[mname+"/"+str(marity)]=mbody
                    iset[mname]=(0,mi)
                continue

            elif size == -5:    # macro expansion
                text=text[0:linind]+code+text[linind:]
                generated = generated[0:linind]+len(code)*[True]+generated[linind:]
                continue
            elif size >= 0:     # deal with the label off a true instruction
                if Tpl and passno==1:
                    if not DsIns and size>0:
                        errLine = linum
                        EP("On line "+str(linum)+" ERROR: Only dc/ds allowed in templates")
                    DsIns=False
                if label!="" and passno==1:
                    if not ready:
                        errLine = linum
                        EP("On line "+str(linum)+" ERROR: 'asect' or 'rsect' expected")
                    addr=PC
                    if Tpl:
                        if label[0]==">":
                            errLine = linum
                            EP("On line "+str(linum)+" ERROR: exts in template not allowed")
                        if label in tpls[tplName]:
                            errLine = linum
                            EP("On line "+str(linum)+" ERROR: Label '"+label+"' already defined")
                        tpls[tplName][label]=PC
                    if label[0]==">":
                        label = label[1:]
                        ents[SectName][label]=PC
                    if label[0]=="!":
                        if label[1]==">":
                            errLine = linum
                            EP("On line "+str(linum)+" ERROR: label "+label[2:]+" both ext and entry")
                        label = label[1:]
                        addr=0
                    if not Tpl and label in labels[SectName]:
                        errLine = linum
                        EP("On line "+str(linum)+" ERROR: label "+label+" already defined")
                    if not Tpl:
                        labels[SectName][label]=addr
                    if not Rel:
                        abses[label]=PC

            if passno==2 and size>0 and not Tpl:
                if not ready:
                    errLine = linum
                    EP("On line "+str(linum)+" ERROR: 'asect' or 'rsect' expected")
                output+=[(linind,PC,code,SectName)]
            if passno==2 and Tpl:
                output+=[(linind,PC,[],"")]      # dummy output to get addresses in listing
            if size>0:
                    PC+=size
        if not finished:
            EP("ERROR: file ends before end of program")
    return output

def shex(k):
    m=k
    if m<0:
        m=256+m
    return format(m,"02x")[:2]

def pretty_print(obj1,src, prtOP=True):
    global asmver
    global lst_me
    def ismex(s):
        return s[-2:]=="#"+chr(1)
    obj=obj1

    #if not prtOP:
    #    offset=20
    #else:
    offset=15

    if prtOP == True:
        print("\nCdM-8 Assembler v"+asmver+" <<<"+filename+'.asm>>> '+time.strftime("%d/%m/%Y")+' '+time.strftime("%H:%M:%S")+'\n')
    else:
        # return code listing via function return (to cocoide)
        retlist=""
        lst_me = False

    me_skip=False

    if lst_me:              # remove macro expansion markers from the source lines
        src1=[]
        for s in src:
            slong=s
            while ismex(slong):
                slong = slong[:-2]
            src1 += [slong]
        src=src1

    ln=0
    for lnind in range(len(src)):
        if not generated[lnind] or lst_me:
            ln+=1

        s=src[lnind]

        if me_skip and ismex(s):
            continue
        else:
            me_skip=False

        if lnind+1 <= len(src)-1 and not ismex(s) and ismex(src[lnind+1]):    # we are inside macro expansion and must not list it
            last_line_ind=lnind+1
            while last_line_ind<=len(src)-1:
                if not ismex(src[last_line_ind]):
                    break
                else:
                    last_line_ind += 1
            last_line_ind -= 1
            last_line=last_line_ind+1
            me_skip=True

            if obj==[] or (obj !=[] and obj[0][0] > last_line):         # macro produced no code
                if prtOP == True:
                    print(' '*offset+' '+format(ln,'3d')+'  '+s)    # just print the mi
                else:
                    retlist += ' '*offset+' '+format(ln,'3d') +s+'\n'

                continue
            else:
                addr=obj[0][1]
                clist=obj[0][2]
                secname=obj[0][3]
                a1=addr+len(clist)
                k=1
                frag=False
                while k<= len(obj)-1 and obj[k][0] <= last_line:
                    if obj[k][1]== a1 and obj[k][3]==secname:
                        clist += obj[k][2]
                        a1 += len(obj[k][2])
                    else:
                        if prtOP == True:
                            print( ("<scattered>"+' '*offset)[0:offset]+' '+format(ln,'3d')+'  '+s )
                        else:
                            retlist += ("<scattered>"+' '*offset)[0:offset]+' '+format(ln,'3d')+'\n'
                        frag=True
                        break
                    k+=1

                if frag:
                    while k<=len(obj)-1 and obj[k][0] <= last_line:
                        k += 1
                    obj= obj[k:]
                    continue
                else:
                    obj= [(lnind+1,addr,clist,secname)]+obj[k:]



        if obj == [] or obj[0][0]!=lnind+1:
            if prtOP == True:
                print(' '*offset+' '+format(ln,'3d')+'  '+s)
            else:
                retlist += ' '*offset+' '+format(ln,'3d')+'  '+s+'\n'
        else:
            addr=obj[0][1]
            clist=obj[0][2]
            secname=obj[0][3]
            obj = obj[1:]
            tstr=s
            ln1=ln
            if secname=="":     # template
                if prtOP == True:
                    print( (format(addr,"02x")+': '+" "*offset)[0:offset]+' '+format(ln1,'3d')+'  '+s)
                else:
                    retlist += (format(addr,"02x")+': '+" "*offset)[0:offset]+' '+format(ln1,'3d')+'  '+s+'\n'
            while clist!=[]:
                pstr =format(addr,"02x")+': '+(' '.join(map(shex,clist[0:4])))
                ppr=(pstr+" "*offset)[0:offset]
                if (ln1>0):
                    sln=format(ln1,'3d')
                else:
                    sln=' '
                if prtOP == True:
                    print( ppr+' '+sln+"  "+tstr)
                else:
                    retlist += ppr+' '+sln+"  "+tstr+'\n'
                if len(clist)<=4:
                    break
                addr+=4
                tstr=' '
                ln1=0
                clist=clist[4:]

    if prtOP == True: # Not needed for cocide
        print( '\n'+"="*70)
        print( "\nSECTIONS:\nName\tSize\tRelocation offsets\n")

        for name in rsects:
            relsn= rellist[name]
            strg=''
            for r in relsn:
                strg += format(r,"02x")+' '
            print( name+"\t"+format(rsects[name],"02x")+'\t'+strg)

        print( "\nENTRIES:\nSection\t\tName/Offset\n")
        for name in ents:
            strg=name+'\t\t'
            if ents[name]=={}:
                strg+='<NONE>'
                print(strg)
                continue
            for nm in ents[name]:
                strg+=nm+':'+format(ents[name][nm],"02x")+'\t'
            print(strg)

        print("\nEXTERNALS:\nName\t\tUsed in\n")
        for name in exts:
            strg=name+'\t\t'
            for pair in exts[name]:
                (nm,oset)=pair
                strg+=nm+'+'+format(oset,"02x")+' '
            print(strg)
        print('\n'+70*'=')
    else:
        return retlist

def genoc(output, objbuff=None):
    def eladj(absegs):
        if len(absegs)<2:      #elimenate adjacent segments
            return absegs
        x,y,w=absegs[0], absegs[1], absegs[2:]
        if x[0]+len(x[1])==y[0]:    # adjacent: merge into one
            return eladj( [(x[0],x[1]+y[1])]+w )
        else:
            return [x]+eladj([y]+w)

    if objbuff==None:
        file=open(filename+".obj","w")
    else:
        objbuff=""
    sects={}
    absegs=[]
    for r in output:
        s=r[3]
        a=r[1]
        d=r[2]
        if s=="":
            continue
        if s!="$abs":
            if s not in sects:
                sects[s]=[]
            sects[s]+=d
        else:
            absegs+=[(a,d)]
    absegs=eladj(absegs)
    for pair in absegs:
        (a,d)=pair
        if objbuff==None:
            file.write("ABS  "+format(a,"02x")+": "+' '.join(map(shex,d))+'\n')
        else:
            objbuff += "ABS  "+format(a,"02x")+": "+' '.join(map(shex,d))+'\n'

    en=ents["$abs"]
    for e in en:
        if objbuff == None:
            file.write("NTRY "+e+' '+shex(en[e])+'\n')
        else:
            objbuff += "NTRY "+e+' '+shex(en[e])+'\n'

    for st in sects:
        if objbuff == None:
            file.write("NAME "+st+'\n')
            file.write("DATA "+' '.join(map(shex,sects[st]))+'\n')
            file.write("REL  "+' '.join(map(shex,rellist[st]))+'\n')
            en=ents[st]
            for e in en:
                file.write("NTRY "+e+' '+shex(en[e])+'\n')
        else:
            objbuff += "NAME "+st+'\n' + "DATA "
            objbuff +=' '.join(map(shex,sects[st]))+'\n'
            objbuff += "REL  "+' '.join(map(shex,rellist[st]))+'\n'
            en=ents[st]
            for e in en:
                objbuff += "NTRY "+e+' '+shex(en[e])+'\n'

    for extn in exts:
        strg = "XTRN "+extn+':'
        if exts[extn]==[]:
            EP("WARNING: ext '"+extn+"' declared, not used")
        for pair in exts[extn]:
            (s,offset)=pair
            strg+=' '+s+' '+shex(offset)
        if objbuff==None:
            file.write(strg+'\n')
        else:
            objbuff += strg+'\n'

    if objbuff == None:
        file.close()
    else:
        return objbuff
    return

def takemdefs(file,filename):
    global macros,iset
    def formerr():

        EP("Error in macro library file '"+filename+"' On line "+str(ln)+":\n"+l)
    state=0
    ln=0
    for l in file:
        l=l.rstrip()
        ln+=1
        if l=="" or l[0]=='#' :
            continue
        if state==1:
            if l[0]!='*':
                body+=[l]
            else:
                macros[name]=body
                iset[opcode]=(0,mi)
                state=0
        if state==0:
            if not l[0]=="*":
                formerr()
            if not l[1].isalpha():
                formerr()
            k=2
            found=False
            while (k<=len(l)-1):
                if not (l[k].isalnum() or l[k]=='_'):
                    found=True
                    break
                k+=1
            if not found:
                formerr()
            if l[k]!='/':
                formerr()
            opcode=l[1:k]
            k+=1
            if k>len(l) or not l[k].isdigit():
                formerr()
            name=l[1:k+1]
            body=[]
            state=1
    macros[name]=body
    iset[opcode]=(0,mi)



###################### M A C R O  FACILITIES
#
lst_me=False                    # flag: include macro expansions in listing

mcount=1                        # nonce for macros
mcalls=0                        # the number of macro expansions made so far
macdef=False
mname=""
marity=0
mvars={}
macros={}
mstack=[[],[],[],[],[],[]]
pars=[]                         # global list of parameters of the current macro

def EP(s, term=True):
    global retError, errorMsg
    #print("**", retError)
    if retError:
        errorMsg = s
        #if errorMsg !="":
        #    errorMsg = errorMsg + "\n"+s
    else:
        sys.stderr.write(s+'\n')
        if term:
            quit(-1)
    #print(errorMsg)#debug


def mxpand(s,pos,pno):          # substitute factual pars for $1...$<pno> in s escaping quoted strings
    global pars                 # substitute a nonce for ' and strings for ?<id> from mvars
    global mvars
    if s == "":
        return ""
    if len(s)==1 and s=="$":
           raise SE(pos,"Missing parameter number")
    x=s[0]

    if x=="$":
        if not s[1].isdigit:
            raise SE(pos,"Illegal parameter number")
        n=int(s[1])
        if n>pno:
            raise SE(pos,"Parameter number too high")
        k=len(pars[n-1])
        return pars[n-1]+mxpand(s[2:],pos+k-2,pno)

    if x=="?":
        return mxpand("!"+mxpand(s[1:],pos+1,pno), pos,pno)
    if x=="!":
        k=1
        w=""
        while k<=len(s)-1:
            if s[k].isalnum():
                w+=s[k]
                k+=1
            else:
                break
        if w=="":
            if len(s)==1:
                ofc=""
            else:
                ofc=s[1]
            raise SE(pos,"Illegal macro-variable '"+ofc+"'")
        if w not in mvars:
            raise SE(pos,"Unassigned macro-variable: "+w)
        return mvars[w]+mxpand(s[k:],pos+len(mvars[w]),pno)

    if x=="'":
        smcount=str(mcount)
        return smcount+mxpand(s[1:], pos+len(smcount),pno)
    if x=='"':
        k=1
        esc=False
        while k<=len(s)-1:
            if esc:
                esc=False
                continue
            if s[k]=="\\":
                esc=True
                continue
            v=s[k]
            if v=="\"":
                return s[:k+1]+mxpand(s[k+1:],pos+k+1,pno)
            k+=1
        return s
    else:
        return x+mxpand(s[1:], pos+1, pno)

def unptoken(t):
    if t[0]=="id":
        return t[1]
    if t[0]=="reg":
        return "r"+str(t[1])
    if t[0]=="num":
        return "0x"+format(t[1]+256,"02x")[-2:]
    if t[0]=="str":
        return '"'+(t[1].replace('\\','\\\\')).replace('"','\\"')+'"'
    raise SE(t[2],"Illegal item")

def commasep(tokens):
    k=0
    result=[]
    while (k<= len(tokens)-1):
        if tokens[k][0]=='end':
            return result
        else:
            if tokens[k][0]=="id" and k<=len(tokens)-3 and tokens[k+1][0]=='.' and tokens[k+2][0]=="id": # template field
                result += [unptoken(tokens[k])+"."+unptoken(tokens[k+2])]
                k=k+2
            else:
                result += [unptoken(tokens[k])]
        k=k+1
        if k<=len(tokens)-1 and tokens[k][0]!="," and tokens[k][0]!="end":
            raise SE(tokens[k][2],"Comma expected here")
        else:
            k=k+1
    return result

def ismstack(l,s):
    global mstack,mvarsm , errLine, errorMsg
    def diag(pos,msg,brief=False):
        if brief:
            errLine = l
            prefix="On line "+str(l)+" ERROR: "
        else:
            errLine = l
            prefix="On line "+str(l)+" ERROR: Macro \nExpanding:\n"+s+"\n"+(" "*pos)+"^\n"
        EP(prefix+msg)

    tokens=lexline(l,s)
    if errorMsg != "": return

    mstackind=0

    try:
        if len(tokens)>=1:
            if tokens[0][0]=="num":
                mstackind=tokens[0][1]
                if mstackind>len(mstack)-1:
                    if len(tokens)>1:
                        mstpos=tokens[1][2]
                    else:
                        mstpos=0
                    diag(mstpos,"Macro stack index too high: "+str(mstackind))
                tokens=tokens[1:]

        if len(tokens)==0:
            return False

        if len(tokens)==1:
            if tokens[0][0]=="id" and (tokens[0][1] in ["mpush", "mread", "mpop"]):
                diag(0,"Macro stack operation without argument")
            else:
                return False

        if len(tokens)>=3 and tokens[0][0]=="id" and tokens[1][0]==":":
            if tokens[2][0]=="id" and (tokens[2][1] in ["mpush","mread","mpop"]):
                diag(0,"Macro directives must not be labelled")

        if tokens[0][0]=="id" and tokens[0][1]=="mpush":
            frames=commasep(tokens[1:])
            mstack[mstackind]=frames[::-1]+mstack[mstackind]
            return True

        if tokens[0][0]=="id" and (tokens[0][1]=="mpop" or tokens[0][1]=="mread"):
            diagmes="Macro stack "+str(mstackind)+" empty or too few frames"
            k=1
            stoff=0
            brief=False
            while (k < len(tokens)):
                if tokens[k][0]=="id":
                    if len(mstack[mstackind])<stoff+1:
                            diag(tokens[k][2], diagmes, brief)
                    if tokens[0][1]=="mpop":
                        mvars[tokens[k][1]] = mstack[mstackind][0]
                        mstack[mstackind]=mstack[mstackind][1:]
                    else:
                        # Macro error here sometimes - fixed??
                        #print("**", k, len(tokens), mstackind, len(mstack), stoff, len(mstack[mstackind]))#debug
                        mvars[tokens[k][1]] = mstack[mstackind][stoff]
                        stoff+=1
                elif tokens[k][0]=="str":
                    brief=True
                    diagmes=tokens[k][1]
                else:
                    diag(tokens[k][2], "Macro variable or diagnostic message expected here")
                k += 1
                if k<=len(tokens)-1 and tokens[k][0]!=",":
                    diag(tokens[k][2],"Comma expected here")
                else:
                    k += 1
            return True


        if tokens[0][0]=="id" and tokens[0][1]=="unique":       # not a macro stack operation but we keep it here for simplicity
            k=1
            regfree=4*[True]
            regmvars=[]
            howmany=0
            while (k<= len(tokens)-1):
                howmany+=1
                if tokens[k][0]=="id":
                        regmvars+=[tokens[k][1]]
                elif tokens[k][0]=="reg":
                    if regfree[tokens[k][1]]:
                        regfree[tokens[k][1]]=False
                    else:
                        diag(tokens[k][2], "r"+str(tokens[k][1])+" occurs more than once")
                else:
                    diag(tokens[k][2], "Macro variable or register expected here")
                k=k+1
                if k<=len(tokens)-1 and tokens[k][0]!=",":
                    diag(tokens[k][2],"Comma expected here")
                else:
                    k=k+1
            if howmany>4:
                diag(tokens[0][2],"More than 4 operands specified")
            for v in regmvars:
                mvars[v]=""
            for v in regmvars:
                for k in [0,1,2,3]:
                    if regfree[k]:
                        regfree[k]=False
                        if mvars[v]!="":
                            diag(tokens[0][2],"macro var "+v+" occurs more than once")
                        else:
                            mvars[v]="r"+str(k)
                        break
            return True

    except:
        diag(tokens[k][1], "Macro error!", brief=True)

    return False

################################ E N D OF MACRO FACILITIES


def compile_asm (codetext=None, cdm8ver=4 ):
    """ Entry point when imported as a library
    """
    class Args():
        def __init__(self, cdm8ver):
            if cdm8ver == 4:
                self.v3 = False
            else:
                self.v3 = True
            self.dbg = False
            self.save = False


    global retError, errorMsg
    global text, argsPC, Rel, rellist, exts, ents, abses, labels, rsects
    global macros, labels, ents, tpls, Tpl, DsIns, tplName, generated, args, gotminus
    global mcount, mcalls, macdef, mname, marity, mvars, macros, mstack, pars
    global errLine, iset
    

    # (Re-)Init all the global vars
    
    retError=True
    errorMsg=""
    args = Args(cdm8ver)
    text = []
    PC=0
    Rel=False
    rellist = {}
    exts = {}
    ents = {}
    abses= {}
    labels = {}
    rsects = {}
    macros = {}
    labels["$abs"]={}
    ents["$abs"]={}
    tpls={}
    Tpl=False
    DsIns=False
    tplName=""
    generated=[]
    gotminus=False
    errline = None
    lst_me=False                    # flag: include macro expansions in listing
    # macro vars as well
    mcount=1                        # nonce for macros
    mcalls=0                        # the number of macro expansions made so far
    macdef=False
    mname=""
    marity=0
    mvars={}
    macros={}
    mstack=[[],[],[],[],[],[]]
    pars=[]

    for line in codetext:
            line=line.rstrip()
            text += [line.expandtabs()]

    mlb_name = 'standard.mlb'
    mlb_path = os.path.join(sys.path[0], mlb_name)

    skipfile=False
    try:
        mlibfile=open(mlb_path,'r')
    except IOError:
        skipfile=True

    if skipfile:
        skipfile=False
        try:
            mlibfile=open(mlb_name,'r')
        except IOError:
            skipfile=True
            EP("WARNING: no "+mlb_name+" found")
    if not skipfile:
        takemdefs(mlibfile,"standard.mlb")
        mlibfile.close()
    #print("compiling")

    #print(text)
    if errorMsg != "":
        #print("result", errorMsg) #debug
        return None, None, errorMsg

    result=asm()
    if errorMsg != "":
        #print("result", errorMsg) #debug
        return None, None, errorMsg
    objstr=""
    objstr=genoc(result, objstr)
    if errorMsg != "":
        #print("objstr", errorMsg)#debug
        return None, None, errorMsg
    codelist = pretty_print(result, text, False)
    return objstr, codelist, None




if __name__ == "__main__":
    global filename
    parser = argparse.ArgumentParser(description='CdM-8 Assembler v1.0')
    parser.add_argument('filename',type=str, help='source_file[.asm]')
    parser.add_argument('-l',dest='lst',action='store_const',const=True,default=False, help="produce program listing")
    parser.add_argument('-lx',dest='lstx',action='store_const',const=True,default=False, help="produce program listing showing macro expansion")
    parser.add_argument('-m', dest='mlibs', type=str, nargs='*', help='macro_library[.mlb]')
    parser.add_argument('-d', dest='dbg',action='store_const',const=True,default=False, help="include debug output")
    args = parser.parse_args()
    filename=args.filename
    if filename[-4:]==".asm":
        filename=filename[:-4]
    try:
        file=open(filename+'.asm','r')
    except IOError:
        EP(filename+".asm: file not found")
    for line in file:
        line=line.rstrip()
        text += [line.expandtabs()]

    # Test SE (Exception)
    # raise SE(2,"MIcks MEssage")


    mlb_name = 'standard.mlb'
    mlb_path = os.path.join(sys.path[0], mlb_name)

    skipfile=False
    try:
        mlibfile=open(mlb_path,'r')
    except IOError:
        skipfile=True

    if skipfile:
        skipfile=False
        try:
            mlibfile=open(mlb_name,'r')
        except IOError:
            skipfile=True
            EP("WARNING: no "+mlb_name+" found")

    if not skipfile:
        takemdefs(mlibfile,"standard.mlb")
        mlibfile.close()


    if args.mlibs != None :
        for x in args.mlibs:
            if x[-4:]==".mlb":
                x=x[:-4]
            try:
                mlibfile=open(x+".mlb",'r')
            except IOError:
                EP(x+".mlb not found")
            takemdefs(mlibfile,x)
            mlibfile.close()

    result=asm()
    genoc(result)

    if args.lstx:
        lst_me=True
    if args.lst or args.lstx:
        pretty_print(result,text)
    quit()
