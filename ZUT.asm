DFLT_AF: equ 0dd55h
DFLT_BC: equ 01234h
DFLT_DE: equ 05678h
DFLT_HL: equ 09abch
DFLT_IX: equ 0def0h
DFLT_IY: equ 0aabbh

	db	 0FEh		; Binary file ID
	dw	 Begin		; begin address
	dw	 End - 1	; end address
	dw	 Execute	; program execution address (for ,R option)
 
	org	0A000h

Begin:
 
; Program code entry point
Execute:
	di
	ld 	HL,hello
	CALL 	LPSTR
	call 	PrintLF

test00:
	CALL 	ClearTest
	NOP
	CALL 	StoreRegs
	LD 	HL,test00compare
	LD 	IX,0000
	CALL 	CompareRegs
	JP  	test01
test00compare:
	dw 	DFLT_AF	; AF
	dw	DFLT_BC	; BC
	dw	DFLT_DE	; DE
	dw	DFLT_HL	; HL
	dw	DFLT_IX	; IX
	dw	DFLT_IY	; IY

test01:
	CALL 	ClearTest
	LD 	BC,01234h
	CALL 	StoreRegs
	LD 	HL,test01compare
	LD 	IX,0001
	CALL 	CompareRegs
	JP  	test02
test01compare:
	dw 	DFLT_AF	; AF
	dw	01234h	; BC
	dw	DFLT_DE	; DE
	dw	DFLT_HL	; HL
	dw	DFLT_IX	; IX
	dw	DFLT_IY	; IY

test02:
finish:
	LD 	HL,finished
	CALL    LPSTR
	ei
	ret

; sends \r\n
PrintLF:
	PUSH   	AF
	PUSH   	BC
	LD 	C,13
	CALL 	LP
	LD 	C,10
	CALL 	LP
	POP 	BC
	POP 	AF
	RET

; word in BC
PrintWord:
	PUSH   	AF
	PUSH   	BC
	LD 	A,C
	LD 	C,B
	CALL 	PrintByte
	LD 	C,A
	CALL 	PrintByte
	POP 	BC
	POP 	AF
	RET

; byte in c
PrintByte:
	PUSH 	AF
	PUSH 	BC
	PUSH 	BC
; high nibble
	ld 	a,c
	srl     a
	srl     a
	srl     a
	srl     a
	and 	00fh
	cp 	00Ah
	jp 	M,PrintByteLess
	sub 	a,10
	add 	a,'a'
	jp      PrintBytePrint
PrintByteLess:
	add 	a,'0'
PrintBytePrint:
	ld 	c,a
  	call 	LP
	POP 	BC

; low nibble
	ld 	a,c
	and 	00fh
	cp 	00Ah
	jp 	M,PrintByteLess2
	sub 	a,10
	add 	a,'a'
	jp      PrintBytePrint2
PrintByteLess2:
	add 	a,'0'
PrintBytePrint2:
	ld 	c,a
  	call 	LP

	POP 	BC
	POP 	AF
	ret

; print a character in c to line printer
LP:	PUSH 	AF
;	LD      A,C
;	call    0a2h
; check if lpt ready (bit 1 == 0)
LPLOOP:	IN 	A,(090h)
	BIT	1,A
	JP	NZ,LPLOOP
; send char
	LD      A,C
	call    0a2h
	OUT	(091h),a
; strobe
	LD 	A,000h
	OUT	(090h),a
	LD 	A,001h
	OUT	(090h),a
	POP	AF
	RET

; print a '$' terminated string to printer
; address in HL
LPSTR:	PUSH 	AF
	PUSH 	HL
	PUSH 	BC
LPSTRLOOP:
	LD 	A,(HL)
	cp 	'$'
	JP 	Z,LPSTREND
	LD 	C,A
	CALL	LP
	INC	HL
	JP 	LPSTRLOOP
LPSTREND:
	POP 	BC
	POP 	HL
	POP 	AF
	RET

LD_HL_DE:
	PUSH 	DE
	POP 	HL
	RET

LD_DE_HL:
	PUSH 	HL
	POP 	DE
	REt

; check if any register has a different value than expected
; hl points to the values to compare to
CompareRegs:
	PUSH 	BC
	PUSH 	DE

	LD 	DE,storedregs
; need to compare 6 words
	LD 	C,6

CompareLoop:
; low byte
; get from left
	LD 	A,(HL)
	INC 	HL

; get from right
	PUSH 	HL
	CALL 	LD_HL_DE
	LD 	B,(HL)
	INC 	HL
	CALL 	LD_DE_HL
	POP 	HL

	CP 	B
	CALL 	NZ,mismatch1

; high byte
; get from left
	LD 	A,(HL)
	INC 	HL

; get from right
	PUSH 	HL
	CALL 	LD_HL_DE
	LD 	B,(HL)
	INC 	HL
	CALL 	LD_DE_HL
	POP 	HL

	CP 	B
	CALL 	NZ,mismatch2
	
	DEC 	C
	JP 	NZ,CompareLoop
FinishCompareLoop:
	POP 	DE
	POP 	BC
	RET

PrintTestNr:
; desecription
	PUSH 	HL
	LD 	HL,test_nr
	CALL 	LPSTR
	POP 	HL
; number itself
	PUSH 	BC
	PUSH 	IX
	POP 	BC
	CALL 	PrintWord
	POP 	BC
;
	CALL 	PrintLF
	RET

CompareLoopPrintWordNr:
	PUSH  	AF
	PUSH  	HL
	PUSH 	BC
; print description
	LD	HL, mismatch_nr
	CALL 	LPSTR

; calculate word nr
	LD 	A,006h
	SUB	C
; print number
	LD 	C,A
	CALL 	PrintByte
	CALL 	PrintLF
	POP 	BC
	POP 	HL
	POP 	AF
	RET
	
mismatch1:
; print test nr
	CALL 	PrintTestNr

	PUSH 	HL
	PUSH 	BC
	CALL 	CompareLoopPrintWordNr
	LD 	HL,lb_mismatch1
	CALL 	LPSTR
	LD 	C,A
	CALL 	PrintByte
	LD 	HL,lb_mismatch2
	CALL 	LPSTR
	LD 	C,B
	CALL 	PrintByte
	CALL 	PrintLF
	POP 	BC
	POP 	HL
	RET

mismatch2:
; print test nr
	CALL 	PrintTestNr

	PUSH 	HL
	PUSH 	BC
	CALL 	CompareLoopPrintWordNr
	LD 	HL,hb_mismatch1
	CALL 	LPSTR
	LD 	C,A
	CALL 	PrintByte
	LD 	HL,hb_mismatch2
	CALL 	LPSTR
	LD 	C,B
	CALL 	PrintByte
	CALL 	PrintLF
	POP 	BC
	POP 	HL
	RET

; make a copy of all registers
StoreRegs:
	ld 	(sr_sp),sp
	ld 	(sr_bc),bc
	ld 	(sr_de),de
	ld 	(sr_hl),hl
	ld 	(sr_ix),ix
	ld 	(sr_iy),iy
	ld 	(sr_sp),sp
	ld 	sp,temp_stack1
	push 	af
	pop 	de
	ld 	(sr_af),de
	ld 	sp,(sr_sp)
	ret

; setup for a new test
; clear registers
ClearTest:
	LD 	BC,DFLT_AF
	PUSH 	BC
	POP 	AF
	LD 	BC,DFLT_BC
	LD 	DE,DFLT_DE
	LD 	HL,DFLT_HL
	LD 	IX,DFLT_IX
	LD 	IY,DFLT_IY
;	EXX
;	LD 	BC,00000h
;	LD 	DE,00000h
;	LD 	HL,00000h
;	LD 	IX,00000h
;	LD 	IY,00000h
;	PUSH 	BC
;	POP 	AF
;	EXX
	ret

storedregs:
sr_af:	dw 	0
sr_bc:	dw	0
sr_de:	dw	0
sr_hl:	dw	0
sr_ix:	dw	0
sr_iy:	dw	0
sr_sp:	dw	0

temp_stack2:	dw 0
temp_stack1:	dw 0

test_data:	dw 012abh
test_pointer:	dw test_data

hello: 	db 	"Hello, this is a Z80 unittest.\r\n(C) 2020 by Folkert van Heusden\r\nmail@vanheusden.com\r\n$"
test_nr:	db 	"Test nr: $"
mismatch_nr:	db 	"Failing word: $"
hb_mismatch1:	db 	"High byte mismatch, got: $"
hb_mismatch2:	db 	", expected: $"
lb_mismatch1:	db 	"Low byte mismatch, got: $"
lb_mismatch2:	db 	", expected: $"
finished:	db 	"Finished.$"
	db 	0
End:
