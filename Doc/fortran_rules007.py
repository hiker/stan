#!/usr/bin/env python
__usage__ = """
Show Fortran 2000 syntax rules.

References:
  Information technology-Programming Languages-Fortran.
  Part 1: Base language.  ISO/IEC 1539 Working Draft J3/01-007R2.
  ftp://ftp.j3-fortran.org/j3/doc/standing/007/ascii

Usage:
    python %(progname)s [--depth=<int>] <pattern> [<pattern>]... [| less]
where
    --depth=-1  means unlimited but still finite depth
    pattern     is regular expression pattern
    --minishow  solve simple rules
    --yacc      output will be partly suitable for usage with yacc.py

    When used with less program, the output contains underlined and
    bolded words.

Examples:
    %(progname)s expr
R722   expr is [ expr defined-binary-op ] level-5-expr

    %(progname)s --depth=1 expr
R722   expr is [ expr defined-binary-op ] level-5-expr
R723   defined-binary-op is . letter [ letter ] ...  .
R717   level-5-expr is [ level-5-expr equiv-op ] equiv-operand

    %(progname)s '.*'   # shows all rules

    %(progname)s --depth=2 variable

    %(progname)s .*-stmt # show all statement rules
"""%({'progname':'./fortran_rules007.py'})

"""
Copyright 2001 Pearu Peterson all rights reserved,
Pearu Peterson <pearu@ioc.ee>          
Permission to use, modify, and distribute this software is given under the
terms of the LGPL.  See http://www.fsf.org

NO WARRANTY IS EXPRESSED OR IMPLIED.  USE AT YOUR OWN RISK.
$Revision: 3 $
$Date: 2003-06-30 12:50:24 +1000 (Mon, 30 Jun 2003) $
Pearu Peterson
"""

__version__ = "$Id: fortran_rules007.py 3 2003-06-30 02:50:24Z joh $"


import sys,re

if len(sys.argv)==1:
    print __usage__
    sys.exit()

plain = 0
if '--plain' in sys.argv:
    plain = 1

def bold(s):
    if plain: return s
    return ''.join(['%s%s'%(c,c) for c in '%s'%(s)])
def underline(s):
    if plain: return s
    return ''.join(['_%s'%(c) for c in '%s'%(s)])

class Rule:
    name_re = re.compile(r'(.*[-])+name\Z')
    def __init__(self,no,name,defs,rules,names):
        self.no = no
        self.name = name
        self.defs = ['\n\t\t'.join([l1.strip() for l1 in l.split('\n')]) for l in defs]
        self.rules = rules
        self.names = names
    def copy(self):
        return self.__class__(self.no,self.name,self.defs,self.rules,self.names)
    def __str__(self):
        return '%s%s\tis\n\t   %s\n'%(bold('R%-8s'%self.no),underline(self.name),'\n\tor '.join(self.defs))
    def showyacc(self,depth=1,ignore=[]):
        r = []
        for n in [self.name]+self.get_deps(depth):
            if n in ignore: continue
            ignore.append(n)
            r.append(self.get_rule(n).to_yacc())
        return '\n\n'.join(r)
    def yacc_map(self,s):
        from f2py.fortran.tokenizer import special_map
        for k in ['(/','/)','(',')','::',':',',','==','<=','>=','=>','/=',
                  '=','**','*','+','-','<','>','//','/','%']:
            s = s.replace(k,special_map[k])
        return s
    def to_yacc(self):
        defs = []
        for dl in self.defs:
            ds = []
            for d in dl.split('\n'):
                d = re.sub(r'[\w-]+-name','NAME',d)
                d = self.yacc_map(re.sub(r'-(?=\w)','_',d))
                m = re.match(r'(?P<n1>\w+)\s*[[]\s*(?P<op>\w*)\s+(?P<n2>\w+)\s*[]]\s*[.]{3,3}\s*\Z',d)
                if m:
                    if m.group('n1')==m.group('n2'):
                        if m.group('op'):
                            d = '%s_%slist'%(m.group('n1'),m.group('op'))
                        else:
                            d = '%s_seq'%(m.group('n1'))
                m = re.match(r'(?P<start>.*?)\s*[.]{3,3}(?P<end>.*)\Z',d)
                if m:
                    d = '%s_seq%s'%(m.group('start'),m.group('end'))
                m = re.match(r'(?P<start>.*\s*)[[]\s*(?P<name>\w+)\s*[]]',d)
                if m:
                    d = '%sopt_%s%s'%(m.group('start'),m.group('name'),d[m.end():])
                ds.append(d.strip())
            defs.append(' '.join(ds))
        return '%s : %s'%(self.name.replace('-','_'),'\n  | '.join(defs))
    def solve_deps(self,repository,depth):
        if not depth: return
        for nm in (' '.join(self.defs)).split():
            if nm not in repository and nm!=self.name:
                if nm not in self.names:
                    if nm[-5:]=='-name':
                        no = str(int(self.get_rule('name').no)+round(len(self.rules)/1000.,3))
                        self.names.append(nm)
                        self.rules.append(Rule(no,nm,['name'],self.rules,self.names))
                    else:
                        m = re.match(r'(.*-list|scalar-.*)\Z',nm)
                        if m:
                            nm = nm[:m.end()]
                if nm in self.names and nm not in repository:
                    repository.append(nm)
                    self.get_rule(nm).solve_deps(repository,depth-1)
    def get_deps(self,depth=1):
        deps = []
        self.solve_deps(deps,depth)
        return deps
    def get_rule(self,name):
        i = self.names.index(name)
        assert i>=0,`i`
        return self.rules[i]
    def show(self,depth=1,ignore=[]):
        r = []
        for n in [self.name]+self.get_deps(depth):
            if n in ignore: continue
            ignore.append(n)
            r.append(str(self.get_rule(n)))
        return '\n'.join(r)
    
    def minishow(self,depth=1,ignore=[]):
        return str(self.apply(depth))
    def apply(self,depth=1,):
        if not depth: return self
        deps = self.get_deps(depth)
        rule = self.copy()

        for d in deps:
            dr = self.get_rule(d).apply(depth-1)
            if len(dr.defs)!=1: continue
            d1 = dr.defs[0].strip()
            if re.match('.*(\n)',d1):
                continue
            defs = []
            for i in range(len(rule.defs)):
                if ' ' in d and ' ' in rule.defs[i]:
                    df = rule.defs[i]
                else:
                    df = re.sub(r'([^\w-]|\A| )'+d+r'([^\w-]|\Z| )',' '+d1+' ',rule.defs[i])
                if df not in defs:
                    defs.append(df)
            rule.defs = defs
        return rule
            
def main():
    global rules
    rule_re = re.compile(r'R(?P<no>\d+)\s+(?P<name>[\w-]+)\s+is\s+(?P<rest>(.*\n)+?)((?=R\d+)|\Z)')
    rule_lst = []
    names = []
    while 1:
        if not rules: break
        m = rule_re.match(rules)
        assert m,`rules[:80]`
        rule = rules[:m.end()]
        rules = rules[m.end():]
        name = m.group('name')
        no = m.group('no')
        rest = m.group('rest').replace('\t',' ').split(' or ')
        rule_lst.append(Rule(no,name,[l.strip() for l in rest],rule_lst,names))
        names.append(name)

    mth = 'show'
    depth = 0
    ignore =  []
    for pat in sys.argv[1:]:
        if pat[:8]=='--depth=':
            depth = int(pat[8:])
        elif pat=='--show': mth = pat[2:]
        elif pat=='--minishow': mth = pat[2:];depth=1
        elif pat=='--yacc': mth = 'showyacc'
        pat_re = re.compile(pat+r'\Z')
        for n in names:
            if pat_re.match(n):
                r = rule_lst[names.index(n)]
                out = getattr(r,mth)(depth,ignore)
                if out: print out

#fn = 'rules007.txt'
#rules=open(fn).read()
rules = """\
R001    letter is	A
	or B C D E F G H I J K L M N O P Q R S T U V W X Y Z
R002    digit is	0
	or 1 2 3 4 5 6 7 8 9
R101	xyz-list	is	xyz [ , xyz ] ...
R102	xyz-name	is	name
R103	scalar-xyz	is	xyz
R201	program	is	program-unit
	[ program-unit ] ...
R202	program-unit	is	main-program
	or	external-subprogram
	or	module
	or	block-data
R203	external-subprogram	is	function-subprogram
	or	subroutine-subprogram
R204	specification-part	is	[ use-stmt ] ...
	[ import-stmt ] ...
	[ implicit-part ]
	[ declaration-construct ] ...
R205	implicit-part	is	[ implicit-part-stmt ] ...
	implicit-stmt
R206	implicit-part-stmt	is	implicit-stmt
	or	parameter-stmt
	or	format-stmt
	or	entry-stmt
R207	declaration-construct	is	derived-type-def
	or	entry-stmt
	or	enum-alias-def
	or	format-stmt
	or	interface-block
	or	parameter-stmt
	or	procedure-declaration-stmt
	or	specification-stmt
	or	type-alias-stmt
	or	type-declaration-stmt
	or	stmt-function-stmt
R208	execution-part	is	executable-construct
	[ execution-part-construct ] ...
R209	execution-part-construct	is	executable-construct
	or	format-stmt
	or	entry-stmt
	or	data-stmt
R210	internal-subprogram-part	is	contains-stmt
	internal-subprogram
	[ internal-subprogram ] ...
R211	internal-subprogram	is	function-subprogram
	or	subroutine-subprogram
R212	module-subprogram-part	is	contains-stmt
	module-subprogram
	[ module-subprogram ] ...
R213	module-subprogram	is	function-subprogram
	or	subroutine-subprogram
R214	specification-stmt	is	access-stmt
	or	allocatable-stmt
	or	asynchronous-stmt
	or	bind-stmt
	or	common-stmt
	or	data-stmt
	or	dimension-stmt
	or	equivalence-stmt
	or	external-stmt
	or	intent-stmt
	or	intrinsic-stmt
	or	namelist-stmt
	or	optional-stmt
	or	pointer-stmt
	or	protected-stmt
	or	save-stmt
	or	target-stmt
	or	volatile-stmt
	or	value-stmt
R215	executable-construct	is	action-stmt
	or	associate-construct
	or	case-construct
	or	do-construct
	or	forall-construct
	or	if-construct
	or	select-type-construct
	or	where-construct
R216	action-stmt	is	allocate-stmt
	or	assignment-stmt
	or	backspace-stmt
	or	call-stmt
	or	close-stmt
	or	continue-stmt
	or	cycle-stmt
	or	deallocate-stmt
	or	endfile-stmt
	or	end-function-stmt
	or	end-program-stmt
	or	end-subroutine-stmt
	or	exit-stmt
	or	forall-stmt
	or	goto-stmt
	or	if-stmt
	or	inquire-stmt
	or	nullify-stmt
	or	open-stmt
	or	pointer-assignment-stmt
	or	print-stmt
	or	read-stmt
	or	return-stmt
	or	rewind-stmt
	or	stop-stmt
	or	wait-stmt
	or	where-stmt
	or	write-stmt
	or	arithmetic-if-stmt
	or	computed-goto-stmt
R217	keyword	is	name
R301	character	is	alphanumeric-character
	or	special-character
R302	alphanumeric-character	is	letter
	or	digit
	or	underscore
R303	underscore	is	_
R304	name	is	letter [ alphanumeric-character ] ...
R305	constant	is	literal-constant
	or	named-constant
R306	literal-constant	is	int-literal-constant
	or	real-literal-constant
	or	complex-literal-constant
	or	logical-literal-constant
	or	char-literal-constant
	or	boz-literal-constant
R307	named-constant	is	name
R308	int-constant	is	constant
R309	char-constant	is	constant
R310	intrinsic-operator	is	power-op
	or	mult-op
	or	add-op
	or	concat-op
	or	rel-op
	or	not-op
	or	and-op
	or	or-op
	or	equiv-op
R311	defined-operator	is	defined-unary-op
	or	defined-binary-op
	or	extended-intrinsic-op
R312	extended-intrinsic-op	is	intrinsic-operator
R313	label	is	digit [ digit [ digit [ digit [ digit ] ] ] ]
R401	type-param-value	is	scalar-int-expr
	or	*
	or	:
R402	signed-digit-string	is	[ sign ] digit-string
R403	digit-string	is	digit [ digit ] ...
R404	signed-int-literal-constant	is	[ sign ] int-literal-constant
R405	int-literal-constant	is	digit-string [ _ kind-param ]
R406	kind-param	is	digit-string
	or	scalar-int-constant-name
R407	sign	is	+
	or	-
R408	boz-literal-constant	is	binary-constant
	or	octal-constant
	or	hex-constant
R409	binary-constant	is	B ' digit [ digit ] ...  '
	or	B " digit [ digit ] ... "
R410	octal-constant	is	O ' digit [ digit ] ...  '
	or	O " digit [ digit ] ... "
R411	hex-constant	is	Z ' hex-digit [ hex-digit ] ...  '
	or	Z " hex-digit [ hex-digit ] ...  "
R412	hex-digit	is	digit
	or	A
	or	B
	or	C
	or	D
	or	E
	or	F
R413	signed-real-literal-constant	is	[ sign ] real-literal-constant
R414	real-literal-constant	is	significand [ exponent-letter exponent ] [ _ kind-param ]
	or	digit-string exponent-letter exponent [ _ kind-param ]
R415	significand	is	digit-string .  [ digit-string ]
	or	.  digit-string
R416	exponent-letter	is	E
	or	D
R417	exponent	is	signed-digit-string
R418	complex-literal-constant	is	( real-part , imag-part )
R419	real-part	is	signed-int-literal-constant
	or	signed-real-literal-constant
	or	named-constant
R420	imag-part	is	signed-int-literal-constant
	or	signed-real-literal-constant
	or	named-constant
R421	char-literal-constant	is	[ kind-param _ ] ' [ rep-char ] ...  '
	or	[ kind-param _ ] " [ rep-char ] ...  "
R422	logical-literal-constant	is	.TRUE.  [ _ kind-param ]
	or	.FALSE.  [ _ kind-param ]
R423	derived-type-def	is	derived-type-stmt
	[ type-param-def-stmt ] ...
	[ data-component-part ]
	[ type-bound-procedure-part ]
	end-type-stmt
R424	derived-type-stmt	is	TYPE [ [ , type-attr-spec-list ] :: ] type-name  [ ( type-param-name-list ) ]
R425	type-attr-spec	is	access-spec
	or	EXTENSIBLE
	or	EXTENDS ( [ access-spec :: ] parent-type-name  [ = initialization-expr ] )
	or	BIND ( C )
R426	type-param-def-stmt	is	INTEGER [ kind-selector ] [ [ , type-param-attr-spec ] :: ]  type-param-name-list
R427	type-param-attr-spec	is	KIND
	or	NONKIND
R428	data-component-part	is	[ private-sequence-stmt ] ...
	[ component-def-stmt ] ...
R429	private-sequence-stmt	is	PRIVATE
	or	SEQUENCE
R430	component-def-stmt	is	data-component-def-stmt
	or	proc-component-def-stmt
R431	data-component-def-stmt	is	declaration-type-spec [ [ , component-attr-spec-list ] :: ]  component-decl-list
R432	component-attr-spec	is	POINTER
	or	DIMENSION ( component-array-spec )
	or	ALLOCATABLE
	or	access-spec
R433	component-decl	is	component-name [ ( component-array-spec ) ]    [ * char-length ] [ component-initialization ]
R434	component-array-spec	is	explicit-shape-spec-list
	or	deferred-shape-spec-list
R435	component-initialization	is	=  initialization-expr
	or	=> NULL ( )
R436	proc-component-def-stmt	is	PROCEDURE ( [ proc-interface ] ) ,  proc-component-attr-spec-list  ::  proc-decl-list
R437	proc-component-attr-spec	is	POINTER
	or	PASS_OBJ
	or	access-spec
R438	type-bound-procedure-part	is	contains-stmt
	[ binding-private-stmt ]
	proc-binding-stmt
	[ proc-binding-stmt ] ...
R439	binding-private-stmt	is	PRIVATE
R440	proc-binding-stmt	is	specific-binding
	or	generic-binding
	or	final-binding
R441	specific-binding	is	PROCEDURE [ ( abstract-interface-name ) ]   [ [ , binding-attr-list ] :: ] binding-name  [ => binding ]
R442	generic-binding	is	GENERIC [ ( abstract-interface-name ) ]  [ , binding-attr-list ] :: generic-spec => binding-list
R443	final-binding	is	FINAL [ :: ] final-subroutine-name-list
R444	binding-attr	is	PASS_OBJ
	or	NON_OVERRIDABLE
	or	access-spec
R445	binding	is	procedure-name
	or	NULL ( )
R446	end-type-stmt	is	END TYPE [ type-name ]
R447	derived-type-spec	is	type-name [ ( type-param-spec-list ) ]
	or	type-alias-name
R448	type-param-spec	is	[ keyword = ] type-param-value
R449	structure-constructor 	is	derived-type-spec ( [ component-spec-list ] )
R450	component-spec	is	[ keyword = ] expr
R451	type-alias-stmt	is	TYPEALIAS :: type-alias-list
R452	type-alias	is	type-alias-name => declaration-type-spec
R453	enum-alias-def	is	enum-def-stmt
	enumerator-def-stmt
	[ enumerator-def-stmt ] ...
	end-enum-stmt
R454	enum-def-stmt	is	ENUM , BIND ( C ) :: type-alias-name
	or	ENUM [ kind-selector ] [ :: ] type-alias-name
R455	enumerator-def-stmt	is	ENUMERATOR [ :: ] enumerator-list
R456	enumerator	is	named-constant [ = scalar-int-initialization-expr ]
R457	end-enum-stmt	is	END ENUM [ type-alias-name ]
R458	array-constructor	is	(/ ac-spec /)
	or	left-square-bracket ac-spec right-square-bracket
R459	ac-spec	is	type-spec ::
	or	[ type-spec :: ] ac-value-list
R460	left-square-bracket	is	\[
R461	right-square-bracket	is	\]
R462	ac-value	is	expr
	or	ac-implied-do
R463	ac-implied-do	is	( ac-value-list , ac-implied-do-control )
R464	ac-implied-do-control	is	ac-do-variable = scalar-int-expr , scalar-int-expr  [ , scalar-int-expr ]
R465	ac-do-variable	is	scalar-int-variable
R501	type-declaration-stmt	is	declaration-type-spec [ [ , attr-spec ] ...  :: ] entity-decl-list
R502	declaration-type-spec	is	type-spec
	or	CLASS ( derived-type-spec )
	or	CLASS ( * )
R503	type-spec	is	INTEGER [ kind-selector ]
	or	REAL [ kind-selector ]
	or	DOUBLE PRECISION
	or	COMPLEX [ kind-selector ]
	or	CHARACTER [ char-selector ]
	or	LOGICAL [ kind-selector ]
	or	TYPE ( derived-type-spec )
	or	TYPE ( type-alias-name )
R504	attr-spec	is	access-spec
	or	ALLOCATABLE
	or	ASYNCHRONOUS
	or	DIMENSION ( array-spec )
	or	EXTERNAL
	or	INTENT ( intent-spec )
	or	INTRINSIC
	or	language-binding-spec
	or	OPTIONAL
	or	PARAMETER
	or	POINTER
	or	PROTECTED
	or	SAVE
	or	TARGET
	or	VALUE
	or	VOLATILE
R505	entity-decl	is	object-name [ ( array-spec ) ]  [ * char-length ] [ initialization ]
	or	function-name [ * char-length ]
R506	object-name	is	name
R507	initialization	is	= initialization-expr
	or	=> NULL ( )
R508	kind-selector	is	( [ KIND = ] scalar-int-initialization-expr )
R509	char-selector	is	length-selector
	or	( LEN = type-param-value ,  KIND = scalar-int-initialization-expr )
	or	( type-param-value ,  [ KIND = ] scalar-int-initialization-expr )
	or	( KIND = scalar-int-initialization-expr  [ , LEN = type-param-value ] )
R510	length-selector	is	( [ LEN = ] type-param-value )
	or	* char-length [ , ]
R511	char-length	is	( type-param-value )
	or	scalar-int-literal-constant
R512	access-spec	is	PUBLIC
	or	PRIVATE
R513	language-binding-spec	is	BIND ( C [ , NAME = scalar-char-initialization-expr ] )
R514	array-spec	is	explicit-shape-spec-list
	or	assumed-shape-spec-list
	or	deferred-shape-spec-list
	or	assumed-size-spec
R515	explicit-shape-spec	is	[ lower-bound : ] upper-bound
R516	lower-bound	is	specification-expr
R517	upper-bound	is	specification-expr
R518	assumed-shape-spec	is	[ lower-bound ] :
R519	deferred-shape-spec	is	:
R520	assumed-size-spec	is	[ explicit-shape-spec-list , ] [ lower-bound : ] *
R521	intent-spec	is	IN
	or	OUT
	or	INOUT
R522	access-stmt	is	access-spec [ [ :: ] access-id-list ]
R523	access-id	is	use-name
	or	generic-spec
R524	allocatable-stmt	is	ALLOCATABLE [ :: ]   object-name [ ( deferred-shape-spec-list ) ]  [ , object-name [ ( deferred-shape-spec-list ) ] ] ...
R525	asynchronous-stmt	is	ASYNCHRONOUS [ :: ] object-name-list
R526	bind-stmt	is	language-binding-spec [ :: ] bind-entity-list
R527	bind-entity	is	entity-name
	or	/ common-block-name /
R528	data-stmt	is	DATA data-stmt-set [ [ , ] data-stmt-set ] ...
R529	data-stmt-set	is	data-stmt-object-list / data-stmt-value-list /
R530	data-stmt-object	is	variable
	or	data-implied-do
R531	data-implied-do	is	( data-i-do-object-list , data-i-do-variable =  scalar-int-expr , scalar-int-expr [ , scalar-int-expr ] )
R532	data-i-do-object	is	array-element
	or	scalar-structure-component
	or	data-implied-do
R533	data-i-do-variable	is	scalar-int-variable
R534	data-stmt-value	is	[ data-stmt-repeat * ] data-stmt-constant
R535	data-stmt-repeat	is	scalar-int-constant
	or	scalar-int-constant-subobject
R536	data-stmt-constant	is	scalar-constant
	or	scalar-constant-subobject
	or	signed-int-literal-constant
	or	signed-real-literal-constant
	or	NULL ( )
	or	structure-constructor
R537	int-constant-subobject	is	constant-subobject
R538	constant-subobject	is	designator
R539	dimension-stmt	is	DIMENSION [ :: ] array-name ( array-spec )  [ , array-name ( array-spec ) ] ...
R540	intent-stmt	is	INTENT ( intent-spec ) [ :: ] dummy-arg-name-list
R541	optional-stmt	is	OPTIONAL [ :: ] dummy-arg-name-list
R542	parameter-stmt	is	PARAMETER ( named-constant-def-list )
R543	named-constant-def	is	named-constant = initialization-expr
R544	pointer-stmt	is	POINTER [ :: ] pointer-decl-list
R545	pointer-decl	is	object-name  [ ( deferred-shape-spec-list ) ]
	or	proc-entity-name
R546	protected-stmt	is	PROTECTED [ :: ] entity-name-list
R547	save-stmt	is	SAVE [ [ :: ] saved-entity-list ]
R548	saved-entity	is	object-name
	or	proc-pointer-name
	or	/ common-block-name /
R549	proc-pointer-name	is	name
R550	target-stmt	is	TARGET [ :: ] object-name [ ( array-spec ) ]  [ , object-name [ ( array-spec ) ] ] ...
R551	value-stmt	is	VALUE [ :: ] dummy-arg-name-list
R552	volatile-stmt	is	VOLATILE [ :: ] object-name-list
R553	implicit-stmt	is	IMPLICIT implicit-spec-list
	or	IMPLICIT NONE
R554	implicit-spec	is	declaration-type-spec ( letter-spec-list )
R555	letter-spec	is	letter [ - letter ]
R556	namelist-stmt	is	NAMELIST    / namelist-group-name / namelist-group-object-list  [ [ , ] / namelist-group-name / namelist-group-object-list ] ...
R557	namelist-group-object	is	variable-name
R558	equivalence-stmt	is	EQUIVALENCE equivalence-set-list
R559	equivalence-set	is	( equivalence-object , equivalence-object-list )
R560	equivalence-object	is	variable-name
	or	array-element
	or	substring
R561	common-stmt	is	COMMON   [ / [ common-block-name ] / ] common-block-object-list  [ [ , ] / [ common-block-name ] / common-block-object-list ] ...
R562	common-block-object	is	variable-name [ ( explicit-shape-spec-list ) ]
	or	proc-pointer-name
R601	variable	is	designator
R602	variable-name	is	name
R603	designator	is	object-name
	or	array-element
	or	array-section
	or	structure-component
	or	substring
R604	logical-variable	is	variable
R605	default-logical-variable	is	variable
R606	char-variable	is	variable
R607	default-char-variable	is	variable
R608	int-variable	is	variable
R609	substring	is	parent-string ( substring-range )
R610	parent-string	is	scalar-variable-name
	or	array-element
	or	scalar-structure-component
	or	scalar-constant
R611	substring-range	is	[ scalar-int-expr ] : [ scalar-int-expr ]
R612	data-ref	is	part-ref [ % part-ref ] ...
R613	part-ref	is	part-name [ ( section-subscript-list ) ]
R614	structure-component	is	data-ref
R615	type-param-inquiry	is	designator % type-param-name
R616	array-element	is	data-ref
R617	array-section	is	data-ref [ ( substring-range ) ]
R618	subscript	is	scalar-int-expr
R619	section-subscript	is	subscript
	or	subscript-triplet
	or	vector-subscript
R620	subscript-triplet	is	[ subscript ] : [ subscript ] [ : stride ]
R621	stride	is	scalar-int-expr
R622	vector-subscript	is	int-expr
R623	allocate-stmt	is	ALLOCATE ( [ type-spec :: ] allocation-list  [ , alloc-opt-list ] )
R624	alloc-opt	is	STAT = stat-variable
	or	ERRMSG = errmsg-variable
	or	SOURCE = source-variable
R625	stat-variable	is	scalar-int-variable
R626	errmsg-variable	is	scalar-default-char-variable
R627	allocation	is	allocate-object [ ( allocate-shape-spec-list ) ]
R628	allocate-object	is	variable-name
	or	structure-component
R629	allocate-shape-spec	is	[ allocate-lower-bound : ] allocate-upper-bound
R630	allocate-lower-bound	is	scalar-int-expr
R631	allocate-upper-bound	is	scalar-int-expr
R632	source-variable	is	variable
R633	nullify-stmt	is	NULLIFY ( pointer-object-list )
R634	pointer-object	is	variable-name
	or	structure-component
	or	proc-pointer-name
R635	deallocate-stmt	is	DEALLOCATE ( allocate-object-list [ , dealloc-opt-list ] )
R636	dealloc-opt	is	STAT = stat-variable
	or	ERRMSG = errmsg-variable
R701	primary	is	constant
	or	designator
	or	array-constructor
	or	structure-constructor
	or	function-reference
	or	type-param-inquiry
	or	type-param-name
	or	( expr )
R702	level-1-expr	is	[ defined-unary-op ] primary
R703	defined-unary-op	is	. letter [ letter ] ...  .
R704	mult-operand	is	level-1-expr [ power-op mult-operand ]
R705	add-operand	is	[ add-operand mult-op ] mult-operand
R706	level-2-expr	is	[ [ level-2-expr ] add-op ] add-operand
R707	power-op	is	**
R708	mult-op	is	*
	or	/
R709	add-op	is	+
	or	-
R710	level-3-expr	is	[ level-3-expr concat-op ] level-2-expr
R711	concat-op	is	//
R712	level-4-expr	is	[ level-3-expr rel-op ] level-3-expr
R713	rel-op	is	.EQ.
	or	.NE.
	or	.LT.
	or	.LE.
	or	.GT.
	or	.GE.
	or	==
	or	/=
	or	<
	or	<=
	or	>
	or	>=
R714	and-operand	is	[ not-op ] level-4-expr
R715	or-operand	is	[ or-operand and-op ] and-operand
R716	equiv-operand	is	[ equiv-operand or-op ] or-operand
R717	level-5-expr	is	[ level-5-expr equiv-op ] equiv-operand
R718	not-op	is	.NOT.
R719	and-op	is	.AND.
R720	or-op	is	.OR.
R721	equiv-op	is	.EQV.
	or	.NEQV.
R722	expr	is	[ expr defined-binary-op ] level-5-expr
R723	defined-binary-op	is	. letter [ letter ] ...  .
R724	logical-expr	is	expr
R725	char-expr	is	expr
R726	default-char-expr	is	expr
R727	int-expr	is	expr
R728	numeric-expr	is	expr
R729	specification-expr	is	scalar-int-expr
R730	initialization-expr	is	expr
R731	char-initialization-expr	is	char-expr
R732	int-initialization-expr	is	int-expr
R733	logical-initialization-expr	is	logical-expr
R734	assignment-stmt	is	variable = expr
R735	pointer-assignment-stmt	is	data-pointer-object [ ( bounds-spec-list ) ] => data-target
	or	data-pointer-object ( bounds-remapping-list ) => data-target
	or	proc-pointer-object => proc-target
R736	data-pointer-object	is	variable-name
	or	variable % data-pointer-component-name
R737	bounds-spec	is	lower-bound :
R738	bounds-remapping	is	lower-bound : upper-bound
R739	data-target	is	variable
	or	expr
R740	proc-pointer-object	is	proc-pointer-name
	or	variable % procedure-component-name
R741	proc-target	is	expr
	or	procedure-name
R742	where-stmt	is	WHERE ( mask-expr ) where-assignment-stmt
R743	where-construct	is	where-construct-stmt
	[ where-body-construct ] ...
	[ masked-elsewhere-stmt
		[ where-body-construct ] ... ] ...
	[ elsewhere-stmt
		[ where-body-construct ] ... ]
	end-where-stmt
R744	where-construct-stmt	is	[ where-construct-name : ] WHERE ( mask-expr )
R745	where-body-construct	is	where-assignment-stmt
	or	where-stmt
	or	where-construct
R746	where-assignment-stmt	is	assignment-stmt
R747	mask-expr	is	logical-expr
R748	masked-elsewhere-stmt	is	ELSEWHERE ( mask-expr ) [ where-construct-name ]
R749	elsewhere-stmt	is	ELSEWHERE [ where-construct-name ]
R750	end-where-stmt	is	END WHERE [ where-construct-name ]
R751	forall-construct	is	forall-construct-stmt
	[ forall-body-construct ] ...
	end-forall-stmt
R752	forall-construct-stmt	is	[ forall-construct-name : ] FORALL forall-header
R753	forall-header	is	( forall-triplet-spec-list [ , scalar-mask-expr ] )
R754	forall-triplet-spec	is	index-name = subscript : subscript [ : stride ]
R755	forall-body-construct	is	forall-assignment-stmt
	or	where-stmt
	or	where-construct
	or	forall-construct
	or	forall-stmt
R756	forall-assignment-stmt	is	assignment-stmt
	or	pointer-assignment-stmt
R757	end-forall-stmt	is	END FORALL [ forall-construct-name ]
R758	forall-stmt	is	FORALL forall-header forall-assignment-stmt
R801	block	is	[ execution-part-construct ] ...
R802	if-construct	is	if-then-stmt
	block
	[ else-if-stmt
		block ] ...
	[ else-stmt
		block ]
	end-if-stmt
R803	if-then-stmt	is	[ if-construct-name : ] IF ( scalar-logical-expr ) THEN
R804	else-if-stmt	is	ELSE IF ( scalar-logical-expr ) THEN [ if-construct-name ]
R805	else-stmt	is	ELSE [ if-construct-name ]
R806	end-if-stmt	is	END IF [ if-construct-name ]
R807	if-stmt	is	IF ( scalar-logical-expr ) action-stmt
R808	case-construct	is	select-case-stmt
	[ case-stmt
		block ] ...
	end-select-stmt
R809	select-case-stmt	is	[ case-construct-name : ] SELECT CASE ( case-expr )
R810	case-stmt	is	CASE case-selector [ case-construct-name ]
R811	end-select-stmt	is	END SELECT [ case-construct-name ]
R812	case-expr	is	scalar-int-expr
	or	scalar-char-expr
	or	scalar-logical-expr
R813	case-selector	is	( case-value-range-list )
	or	DEFAULT
R814	case-value-range	is	case-value
	or	case-value :
	or	: case-value
	or	case-value : case-value
R815	case-value	is	scalar-int-initialization-expr
	or	scalar-char-initialization-expr
	or	scalar-logical-initialization-expr
R816	select-type-construct	is	select-type-stmt
	[ type-guard-stmt
		block ] ...
	end-select-type-stmt
R817	select-type-stmt	is	[ select-construct-name : ] SELECT TYPE  ( [ associate-name => ] selector )
R818	selector	is	expr
	or	variable
R819	type-guard-stmt	is	TYPE IS ( extensible-type-name ) [ select-construct-name ]
	or	TYPE IN ( extensible-type-name ) [ select-construct-name ]
	or	TYPE DEFAULT [ select-construct-name ]
R820	end-select-type-stmt	is	END SELECT [ select-construct-name ]
R821	associate-construct	is	associate-stmt
	block
	end-associate-stmt
R822	associate-stmt	is	[ associate-construct-name : ] ASSOCIATE ( association-list )
R823	association	is	associate-name => selector
R824	end-associate-stmt	is	END ASSOCIATE [ associate-construct-name ]
R825	do-construct	is	block-do-construct
	or	nonblock-do-construct
R826	block-do-construct	is	do-stmt
	do-block
	end-do
R827	do-stmt	is	label-do-stmt
	or	nonlabel-do-stmt
R828	label-do-stmt	is	[ do-construct-name : ] DO label [ loop-control ]
R829	nonlabel-do-stmt	is	[ do-construct-name : ] DO [ loop-control ]
R830	loop-control	is	[ , ] do-variable = scalar-int-expr , scalar-int-expr  [ , scalar-int-expr ]
	or	[ , ] WHILE ( scalar-logical-expr )
R831	do-variable	is	scalar-int-variable
R832	do-block	is	block
R833	end-do	is	end-do-stmt
	or	continue-stmt
R834	end-do-stmt	is	END DO [ do-construct-name ]
R835	nonblock-do-construct	is	action-term-do-construct
	or	outer-shared-do-construct
R836	action-term-do-construct	is	label-do-stmt
	do-body
	do-term-action-stmt
R837	do-body	is	[ execution-part-construct ] ...
R838	do-term-action-stmt	is	action-stmt
R839	outer-shared-do-construct	is	label-do-stmt
	do-body
	shared-term-do-construct
R840	shared-term-do-construct	is	outer-shared-do-construct
	or	inner-shared-do-construct
R841	inner-shared-do-construct	is	label-do-stmt
	do-body
	do-term-shared-stmt
R842	do-term-shared-stmt	is	action-stmt
R843	cycle-stmt	is	CYCLE [ do-construct-name ]
R844	exit-stmt	is	EXIT [ do-construct-name ]
R845	goto-stmt	is	GO TO label
R846	computed-goto-stmt	is	GO TO ( label-list ) [ , ] scalar-int-expr
R847	arithmetic-if-stmt	is	IF ( scalar-numeric-expr ) label , label , label
R848	continue-stmt	is	CONTINUE
R849	stop-stmt	is	STOP [ stop-code ]
R850	stop-code	is	scalar-char-constant
	or	digit [ digit [ digit [ digit [ digit ] ] ] ]
R901	io-unit	is	file-unit-number
	or	*
	or	internal-file-variable
R902	file-unit-number	is	scalar-int-expr
R903	internal-file-variable	is	default-char-variable
R904	open-stmt	is	OPEN ( connect-spec-list )
R905	connect-spec	is	[ UNIT = ] file-unit-number
	or	ACCESS = scalar-default-char-expr
	or	ACTION = scalar-default-char-expr
	or	ASYNCHRONOUS = scalar-default-char-expr
	or	BLANK = scalar-default-char-expr
	or	DECIMAL = scalar-default-char-expr
	or	DELIM = scalar-default-char-expr
	or	ERR = label
	or	FILE = file-name-expr
	or	FORM = scalar-default-char-expr
	or	IOMSG = iomsg-variable
	or	IOSTAT = scalar-int-variable
	or	PAD = scalar-default-char-expr
	or	POSITION = scalar-default-char-expr
	or	RECL = scalar-int-expr
	or	ROUND = scalar-default-char-expr
	or	SIGN = scalar-default-char-expr
	or	STATUS = scalar-default-char-expr
R906	file-name-expr	is	scalar-default-char-expr
R907	iomsg-variable	is	scalar-default-char-variable
R908	close-stmt	is	CLOSE ( close-spec-list )
R909	close-spec	is	[ UNIT = ] file-unit-number
	or	IOSTAT = scalar-int-variable
	or	IOMSG = iomsg-variable
	or	ERR = label
	or	STATUS = scalar-default-char-expr
R910	read-stmt	is	READ ( io-control-spec-list ) [ input-item-list ]
	or	READ format [ , input-item-list ]
R911	write-stmt	is	WRITE ( io-control-spec-list ) [ output-item-list ]
R912	print-stmt	is	PRINT format [ , output-item-list ]
R913	io-control-spec	is	[ UNIT = ] io-unit
	or	[ FMT = ] format
	or	[ NML = ] namelist-group-name
	or	ADVANCE = scalar-default-char-expr
	or	ASYNCHRONOUS = scalar-char-initialization-expr
	or	BLANK = scalar-default-char-expr
	or	DECIMAL = scalar-default-char-expr
	or	DELIM = scalar-default-char-expr
	or	END = label
	or	EOR = label
	or	ERR = label
	or	ID = scalar-int-variable
	or	IOMSG = iomsg-variable
	or	IOSTAT = scalar-int-variable
	or	PAD = scalar-default-char-expr
	or	POS = scalar-int-expr
	or	REC = scalar-int-expr
	or	ROUND = scalar-default-char-expr
	or	SIGN = scalar-default-char-expr
	or	SIZE = scalar-int-variable
R914	format	is	default-char-expr
	or	label
	or	*
R915	input-item	is	variable
	or	io-implied-do
R916	output-item	is	expr
	or	io-implied-do
R917	io-implied-do	is	( io-implied-do-object-list , io-implied-do-control )
R918	io-implied-do-object	is	input-item
	or	output-item
R919	io-implied-do-control	is	do-variable = scalar-int-expr ,  scalar-int-expr [ , scalar-int-expr ]
R920	dtv-type-spec	is	TYPE( derived-type-spec )
	or	CLASS( derived-type-spec )
R921	wait-stmt	is	WAIT ( wait-spec-list )
R922	wait-spec	is	[ UNIT = ] file-unit-number
	or	END = label
	or	EOR = label
	or	ERR = label
	or	ID = scalar-int-variable
	or	IOMSG = iomsg-variable
	or	IOSTAT = scalar-int-variable
R923	backspace-stmt	is	BACKSPACE file-unit-number
	or	BACKSPACE ( position-spec-list )
R924	endfile-stmt	is	ENDFILE file-unit-number
	or	ENDFILE ( position-spec-list )
R925	rewind-stmt	is	REWIND file-unit-number
	or	REWIND ( position-spec-list )
R926	position-spec	is	[ UNIT = ] file-unit-number
	or	IOMSG = iomsg-variable
	or	IOSTAT = scalar-int-variable
	or	ERR = label
R927	inquire-stmt	is	INQUIRE ( inquire-spec-list )
	or	INQUIRE ( IOLENGTH = scalar-int-variable ) output-item-list
R928	inquire-spec	is	[ UNIT = ] file-unit-number
	or	FILE = file-name-expr
	or	ACCESS = scalar-default-char-variable
	or	ACTION = scalar-default-char-variable
	or	ASYNCHRONOUS = scalar-default-char-variable
	or	BLANK = scalar-default-char-variable
	or	DECIMAL = scalar-default-char-variable
	or	DELIM = scalar-default-char-variable
	or	DIRECT = scalar-default-char-variable
	or	ERR = label
	or	EXIST = scalar-default-logical-variable
	or	FORM = scalar-default-char-variable
	or	FORMATTED = scalar-default-char-variable
	or	ID = scalar-int-variable
	or	IOMSG = iomsg-variable
	or	IOSTAT = scalar-int-variable
	or	NAME = scalar-default-char-variable
	or	NAMED = scalar-default-logical-variable
	or	NEXTREC = scalar-int-variable
	or	NUMBER = scalar-int-variable
	or	OPENED = scalar-default-logical-variable
	or	PAD = scalar-default-char-variable
	or	PENDING = scalar-default-logical-variable
	or	POS = scalar-int-variable
	or	POSITION = scalar-default-char-variable
	or	READ = scalar-default-char-variable
	or	READWRITE = scalar-default-char-variable
	or	RECL = scalar-int-variable
	or	ROUND = scalar-default-char-variable
	or	SEQUENTIAL = scalar-default-char-variable
	or	SIGN = scalar-default-char-variable
	or	SIZE = scalar-int-variable
	or	STREAM = scalar-default-char-variable
	or	UNFORMATTED = scalar-default-char-variable
	or	WRITE = scalar-default-char-variable
R1001	format-stmt	is	FORMAT format-specification
R1002	format-specification	is	( [ format-item-list ] )
R1003	format-item	is	[ r ] data-edit-desc
	or	control-edit-desc
	or	char-string-edit-desc
	or	[ r ] ( format-item-list )
R1004	r	is	int-literal-constant
R1005	data-edit-desc	is	I w [ . m ]
	or	B w [ . m ]
	or	O w [ . m ]
	or	Z w [ . m ]
	or	F w . d
	or	E w . d [ E e ]
	or	EN w . d [ E e ]
	or	ES w . d [ E e ]
	or	G w . d [ E e ]
	or	L w
	or	A [ w ]
	or	D w . d
	or	DT [ char-literal-constant ] [ ( v-list ) ]
R1006	w	is	int-literal-constant
R1007	m	is	int-literal-constant
R1008	d	is	int-literal-constant
R1009	e	is	int-literal-constant
R1010	v	is	signed-int-literal-constant
R1011	control-edit-desc	is	position-edit-desc
	or	[ r ] /
	or	:
	or	sign-edit-desc
	or	k P
	or	blank-interp-edit-desc
	or	round-edit-desc
	or	decimal-edit-desc
R1012	k	is	signed-int-literal-constant
R1013	position-edit-desc	is	T n
	or	TL n
	or	TR n
	or	n X
R1014	n	is	int-literal-constant
R1015	sign-edit-desc	is	SS
	or	SP
	or	S
R1016	blank-interp-edit-desc	is	BN
	or	BZ
R1017	round-edit-desc	is	RU
	or	RD
	or	RZ
	or	RN
	or	RC
	or	RP
R1018	decimal-edit-desc	is	DC
	or	DP
R1019	char-string-edit-desc	is	char-literal-constant
R1101	main-program	is	[ program-stmt ]
	[ specification-part ]
	[ execution-part ]
	[ internal-subprogram-part ]
	end-program-stmt
R1102	program-stmt	is	PROGRAM program-name
R1103	end-program-stmt	is	END [ PROGRAM [ program-name ] ]
R1104	module	is	module-stmt
	[ specification-part ]
	[ module-subprogram-part ]
	end-module-stmt
R1105	module-stmt	is	MODULE module-name
R1106	end-module-stmt	is	END [ MODULE [ module-name ] ]
R1107	use-stmt	is	USE [ [ , module-nature ] :: ] module-name [ , rename-list ]
	or	USE [ [ , module-nature ] :: ] module-name ,  ONLY : [ only-list ]
R1108	module-nature	is	INTRINSIC
	or	NON_INTRINSIC
R1109	rename	is	local-name => use-name
	or	OPERATOR ( local-defined-operator ) =>  OPERATOR ( use-defined-operator )
R1110	only	is	generic-spec
	or	only-use-name
	or	rename
R1111	only-use-name	is	use-name
R1112	local-defined-operator	is	defined-unary-op
	or	defined-binary-op
R1113	use-defined-operator	is	defined-unary-op
	or	defined-binary-op
R1114	block-data	is	block-data-stmt
	[ specification-part ]
	end-block-data-stmt
R1115	block-data-stmt	is	BLOCK DATA [ block-data-name ]
R1116	end-block-data-stmt	is	END [ BLOCK DATA [ block-data-name ] ]
R1201	interface-block	is	interface-stmt
	[ interface-specification ] ...
	end-interface-stmt
R1202	interface-specification	is	interface-body
	or	procedure-stmt
R1203	interface-stmt	is	INTERFACE [ generic-spec ]
	or	INTERFACE PROCEDURE ( )
R1204	end-interface-stmt	is	END INTERFACE [ generic-spec ]
R1205	interface-body	is	function-stmt
	[ specification-part ]
	end-function-stmt
	or	subroutine-stmt
	[ specification-part ]
	end-subroutine-stmt
R1206	procedure-stmt	is	[ MODULE ] PROCEDURE procedure-name-list
R1207	generic-spec	is	generic-name
	or	OPERATOR ( defined-operator )
	or	ASSIGNMENT ( = )
	or	dtio-generic-spec
R1208	dtio-generic-spec	is	READ ( FORMATTED )
	or	READ ( UNFORMATTED )
	or	WRITE ( FORMATTED )
	or	WRITE ( UNFORMATTED )
R1209	import-stmt	is	IMPORT [ :: ] import-name-list
R1210	external-stmt	is	EXTERNAL [ :: ] external-name-list
R1211	procedure-declaration-stmt	is	PROCEDURE ( [ proc-interface ] ) [ [ , proc-attr-spec ] ... :: ]  proc-decl-list
R1212	proc-interface	is	abstract-interface-name
	or	declaration-type-spec
R1213	proc-attr-spec	is	access-spec
	or	language-binding-spec
	or	INTENT ( intent-spec )
	or	OPTIONAL
	or	POINTER
	or	SAVE
R1214	proc-decl	is	procedure-entity-name [ => NULL ( ) ]
R1215	abstract-interface-name	is	name
R1216	intrinsic-stmt	is	INTRINSIC [ :: ] intrinsic-procedure-name-list
R1217	function-reference	is	procedure-designator ( [ actual-arg-spec-list ] )
R1218	call-stmt	is	CALL procedure-designator [ ( [ actual-arg-spec-list ] ) ]
R1219	procedure-designator	is	procedure-name
	or	data-ref % procedure-component-name
	or	data-ref % binding-name
R1220	actual-arg-spec	is	[ keyword = ] actual-arg
R1221	actual-arg	is	expr
	or	variable
	or	procedure-name
	or	alt-return-spec
R1222	alt-return-spec	is	* label
R1223	function-subprogram	is	function-stmt
	[ specification-part ]
	[ execution-part ]
	[ internal-subprogram-part ]
	end-function-stmt
R1224	function-stmt	is	[ prefix ] FUNCTION function-name  ( [ dummy-arg-name-list ] )  [ , proc-language-binding-spec ] [ RESULT ( result-name ) ]
R1225	proc-language-binding-spec	is	language-binding-spec
R1226	dummy-arg-name	is	name
R1227	prefix	is	prefix-spec [ prefix-spec ] ...
R1228	prefix-spec	is	declaration-type-spec
	or	RECURSIVE
	or	PURE
	or	ELEMENTAL
R1229	end-function-stmt	is	END [ FUNCTION [ function-name ] ]
R1230	subroutine-subprogram	is	subroutine-stmt
	[ specification-part ]
	[ execution-part ]
	[ internal-subprogram-part ]
	end-subroutine-stmt
R1231	subroutine-stmt	is	[ prefix ] SUBROUTINE subroutine-name  [ ( [ dummy-arg-list ] ) ] [ , proc-language-binding-spec ]
R1232	dummy-arg	is	dummy-arg-name
	or	*
R1233	end-subroutine-stmt	is	END [ SUBROUTINE [ subroutine-name ] ]
R1234	entry-stmt	is	ENTRY entry-name [ ( [ dummy-arg-list ] ) [ , proc-language-binding-spec ] [ RESULT ( result-name ) ] ]
	or	ENTRY entry-name [ , proc-language-binding-spec ] [ RESULT ( result-name ) ]
R1235	return-stmt	is	RETURN [ scalar-int-expr ]
R1236	contains-stmt	is	CONTAINS
R1237	stmt-function-stmt	is	function-name ( [ dummy-arg-name-list ] ) = scalar-expr
"""


if __name__ == "__main__":
    main()
