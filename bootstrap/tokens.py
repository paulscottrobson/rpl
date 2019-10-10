# ******************************************************************************
# ******************************************************************************
#
#		Name : 		tokens.py
#		Purpose : 	RPL data table generation - can do RPL, Python, Assembler.
#		Author : 	Paul Robson (paul@robsons.org.uk)
#		Created : 	10th October 2019
#
# ******************************************************************************
# ******************************************************************************

import os,sys,re

# ******************************************************************************
#
#							CBM Pet tokens
#
# ******************************************************************************

class PETTokens(object):
	def __init__(self):
		self.tokens = {}
		tokens = """128:END;129:FOR;130:NEXT;131:DATA;132:INPUT#;133:INPUT;134:DIM;135:READ;
					136:LET;137:GOTO;138:RUN;139:IF;140:RESTORE;141:GOSUB;142:RETURN;143:REM;
					144:STOP;145:ON;146:WAIT;147:LOAD;148:SAVE;149:VERIFY;150:DEF;151:POKE;
					152:PRINT#;153:PRINT;154:CONT;155:LIST;156:CLR;157:CMD;158:SYS;159:OPEN;
					160:CLOSE;161:GET;162:NEW;163:TAB(;164:TO;165:FN;166:SPC(;167:THEN;
					168:NOT;169:STEP;170:+;171:−;172:*;173:/;174:^;175:AND;176:OR;177:>;
					178:=;179:<;180:SGN;181:INT;182:ABS;183:USR;184:FRE	;185:POS;186:SQR;
					187:RND;188:LOG;189:EXP;190:COS;191:SIN;192:TAN;193:ATN;194:PEEK;
					195:LEN;196:STR$;197:VAL;198:ASC;199:CHR$;200:LEFT$;201:RIGHT$;202:MID$"""
		tokens = tokens.upper().replace("\n","").replace("\t","").replace(" ","")
		for p in [x for x in tokens.split(";") if x != ""]:
			p = p.split(":")
			self.tokens[p[1].strip()] = int(p[0])
	#
	def get(self):
		return self.tokens

# ******************************************************************************
#
#						Source information production
#
# ******************************************************************************

class RPLDataTable(object):
	def __init__(self):
		self.tokens = PETTokens().get()										# tokens -> tok.id
		#
		#		These tokens compile directly to P-Code
		#
		self.compiledTokens = """ 
			+ - * / \\ str$ chr$ print > < = and or not # ; ^ % $ . new rnd get input stop
			int @ ! peek poke & return sys goto for next fn clr if then	
		""".upper().replace("\t"," ").replace("\n"," ")
		self.compiledTokens = [x for x in self.compiledTokens.split() if x != ""]
		#
		#		These are the tokens that are changed when mapped to P-Code and how they
		#		are changed. These magic values come from mapping.py
		#
		self.changeAfter = 187
		self.tokensAdjust = -39
		#
		#		These are how the tokens in general are changed.
		#
		self.charChange = -33
		self.tokenChange = -123
		#
		#		Now for each compiled token, we work out what its P-Code token is.
		#
		self.pCodes = {}
		usedCodes = {}
		for t in self.compiledTokens:
			petToken = self.toToken(t)										# this is the CBM token
			pCode = petToken 												# now work out P-Code
			if pCode >= self.changeAfter:									# is it one we shift.
				pCode += self.tokensAdjust																			
			pCode += self.charChange if (pCode<0x80) else self.tokenChange 	# shift it.
			assert pCode not in usedCodes and pCode >= 0 and pCode < 60
			usedCodes[pCode] = pCode
			self.pCodes[t] = pCode 											# save the token p-code
		#
		#		These tokens are only used for syntactic reasons and are not compiled as p-code.
		#
		self.syntaxTokens = ["(",")","[","]",":",","," ",'"',"'","END"]
		#
		#		All known tokens.
		#
		self.allTokens = self.syntaxTokens + self.compiledTokens 			
		self.scanSource()										
	#
	#		Scan all P-Code interpreter sources for addresses of commands.
	#
	def scanSource(self):
		self.commandVectors = {}
	#
	#		Convert a token word or character to an actual token.
	#
	def toToken(self,t):
		return self.tokens[t] if t in self.tokens else ord(t)
	#
	#		Export all tables for assembler.
	#
	def export(self,h,mode):
		self.mode = mode
		if mode == "P":
			h.write("class RPL:\n\tpass\n\n")
		self.exportPCode(h)
		self.exportTokens(h)
		self.exportModifiers(h)
		self.exportLegalSyntax(h)
	#
	#		Export all P-Codes
	#
	def exportPCode(self,h):
		keys = [x for x in self.pCodes.keys()]
		keys.sort(key = lambda x:self.pCodes[x])
		self.comment(h,"PCode constants after preprocessing")
		for t in keys:
			self.exportEquate(h,"PCODE_"+t,self.pCodes[t])
	#
	#		Export all tokens, including the syntactic ones.
	#
	def exportTokens(self,h):
		keys = [x for x in self.allTokens]
		keys.sort(key = lambda x:self.toToken(x))
		self.comment(h,"BASIC Program token constants")
		for t in keys:
			self.exportEquate(h,"PGM_"+t,self.toToken(t))
	#
	#		Export the modifiers that map the PETSCII/Tokens to P-Code
	#
	def exportModifiers(self,h):
		self.comment(h,"PETSCII or Token to P-Code conversion")
		self.exportEquate(h,"Adj_ChangeTokensAt",self.changeAfter)	# change tokens after this
		self.exportEquate(h,"Adj_TokensBy",self.tokensAdjust)		# by adding this
		self.exportEquate(h,"Adj_ChangeChars",self.charChange)		# change characters by this
		self.exportEquate(h,"Adj_ChangeTokens",self.tokenChange)	# change tokens by this.
	#
	#		Export the legal syntax table. This ranges from ASCII 32 to the highest 
	#		token (202). Bits from right to left indicate for each group of 8 charactes
	#		whether it is legal syntax or not.
	#
	def exportLegalSyntax(self,h):
		self.comment(h,"Bit flags for PETSCII/Tokens 32-208 indicating if valid syntax")
		checkFlags = [ 0 ] * 22 									# 22 bytes from 32-207
		for t in self.allTokens: 									# work through all legit tokens.
			n = self.toToken(t) 									# get the token/PETSCII 
			assert n >= 32 and n < 208								# check range.
			n = n - 32 												# remove initial offset
			checkFlags[n >> 3] |= (0x80 >> (n & 7))					# set the bit
		if self.mode == "P":
			h.write("RPL.SYNTAXCHECK = {0}\n".format(str(checkFlags)))
		elif self.mode == "R":
			h.write("RPL_SYNTAXCHECK: ({0})\n".format(",".join([str(x) for x in checkFlags])))
		else:
			h.write("SyntaxCheckTable:\n")
			h.write("\t.byte {0}\n".format(",".join(["${0:02x}".format(x) for x in checkFlags])))
	#
	#		Export a comment
	#
	def comment(self,h,c):
		if self.mode != 'R':
			h.write("{1}\n{1}\t\t{0}\n{1}\n".format(c,"#" if self.mode == "P" else ";"))	
	#
	#		Export an equate
	#
	def exportEquate(self,h,name,value):
		name = name.replace("!","PLING").replace("#","HASH").replace("$","DOLLAR").replace("%","PERCENT")
		name = name.replace("&","AMPERSAND").replace("-","MINUS").replace(".","DOT")
		name = name.replace(";","SEMICOLON").replace("@","AT").replace("+","PLUS").replace("*","ASTERISK")
		name = name.replace("/","SLASH").replace("^","HAT").replace(">","GREATER").replace("=","EQUAL")
		name = name.replace("<","LESS").replace("\\","BACKSLASH").replace(" ","SPACE")
		name = name.replace("(","LPAREN").replace(")","RPAREN").replace(":","COLON")
		name = name.replace("[","LSQPAREN").replace("]","RSQPAREN").replace(",","COMMA")
		name = name.replace('"',"DQUOTE").replace("'","SQUOTE").replace("","")
		name = name.replace("","").replace("","").replace("","")
		name = name.upper()
		assert re.match("^[A-Z0-9\\_]+$",name) is not None,"["+name+"]"
		if self.mode == 'P':
			h.write("RPL.{0} = {1}\n".format(name,value))
		elif self.mode == 'R':
			h.write(":{0}:{1}:\n".format(name,value))
		else:
			h.write("{0} = {1}\n".format(name,value))

# ******************************************************************************
#
#								Line Tokeniser
#
# ******************************************************************************

class Tokeniser(object):
	def __init__(self):
		self.tokens = PETTokens().get()
		self.longest = max([len(x) for x in self.tokens.keys()])			# longest token length
	#
	#		Tokenise the given line.
	#
	def tokenise(self,s):
		code = []															# result buffer
		s = s.upper().strip()												# preprocess
		while s != "":
			t = None
			for sz in range(self.longest,0,-1):								# look backwards from longest
				if t is None and s[:sz] in self.tokens:						# is there a match ?
					t = s[:sz]												# store that match
			#
			if t is not None:												# found a token
				code.append(self.tokens[t])									# append token code
				s = s[len(t):]												# strip it out
			#
			elif s.startswith('"'):											# found a quoted string
				p = s[1:].find('"')											# find end
				assert p >= 0,"Missing closing quote"
				for c in range(0,p+2):										# copy verbatim
					code.append(ord(s[c]))
				s = s[p+2:]
			else:															# otherwise, just character
				code.append(ord(s[0]))
				s = s[1:]
		return code
	#
	#		Test the tokeniser
	#
	def test(self,l):
		c = self.tokenise(l)
		print(l)
		print("\t"+str(c))

if __name__ == "__main__":
	dt = RPLDataTable()
	if len(sys.argv) == 3:
		h = open(sys.argv[2],"w")
		dt.export(h,sys.argv[1].upper())
		h.close()
		print("Created "+sys.argv[2])
	else:
		dt.export(sys.stdout,'P')
		tk = Tokeniser()
		tk.test('abcde')
		tk.test('"forks " "" ')	
		tk.test(" forks + #<>= \\ ")
