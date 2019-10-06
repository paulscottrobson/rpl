import sys
#
#		Experimental program to map tokens and characters so they can compile
#		directly.
#

#
#		Add to a counting record
#
def addToken(record,n,t):
	if n not in record:
		record[n] = []
	record[n].append(t)
#
#		Convert text to token.
#
def convert(tokenHash,t):
	if t in tokenHash:
		if tokenHash[t] == 163:
			print(t,"<<<")
		return tokenHash[t]

	return ord(t)
#
#		List of tokens in CBM Basic v2.0
#
src = "128:END;129:FOR;130:NEXT;131:DATA;132:INPUT#;133:INPUT;134:DIM;135:READ;136:LET;137:GOTO;138:RUN;139:IF;140:RESTORE;141:GOSUB;142:RETURN;143:REM;144:STOP;145:ON;146:WAIT;147:LOAD;148:SAVE;149:VERIFY;150:DEF;151:POKE;152:PRINT#;153:PRINT;154:CONT;155:LIST;156:CLR;157:CMD;158:SYS;159:OPEN;160:CLOSE;161:GET;162:NEW;163:TAB(;164:TO;165:FN;166:SPC(;167:THEN;168:NOT;169:STEP;170:+;171:−;172:*;173:/;174:^;175:AND;176:OR;177:>;178:=;179:<;180:SGN;181:INT;182:ABS;183:USR;184:FRE	;185:POS;186:SQR;187:RND;188:LOG;189:EXP;190:COS;191:SIN;192:TAN;193:ATN;194:PEEK;195:LEN;196:STR$;197:VAL;198:ASC;199:CHR$;200:LEFT$;201:RIGHT$;202:MID$"
#
#		Convert to a look up table.
#
v2tokens = {}
v2toTokens = {}
for p in src.lower().split(";"):
	p = p.strip().split(":")
	v2tokens[p[1]] = int(p[0])
	v2toTokens[int(p[0])] = p[1]
#
#		Direct compile tokens used in RPL.
#
tokens = """ 
	+ - * / \\
	str$ chr$ print
	> < =
	and or not
	# ; ^ % $ . new
	int 
	@ ! peek poke
	& return sys goto
	for next fn clr
	if then
	rnd get input stop
""".replace("\t"," ").replace("\n"," ")

tokens_syntax = ["(",")","[","]",":",","," ",'"',"'","end"]

tokens = [x for x in tokens.split() if x != ""]
#
#		Convert tokens to ASCII equivalents, or token codes. We now have
#		a list of directly compilable tokens.
#
startTokens = [convert(v2tokens,t) for t in tokens]
startTokens.sort()
#
#		Adjust one or more tokens by a fixed constant.
#
print(startTokens)
tokensToChange = [ 187,194,196,199 ]
#
#		Now try multiple shifts
#
for adjust in range(40,0):
	print(adjust)
	for cShift in range(-64,32):
		for tShift in range(-150,32):
			tokens = [x+adjust if x in tokensToChange else x for x in startTokens]
			#
			#		Count the number mapped to each.
			#
			counts = {}
			for tok in tokens:
				if tok < 128:
					addToken(counts,cShift+tok,tok)
				else:
					addToken(counts,tShift+tok,tok)
			#
			#		Calculate the range
			#				
			highToken = max(counts.keys())
			lowToken = min(counts.keys())
			tokenRange = highToken-lowToken+1
			#
			#		Count the number of collisions.
			#
			collisions = 0
			for n in counts.values():
				if len(n) > 1:
					collisions += (len(n) - 1)
			#
			#		Is it decent ?
			#
			if lowToken == 0 and tokenRange <= 65 and collisions <= 0:
					print(cShift,tShift,adjust)
					print("\t",collisions,tokenRange,highToken,lowToken)
					print("\t",[x for x in counts.values() if len(x) > 1])
	#				print("\t",[x for x in range(0,tokenRange) if x not in counts.keys()])

#sys.exit(0)

adjust = -39
cShift = -33
tShift = -123

mapping = {}

for t in startTokens:
	mt = t
	if mt in tokensToChange:
		mt += adjust
	mt = mt + (cShift if mt < 128 else tShift)
	if mt in mapping:
		print("Duplicate ",t,mt)
	mapping[mt] = [ mt,t,chr(t) if t < 128 else v2toTokens[t] ]
	#print(mt)
#
#	
#
for i in range(0,64):
	if i in mapping:
		print(i,mapping[i])
print(len(startTokens),len(mapping))
