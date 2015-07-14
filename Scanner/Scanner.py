#!/usr/bin/env python

import re
from   string                import expandtabs,rstrip,lstrip,strip, upper
from   Token                 import Token, Token2Name
from   AOR.AttributeString   import AttributeString
from   AOR.SpecialStatements import Comment, ContMarker, CommentLine

def ScannerFactory(name=None,lines=None,format=None,maxcols=None,
                   project=None):
  """ return an instance of scanner. try to be clever, eg
      work out whether to use fixed or free form, set
      provide a set of lines instead of a file if testing
      is being done, etc """

  use_format = "fixed"
  use_maxcols = 72

  if name:
    if not project:
      # Avoid circular references: project -> Scanner -> project
      from Tools.Project import Project
      project = Project()
      
    dFileOpt = project.dGetFileOptions(name)
    # is it fixed or free format?
    if name[-1] == '0': # f90, F90, ...?
      use_format  = dFileOpt.get("format","free")
      use_maxcols = dFileOpt.get("linelength",132)
    else:
      use_format  = dFileOpt.get("format","fixed")
      use_maxcols = dFileOpt.get("linelength",72)

  # explicit format overrides the guess
  if format:
    use_format = format

  if maxcols:
    use_maxcols = maxcols

  if use_format=="free":
    return FreeformScanner(name,use_maxcols,lines, project)
  else:
    return FixedformScanner(name,use_maxcols,lines, project)

# =============================================================================

class Scanner(Token):
  """ view of a fortran file as a set of tokens """

  def __init__(self, name=None, maxcols=72, lines=None, project=None):
    # Create a project instance, to get access to the FindFile function,
    # which is needed for include files.
    if project:
      self.project = project
    else:
      from Tools.Project import Project
      self.project = Project()
      
    
    # Each part is a tuple of (line, column, type, text)
    # Certain tokens (compiler- and preprocessor directives, comments, and
    # continuation marker) are actually stored as postfix or prefix attributes
    # of a string of a 'real' token (a 'real' token is everything else).
    # Currently, all such attribute tokens are stored as prefix attributes of
    # the next real token, except for the last tokens of a file which gets
    # stored as a postfix token of the last real token.
    # Attributes are stored in the string part of a token: instead of
    # a normal string an object of type AttributeString is created,
    # which is a string with a list of prefix- and postfix-attributes.    
    self.tokens = []
    
    # Tokens, which are converted into attributes, are collected here.
    # This is e.g. needed for comments at the beginning of a file, etc.
    self.lPrefix = []
    self.name    = name

    # maxcols is usually 72 or 132 but can be changed with
    # compiler options, so we need to support this. Anything
    # beyond this column is kept but ignored
    self.maxcols = maxcols

    # for testing a number of lines of code might be passed
    # in explicitly. In this case ignore the file and scan
    # the passed lines
    self.lines = lines

    # For include files: a separate scanner handling the included file:
    self.includescanner = None

    # scan the file
    self.Scan()

    # initialise the iterator
    self.current = 0

  # ---------------------------------------------------------------------------

  def GetNextToken(self):
    """ return a tuple with the next token: (type, string) """
    # First see if we are currently reading from an include file
    if self.includescanner:
      # If so, call the scanner handling the included file ...
      t = self.includescanner.GetNextToken()
      if t:
        return t                        # and return its token - if it exists
      # Otherwise: reset the include scanner, and continue wit the token from
      # the currently handled file.
      self.includescanner=None
      
    if self.current<len(self.tokens):
      while 1:
        self.current = self.current+1
        if self.tokens[self.current-1][2]!=self.tok_INCLUDE:
          return (self.tokens[self.current-1][2],self.tokens[self.current-1][3])
          
        # Create a scanner for the include file. If the include file
        # is not found, ignore this error and get the next token
        # from the current file
        if not self.DoInclude(self.tokens[self.current-1][3]):
          continue
        
        t=self.includescanner.GetNextToken()
        if t: return t
          
        # Special case: we have an empty include file (or at least
        # without any real tokens in it)
        self.includescanner=None
        
    else:
      return None

  # ---------------------------------------------------------------------------
  def DoInclude(self, sFilename=None):
    if self.includescanner:
      return self.includescanner.DoInclude(sFilename)
    
    fName = self.project.FindFile(sFilename)
    if not fName:
      print 'include file "%s" not found'%sFilename
      print '(this error can be ignored)'
      return 0
    
    self.includescanner = ScannerFactory(fName)
    return self.includescanner
  # ---------------------------------------------------------------------------
  # Returns true if currently data is read from an include file. 
  def bIsIncludeFile(self): return self.includescanner!=None
  # ---------------------------------------------------------------------------
  # Returns the name of the include file, from which data is currently read.
  def sGetIncludeFilename(self): return self.includescanner.GetFilename()
  # ---------------------------------------------------------------------------

  def UnGet(self,lasttoken):
    """ wind the iterator back one. For now lasttoken is ignored """
    if self.includescanner:
      self.includescanner.UnGet(lasttoken)
    else:
      if self.current>0:
        self.current = self.current-1

  # ---------------------------------------------------------------------------
  # Returns a tuple (line number, column number)
  def GetLocation(self): return (self.tokens[self.current-1][0],
                                 self.tokens[self.current-1][1])
  # ---------------------------------------------------------------------------
  # Returns a tuple (line number, column number) for the previous token
  def GetPreviousLocation(self):
    if(self.current>1):
      return (self.tokens[self.current-2][0],
              self.tokens[self.current-2][1])
    else:
      # If there is no previous token (self.current always points to the NEXT
      # token, not to the current one), we just return the current token.
      return self.GetLocation()
  # ---------------------------------------------------------------------------

  def GetLinenumber(self):
    return self.tokens[self.current-1][0]

  # ---------------------------------------------------------------------------

  def GetColumnnumber(self):
    return self.tokens[self.current-1][1]

  # ---------------------------------------------------------------------------

  def GetFormat(self):
    # deferred to subclass
    return ""

  # ---------------------------------------------------------------------------
  def GetFileLocation(self):
    if self.includescanner:
      sLocation = self.includescanner.GetFileLocation()
      return '%s included from %s (line # %d)'%(sLocation, self.name,
                                                self.GetLinenumber())
    return '%s (line# %d)'%(self.name, self.GetLinenumber())
  # ---------------------------------------------------------------------------
  def GetCurrentLine(self):
    return self.lines[self.GetLinenumber()-1]
  # ---------------------------------------------------------------------------

  def GetFilename(self):
    if self.includescanner:
      sName = self.includescanner.GetFilename()
      return '%s included from %s'%(sName, self.name)
    return self.name

  # ---------------------------------------------------------------------------

  def eof(self):
    """ test for end of file (ie all tokens got) """
    return not self.includescanner and self.current>=len(self.tokens)

  # ---------------------------------------------------------------------------
  # --- private ---

  def GetLines(self):
    if self.lines != None:
      return self.lines
    else:
      f = open(self.name, 'r')
      self.lines = f.readlines()
      f.close()
      return self.lines

  # ---------------------------------------------------------------------------

  def Scan(self):
    """ scan the file into a list of tokens. this routine sorts out
        blank lines, string literals, continuation markers etc from the
        actual code, and passes actual code to Tokenise() to extract
        specific tokens
    """

    text = self.GetLines()

    # some aspects of fortran are context dependant, eg in free form only
    # look for a label at the start of a statement, and a leading continuation
    # marker if a trailing one was found on the previous line. line_type 
    # indicates the current context
    line_type = self.NEW_STATEMENT
    i = -1
    while i<len(text)-1:
      i = i+1
      line_num = i+1
      # untangle tab stops right upfront
      line = expandtabs(rstrip(text[i]))


      
      # catch compiler directives
      if self.re_directive.match(line):
        col_num = len(line)-len(lstrip(line)) + 1
        self.AppendToken(line_num, col_num, self.tok_DIRECTIVE, line)
        self.AppendToken(line_num, len(line), self.tok_SEPARATOR, "")
        continue

      # catch other comment lines (which includes empty lines)
      if line.strip()=='' or self.re_commentline.match(line):
        col_num = len(line)-len(lstrip(line)) + 1
        if line_type!=self.NEW_STATEMENT:
          self.AppendAttribute(CommentLine(line))
        else:
          self.AppendToken(line_num, col_num, self.tok_COMMENTLINE, line)
          self.AppendToken(line_num, len(line), self.tok_SEPARATOR, "")
        continue

      # catch preprocessing lines
      if self.re_cppline.match(line):
        g=self.re_cppinclude.match(line)
        if g:
          col_num = len(line)-len(lstrip(line)) + 1
          self.AppendIncludeToken(line_num, col_num, g.group(1))
        col_num = len(line)-len(lstrip(line)) + 1
        self.AppendToken(line_num, col_num, self.tok_PREDIRECTIVE, lstrip(line))
        self.AppendToken(line_num, len(line), self.tok_SEPARATOR, "")
        continue

      # anything after line 72/132 is happily ignored by fortran. If it
      # is part of a comment all is well, otherwise there is probably a
      # subtle coding error (or some devious programmer is using the 
      # columns after 72/132 to hold comments without a sentinal. urk, it
      # doesn't bear thinking about ...)
      # Hold onto text after line 72/132 and add it either to the trailing 
      # comment or to the part list as ignored text.
      remainder = ''
      if len(line)>self.maxcols:
        remainder = line[self.maxcols:]
        line = line[:self.maxcols]

      # remove format and context dependant complicated bits 
      col_num = 1

      old_len = len(line)
      line    = self.StripLabel(line,line_num,col_num,line_type)
      new_len = len(line)
      col_num = col_num + old_len - new_len

      old_len = new_len
      line    = self.StripContMark(line,line_num,col_num,line_type)
      new_len = len(line)
      col_num = col_num + old_len - new_len

      if line_type==self.CONT_SQUOTE or line_type==self.CONT_DQUOTE:
        old_len = new_len
        line    = self.StripContQuote(line,line_num,col_num,line_type)
        new_len = len(line)
        col_num = col_num + old_len - new_len
        if line=='':
          # quote was rest of line - check if it is finished
          if self.tokens[-1][2]!=self.tok_QUOTE_END and \
                 self.tokens[-1][2]!=self.tok_QUOTE_MIDDLE:
            line_type = self.NEW_STATEMENT
          elif self.tokens[-1][2]==self.tok_QUOTE_END:
            line_type = self.NEW_STATEMENT
            self.AppendToken(line_num, col_num, self.tok_SEPARATOR, "")
          continue

      # reset line_type for next line (any variations from default will 
      # be picked up in j loop below)
      line_type = self.NEW_STATEMENT


      # findall returns a lit of tokens. split returns everything between
      # them. If all is well split should only return only blocks of 
      # whitespace (which we use to get the column number of each token).
      # anything non-whitespace that it finds is a mystery token, store
      # it as unknown
      everything = self.re_all_tokens.findall(line)
      spacing    = self.re_all_tokens.split(line)

      for j in range(len(everything)):
          space_len  = len(spacing[j])
          space_text = lstrip(spacing[j])
          if space_text!='':
              # we have found something we don't understand!
              col_num = col_num+(space_len-len(space_text))
              self.AppendToken(line_num, col_num, self.tok_UNKNOWN, space_text)
              col_num = col_num+len(space_text)
          else:
              col_num = col_num+space_len

          if everything[j]=='&' and line_type!=self.CONT_SQUOTE  \
                 and line_type!=self.CONT_DQUOTE:
              line_type=self.CONT_STATEMENT

          # check for macro-token types (string literals, continuation
          # markers,statement separators (;) and trailing comments)
          col_num = self.Tokenise(line_num,col_num,everything[j])
          # if token was an unfinished quote we will need to set line_type
          if self.tokens[-1][2]==self.tok_QUOTE_START \
                 and line_type!=self.CONT_SQUOTE and line_type!=self.CONT_DQUOTE:
              if everything[j][0]=='\'':
                  line_type = self.CONT_SQUOTE
              else:
                  line_type = self.CONT_DQUOTE

      if remainder!='':
        self.AppendAttribute(Comment(remainder, (line_num, col_num)))

      if line_type==self.NEW_STATEMENT:
        self.AppendToken(line_num, col_num, self.tok_SEPARATOR, "")

    if self.lPrefix:
      if len(self.tokens)==0:
        # This can happen if we have a (usually include) file which doesn't
        # have any real tokens, e.g. only comments and another include.
        # Any include file in the current file IS handled correctly, just
        # the current file can not be correctly represented, since there is
        # no way to store the attributes.
        return
      prevtok = self.tokens[-1]
      sOld    = prevtok[3]
      if sOld.__class__==str:
        sOld=AttributeString(sOld)
      elif not sOld.__class__==AttributeString:
        # This can happen if we have a (usuallly include) file which doesn't
        # have any real tokens, e.g. only comments and another include.
        # Any include file in the current file IS handled correctly, just
        # the current file can not be correctly represented, since there is
        # no way to store the attributes.
        return
      
      # Special case: comments (or directives, ... ) following the last
      # real fortran token. In this case self.lPrefix contains the missing
      # special lines (which usually would be added as a prefix to the next
      # fortran token), which is now appended as a postfix to the
      # last real fortran token.
      if self.lPrefix:
        # The parameter -2 specifies which element to replace: the last element
        # is the separator token, so we have to add the missing lines to the
        # second last token in the list.
        # As a more difficult test: include files which only contain
        # comments and #includes --> no fortran tokens to attach anything to :(
        # I don't have a nice solution at this time, so we just handle this as
        # a special case and ignore the tokens (which means we have an empty file).
        if len(self.tokens)>=2:
          self.AppendAttribute2PreviousToken(self.lPrefix, n=-2)
        self.lPrefix=[]

  # ---------------------------------------------------------------------------

  def StripLabel(self,line,line_num,col_num,next):
    # deferred to subclass
    return line

  # ---------------------------------------------------------------------------

  def StripContMark(self,line,line_num,col_num,next):
    # deferred to subclass
    return line

  # ---------------------------------------------------------------------------

  def StripContQuote(self,line,line_num,col_num,next):
    # deferred to subclass
    return line

  # ---------------------------------------------------------------------------
  def AppendAttribute(self, att):
    # If a continuation marker is written, a previously written
    # end of statement marker is invalid and must be removed. An
    # eos marker can not have any attributes, so no need to check this.
    # It is more efficient to remove a previously appended marker than
    # checking whenever a tok_SEPARATOR is written if the next (non
    # comment, ...) line is not a continuation (at least for fixed format):
    # 1) we had to find the next non-{comment, pre-directive,
    #    compiler-directive} line - which involves regexp comparisons
    # 2) Many more lines are not continued (i.e. the marker doesn't
    #    have to be removed) than continued, so we remove less lines
    #    than we had to check otherwise
    if att.__class__==ContMarker:
      self.ContLineCleanup()

    # If the token to append is an attribute, just append it to the list
    # of prefix attributes. Prefix is the default, which applies to most
    # of the attributes quite naturally (except: endserial, endcritical,
    # tasklocal, taskglobal, vreg, select, endif - which would be more
    # 'natural' to be appended as postfix, but it actually shouldn't matter
    # currently).
    if att.__class__==Comment:
      # We should never have a COMMENT (not a COMMENT_LINE) before we have
      # a real token, so it is safe to access tokens[-1]
      self.AppendAttribute2PreviousToken(att)
    else:
      self.lPrefix.append( att )

  # ---------------------------------------------------------------------------
  # This function is called when a continuation marker (in fixed form) is found.
  # This means, that:
  # 1) the previous token (after which an end of line token was appended) was
  #    not the last token of the 'line'.
  # 2) Any comment, directive lines since the last real token can not be
  #    treated as stand-alone types, bust must be added as an attribute
  #    instead, since they can't be part of the (extended grammar)
  def ContLineCleanup(self):
    if not self.tokens: return
    
    # Now search for the last real token, and skip all special
    # tokens like comments, directives, and end-of-line separators.
    # -------------------------------------------------------------
    i=len(self.tokens)-1
    t=self.tokens[i]
    while i>=0 and (t[2]==Token.tok_COMMENTLINE  or \
                    t[2]==Token.tok_PREDIRECTIVE or \
                    t[2]==Token.tok_DIRECTIVE    or \
                    t[2]==Token.tok_SEPARATOR        ):
      i=i-1
      t=self.tokens[i]

    # Now i is the last real token, i+1 is the separator token:
    # ---------------------------------------------------------
    i=i+1
    
    # Now convert all non-separator tokens into attributes:
    # -----------------------------------------------------
    if i>=0 and i<=len(self.tokens)-1 and \
           self.tokens[i][2]==Token.tok_SEPARATOR:
      # Now convert all commentlines and directives into
      # attributes
      j=i+1
      while j<len(self.tokens):
        if self.tokens[j][2]==Token.tok_COMMENTLINE:
          self.lPrefix.append( CommentLine(self.tokens[j][3]) )
        elif self.tokens[j][2]!=Token.tok_SEPARATOR:
          self.lPrefix.append( self.tokens[j][3] )
        j=j+1

      # Then remove the unnecessary end-of-line tokens and
      # the tokens which were converted into attributes:
      # --------------------------------------------------
      del self.tokens[i:]

  # ---------------------------------------------------------------------------
  # This appends the attribute 'att' as a postfix attribute to the last token
  # on the token stack.
  def AppendAttribute2PreviousToken(self, att, n=-1):
    prevtok = self.tokens[n]
    sOld    = prevtok[3]
    if not isinstance(sOld, AttributeString):
      sOld=AttributeString(sOld)
    sOld.AppendPostfix( att )
    self.tokens[n] = (prevtok[0], prevtok[1], prevtok[2], sOld)
  # ---------------------------------------------------------------------------
  # This function insers a special token, which tells GetNextToken that the
  # next token is to be read from an include file. It might be more convenient,
  # if the scanner would only read one line - handling of include files would
  # probably be simpler.
  # AppendToken can not be used, since we don't want to have any attributes
  # attached to this special token.
  def AppendIncludeToken(self, line, column, sFilename):
    self.tokens.append( (line, column, self.tok_INCLUDE, sFilename) )
  # ---------------------------------------------------------------------------
  # Appends a token to the list of all tokens. If a (list of) prefix attributes
  # are defined, the actual string part of the token will be converted to an
  # AttributeString, and the prefixes will be attached as prefix to the string.
  def AppendToken(self, line, column, tokentype, s):
    if self.lPrefix:
      sAtt = AttributeString(s)
      sAtt.SetPrefixAttributes(self.lPrefix)
      self.lPrefix=[]
      self.tokens.append( (line, column, tokentype, sAtt) )
    else:
      self.tokens.append( (line, column, tokentype, s) )

  # ---------------------------------------------------------------------------

  def Tokenise(self,line_num,col_num,text):
    # determine what a specific token is and add it to the token list
    if text[0]=='!':
      self.AppendAttribute(Comment(text, (line_num, col_num)))
      return col_num+len(text)

    if text[0]=='\'':
      if text[-1]==text[0] and (self.re_oddsquote.search(text) or text=="''"):
        tok_type = self.tok_QUOTE
      else:
        tok_type = self.tok_QUOTE_START

    elif text[0]=='"':
      if text[-1]==text[0] and (self.re_odddquote.search(text) or text=='""'):
        tok_type = self.tok_QUOTE
      else:
        tok_type = self.tok_QUOTE_START

    elif text[0]=='&':
      # non-leading cont marker: free form only
      # need to remove leading blanks in col_num calculation
      col_num = col_num + len(text)-1
      
      # A non-leading cont marker needs to be appended to the
      # previous tokens as a postfix.
      self.AppendAttribute2PreviousToken(ContMarker(text[0],
                                                    (line_num, col_num))  )
      return col_num

    elif text[0]==';':
      # only relevant in free format
      tok_type = self.tok_SEPARATOR

    elif self.re_truefalse.match(text): # check first for .true./.false.
      tok_type = self.tok_TRUEFALSE     # otherwhise these would be an operator!
      
    elif self.re_special.match(text):
      tok_type = self.tok_SPECIAL

    elif self.re_operator.match(text):
      tok_type = self.tok_OPERATOR

    elif self.re_number.match(text):
      tok_type = self.tok_NUMBER

    elif self.re_keyword.match(text):
      tok_type = self.tok_KEYWORD

    elif self.re_identifier.match(text):
      tok_type = self.tok_IDENTIFIER

    else:
      # no idea what it is
      tok_type = self.tok_UNKNOWN

    self.AppendToken(line_num, col_num, tok_type, text)
    return col_num+len(text)
  
  # ---------------------------------------------------------------------------
  # --- line types ---
  NEW_STATEMENT  = 0
  CONT_STATEMENT = 1
  CONT_SQUOTE    = 2
  CONT_DQUOTE    = 3

  # --- token types ---
  # (moved into Token base class)

  # --- patterns ---

    # comments
  p_commentline       = r'(?:^\s*!.*$)'
  p_trailing_comment  = r'(?:!.*$)'
  re_commentline      = re.compile(p_commentline)

    # f90 directives
  p_directive  = r'(?:[!c\*][vc]dir.*$)' +'|'+ r'(?:!\$omp.*$)'
  re_directive = re.compile(p_directive,re.I)

    # preprocessor lines
  p_cppline     = r'(?:^#)'
  p_include     = r'(?:^#\s*include\s*"([^"]+))"'
  re_cppline    = re.compile(p_cppline)
  re_cppinclude = re.compile(p_include)
  

    # string literals
  p_dquote_start     = r'(?:\")'
  p_dquote_end       = r'(?:.*?(?:[^"]\"(?!\")))'
  p_squote_start     = r'(?:\')'
  p_squote_end       = r'(?:.*?(?:[^\']\'(?!\')))'
  # Handle the special case of an empty string: "" or '' - an empty string
  # does not match p_?quote_start+p_?quote_end, since the end regular
  # expressions must contain one non-quote character!!
  p_full_quote       = p_dquote_start+p_dquote_end +"|''|"+ \
                       p_squote_start+p_squote_end +'|""'
  p_odddquote        = r'(?:[^"]"("")*)$'
  p_oddsquote        = r"(?:[^']'('')*)$"
  re_odddquote       = re.compile(p_odddquote)
  re_oddsquote       = re.compile(p_oddsquote)

    # number literals (note: hex, octal, binary numbers not supported yet)
  #JH# Causes a problem with "2_1", because of the \b. Not sure if this
  # breaks anything else
  # p_num   = r'(?:\b[0-9]+(?:\.(?! *[A-Za-z]+\.))?[0-9]*|\.[0-9]+)'
  p_num     = r'(?:[0-9]+(?:\.(?! *[A-Za-z]+\.))?[0-9]*|\.[0-9]+)'
  p_number  = r'(?:'+p_num+r'(?: *[DEde] *[+-]?[0-9]+)?)'
  re_number = re.compile(p_number)

    # other tokens
  p_operator_m = r'(?:\*\*|//|==|/=|<=|>=|\. *[A-Za-z]+ *\.)'
  p_operator_s = r'(?:\+|-|\*|/|<|>)'
  # The order for p_special is important! (/ must be recognised first!
  # A '=' must only be recognised if the next character isn't a
  # '=' (else we have a '==', which is matched later!!!)
  p_special    = r'(?:/\)|\(/|/\)|\(|\)|:|,|=>|%|=(?!=)|\_)'
  
  # must be distinguished from an operator!
  p_truefalse  = r'(?:\.true\.|\.false\.|\.t\.|\.f\.)' 
  re_truefalse = re.compile(p_truefalse, re.I)
  re_operator  = re.compile(p_operator_m +'|'+ p_operator_s)
  re_special   = re.compile(p_special)
  
    # the fact the (in fixed form at least) identifiers can have spaces
    # is not considered yet!
  p_identifier  = r'(?:[A-Za-z][A-Za-z0-9_]*)'
  re_identifier = re.compile(p_identifier)

    # keyword
  p_keyword1 = r'(?:call|deallocate|allocate|subroutine|function)'
  p_keyword2 = r'(?:else(?: *if)?)'
  p_keyword  = p_keyword2 + r'(?= )'   # p_keyword1 +'|'+ p_keyword2 + r'(?= )'
  re_keyword = re.compile(p_keyword,re.I)

  p_basic_tokens  = None # deferred to subclass
  re_basic_tokens = None # deferred to subclass

  p_code_tokens   = p_special + '|'+p_operator_m +'|'+ p_operator_s +'|'+ \
                    p_number + '|'+ p_identifier

  
# =============================================================================
class FreeformScanner(Scanner):
  """ specifics for fortran free format files """

  def __init__(self, name, maxcols=132,lines=None, project=None):
    Scanner.__init__(self,name,maxcols,lines,project)

  # ---------------------------------------------------------------------------

  def GetFormat(self):
    return "free"

  # ---------------------------------------------------------------------------
  # --- private ---

  def StripLabel(self,line,line_num,col_num,next):
    # in free format labels are only at the start of a statement
    if next==self.NEW_STATEMENT:
      labelmatch = self.re_label.match(line)
      if labelmatch:
        text = lstrip(labelmatch.group())
        col_num = col_num + labelmatch.end()-len(text)
        self.AppendToken(line_num, col_num, self.tok_LABEL, rstrip(text))
        line = line[labelmatch.end():]
    return line

  # ---------------------------------------------------------------------------

  def StripContMark(self,line,line_num,col_num,next):
    # continuation mark only if next line is a continued one
    #if next!=self.NEW_STATEMENT:
    contmatch = self.re_contmark.match(line)
    if contmatch:
      text = lstrip(contmatch.group())
      self.AppendAttribute( ContMarker(text, (line_num, col_num)) )
      line = lstrip(line)[1:]
    return line

  # ---------------------------------------------------------------------------

  def StripContQuote(self,line,line_num,col_num,next):
    # note: leading cont mark will already have been stripped
    if next==self.CONT_SQUOTE:
      qmatch = self.re_cont_squote.match(line)
      if qmatch:
        text = qmatch.group()
        # make sure that the string ends in an odd number of quote characters,
        # since a line ending in (e.g.) '' or '''' wouldn't end a string
        is_complete = text[-1]=='\'' and self.re_oddsquote.search(text)
    else: # next==self.CONT_DQUOTE
      qmatch = self.re_cont_dquote.match(line)
      if qmatch:
        text = qmatch.group()
        is_complete = text[-1]=='"' and self.re_odddquote.search(text)

    if qmatch:
      if is_complete:
        self.AppendToken(line_num, col_num, self.tok_QUOTE_END, text)
        line = line[qmatch.end():]
      else:
        text = text[:-1]
        self.AppendToken(line_num, col_num, self.tok_QUOTE_MIDDLE, text)
        col_num = col_num+len(text)
        self.AppendAttribute2PreviousToken(ContMarker('&', (line_num, col_num)))
        line = line[qmatch.end():]
    return line


  # ---------------------------------------------------------------------------
  # --- free format patterns ---

    # string literals
  p_quote_linebreak  = r'(?:.*?(?=&$))'
  p_unfinished_quote = Scanner.p_dquote_start+p_quote_linebreak +'|'+\
                       Scanner.p_squote_start+p_quote_linebreak
  p_mid_squote       = r'(?:^(?:.*?\'\')*[^\']*&$)'
  p_cont_squote      = Scanner.p_squote_end+'|'+p_mid_squote
  re_cont_squote     = re.compile(p_cont_squote)
  p_mid_dquote       = r'(?:^(?:.*?"")*[^"]*&$)'
  p_cont_dquote      = Scanner.p_dquote_end+'|'+p_mid_dquote
  re_cont_dquote     = re.compile(p_cont_dquote)

    # other
  p_contmark         = r'(?:^\s*&)'
  re_contmark        = re.compile(p_contmark)
  p_label            = r'(?:^\s*\d{1,5}\s+)'
  re_label           = re.compile(p_label)

  p_basic_tokens     = Scanner.p_full_quote +'|'+ p_unfinished_quote+'|'+ \
                       Scanner.p_trailing_comment + '|;|&'
  re_basic_tokens    = re.compile(p_basic_tokens)

  p_all_tokens       = p_basic_tokens +'|'+ Scanner.p_code_tokens
  re_all_tokens      = re.compile(p_all_tokens)
 
# =============================================================================
class FixedformScanner(Scanner):
  """ specifics for fortran fixed format files """

  def __init__(self, name, maxcols=72,lines=None,project=None):
    Scanner.__init__(self,name,maxcols,lines,project)

  def GetFormat(self):
    return "fixed"

  # --- private ---

  def StripLabel(self,line,line_num,col_num,next):
    # in fixed format the first 5 cols may hold a label
    labelmatch = self.re_label.match(line[:5])
    if labelmatch:
      text = lstrip(labelmatch.group())
      col_num = col_num + labelmatch.end()-len(text)
      self.AppendToken(line_num, col_num, self.tok_LABEL, rstrip(text))
      line = line[5:]
    return line


  def StripContMark(self,line,line_num,col_num,next):
    # anything in col 6
    if line[6-col_num]!=' ':
      self.AppendAttribute( ContMarker(line[6-col_num], (line_num, 6)) )
      line = line[6-col_num+1:]
    return line


  def StripContQuote(self,line,line_num,col_num,next):
    # note: leading cont mark will already have been stripped
    # This routine only called if a continued quote is expected
    if next==self.CONT_SQUOTE:
      pattern = self.re_cont_squote
      oddpattern = self.re_oddsquote
    else:
      pattern = self.re_cont_dquote
      oddpattern = self.re_odddquote
    qmatch = pattern.match(line)
    if qmatch:
      text = qmatch.group()
      # make sure that the string end in an odd number of quote characters,
      # since a line ending in (e.g.) '' or '''' wouldn't end a string
      if (next==self.CONT_SQUOTE and text[-1]=='\'' or \
         next==self.CONT_DQUOTE and text[-1]=='"') and oddpattern.search(text):
         self.AppendToken(line_num, col_num, self.tok_QUOTE_END, text)
      else:
         self.AppendToken(line_num, col_num, self.tok_QUOTE_MIDDLE, text)
      line = line[qmatch.end():]
    # else something is badly wrong! perhaps need to add error check
    return line


  # --- patterns ---

    # comments
  p_commentline  = r'(?:^[cC\*].*$)|' + Scanner.p_commentline
  re_commentline = re.compile(p_commentline)
 
    # string literals
  p_quote_linebreak  = r'(?:.*?(?=$))'
  p_unfinished_quote = Scanner.p_dquote_start+p_quote_linebreak +'|'+ \
                       Scanner.p_squote_start+p_quote_linebreak
  p_mid_squote       = r'(?:^(?:.*?\'\')*[^\']*$)'
  p_cont_squote      = Scanner.p_squote_end +'|'+ p_mid_squote
  re_cont_squote     = re.compile(p_cont_squote)
  p_mid_dquote       = r'(?:^(?:.*?"")*[^"]*$)'
  p_cont_dquote      = Scanner.p_dquote_end +'|'+ p_mid_dquote
  re_cont_dquote     = re.compile(p_cont_dquote)

    # other 
  p_label             = r'(?:^\s*\d{1,5})'
  re_label            = re.compile(p_label)


  p_basic_tokens = Scanner.p_full_quote +'|'+ p_unfinished_quote+'|'+ \
                   Scanner.p_trailing_comment + '|;|&'
  re_basic_tokens = re.compile(p_basic_tokens)

  p_all_tokens    = p_basic_tokens +'|'+ Scanner.p_code_tokens
  re_all_tokens   = re.compile(p_all_tokens)

# =============================================================================
if __name__=="__main__":
  from Test.ScannerTest import RunAllTests
  RunAllTests()
    
