RDSLT   equ #000C
WRSLT   equ #0014
ENASLT  equ #0024
JIFFY   equ #FC9E

SLTID equ %00000001 ; F000EEPP -> F=0, Pri=1, Ext=0

    OUTPUT "prog.bin"

    ORG #c000

; ENTRY POINTS
    JP USR0
    JP USR1
    JP USR2

; --------------------------
USR0 ; Return Software ID of cart
    DI
    CALL SETSLT

    CALL SETCMD
    LD A, #90
    LD (#5555), A
    ; 150ns+ delay
    NOP : NOP
    
    LD A, (#8000)
    LD B, A
    LD A, (#8001)
    LD C, A
    
    LD A, #F0
    LD (#4000), A
    
    LD A, B
    LD (#F7F8), A
    LD A, C
    LD (#F7F9), A

    JP CLRSLT

; -----------------------

USR1 ; Format banks
    DI
    CALL SETSLT

    ; banks: #00, #10, #20, #30, #40, #50, #60, #70
    ; AND we need CS12 enabled due to slot mapping, so all must be in #4000-#BFFF
    ; so we need to | #80 to those that don't fall into the region
    ; that makes it:
    ; #80, #90, #A0, #B0, #40, #50, #60, #70
    LD H, #40
    CALL _format_H_bank
    LD H, #50
    CALL _format_H_bank
    LD H, #60
    CALL _format_H_bank
    LD H, #70
    CALL _format_H_bank
    LD H, #80
    CALL _format_H_bank
    LD H, #90
    CALL _format_H_bank
    LD H, #A0
    CALL _format_H_bank
    LD H, #B0
    CALL _format_H_bank
    
    JP CLRSLT

_format_H_bank
    CALL SETCMD
    LD A, #80
    LD (#5555), A
    LD A, #AA
    LD (#5555), A
    LD A, #55
    LD (#AAAA), A
    LD L, 0
    LD (HL), #30

    ; 25ms+ delay needed
    EI
    LD HL, JIFFY
    LD A, (HL)
    ADD 5 ; 16.6ms x 5 = 83ms
_delaying
    CP (HL)
    JR NZ, _delaying

    RET

; -----------------------

USR2 ; Write bytes
    DI
    CALL SETSLT

    LD IX, _BYTEBUF
    LD HL, (_SADDR)
    ; We'll be looping #100 times
    LD B, 0
    LD C, #1

    ; Request byte write
_nextByte
    CALL SETCMD
    LD A, #A0
    LD (#5555), A
    LD A, (IX)
    LD (HL), A

    CALL BUSYWAIT

    ; Check if byte written right now has been written correctly
    LD D, (HL)
    CP D
    JP NZ, _failWriting

    INC HL
    INC IX
    DJNZ _nextByte
    DEC C
    JP NZ, _nextByte


    XOR A
    LD (#F7F8), A
    LD (#F7F9), A
    JP CLRSLT
_failWriting
    LD A, L
    LD (#F7F8), A
    LD A, H
    LD (#F7F9), A
    JP CLRSLT


; -----------------------

BUSYWAIT
    ; Delay 150us+
    DUP 80
    OR 0 ; 4Tstates
    EDUP
    RET

SETSLT
    LD A, SLTID
    LD HL, #4000
    CALL ENASLT
    LD A, SLTID
    LD HL, #8000
    JP ENASLT

SETCMD
    LD A, #AA
    LD (#5555), A
    LD A, #55
    LD (#AAAA), A
    RET

CLRSLT
    XOR A
    LD HL, #4000
    CALL ENASLT
    XOR A
    LD HL, #8000
    JP ENASLT


    ORG #C300
_SADDR  db 0, 0
    ORG #D000
_BYTEBUF db 0