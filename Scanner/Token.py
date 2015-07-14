#!/usr/bin/env python

class Token:

  # --- token types ---
  #
  # Basically the token number can be arbitrary numbers. But to make
  # some comparisons more efficient, the numbers are grouped.
  # group 1: everything below TOK_ATTRIBUTESMAX
  #          Tokens which should not be returned individually, but which are
  #          added as 'attribute' to the previous token.
  tok_COMMENT      = 1   # full line or trailing comment
  tok_COMMENTLINE  = 2   # full line or trailing comment
  tok_F90_DIR      = 3   # !cdir, !$omp etc
  tok_CPP_DIR      = 4   # #include #define #ifdef etc
  tok_IGNORED      = 5   # anything after col 72/132
  tok_CONT_MARK    = 6   # & at begin or end in free, char in col 6 in fixed
  TOK_ATTRIBUTESMAX= 9
  tok_UNKNOWN      = 10  # catch-all class
  tok_LABEL        = 20  #
  tok_QUOTE_START  = 21  # first part of multiline quote
  tok_QUOTE_MIDDLE = 22  # entire line in a multiline quote (ie no quote marks)
  tok_QUOTE_END    = 23  # last part of multiline quote
  tok_QUOTE        = 24  # entire quote that fits on one line
  tok_SEPARATOR    = 25  # ;
  tok_NUMBER       = 26  # number literal
  tok_KEYWORD      = 27  #
  tok_IDENTIFIER   = 28  #
  tok_OPERATOR     = 29  # +,-,*,**,.ge. .and. .not. .true. 
  tok_TRUEFALSE    = 30  # .true. or .false.
  tok_SPECIAL      = 31  # (),
  tok_INCLUDE      = 32  # Special tokens, means that the next token must be
                         # read from an include file - the respective scanner
                         # will be the second element of the token
  tok_DIRECTIVE    = 33  # compiler directive
  tok_PREDIRECTIVE = 34  # preprocessor directive
  

# =============================================================================
# Reverse mapping: map a number to a token name
def Token2Name(n):
  # Token.__dict__ is a dictionary with all attributes
  for k,v in Token.__dict__.items():
    if v==n: return k
  return "???"
