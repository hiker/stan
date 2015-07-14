#!/usr/bin/env python

import string
from   types           import ListType

# ------------------------------------------------------------------------------
# Creates a flattened list of a list of list of ...
def flatten(l):
    if type(l) != ListType: return [l]
    lResult = []
    for i in l:
        lResult.extend(flatten(i))
    return lResult
                          

# ------------------------------------------------------------------------------
lAllIntrinsics = ['abs',    'acos',  'aimg',  'aint',  'alog',   'alog10',
                  'amax0',  'amax1', 'amin0', 'amin1', 'amod',   'anint',
                  'asin',   'atan',  'atan2', 'cabs',  'ccos',   'cexp',
                  'char',   'clog',  'conjg', 'cos',   'cosh',   'csin',
                  'csqrt',  'dabs',  'dasin', 'datan', 'datan2', 'dcos',
                  'dcosh',  'ddim',  'dexp',  'dim',   'dint',   'dlog',
                  'dlog10', 'dmax1', 'dmin1', 'dmod',  'dnint',  'dprod',
                  'dsign',  'dsin',  'dsqrt', 'dtan',  'dtanh',  'exp',
                  'float',  'iabs',  'ichar', 'idim',  'idint',  'idnint',
                  'ifix',   'index', 'int',   'isign', 'len',    'lge',
                  'lgt',    'lle',   'llt',   'log',   'log10',  'max',
                  'max0',   'max1',  'min',   'min0',  'min1',   'mod',
                  'nint',   'real',  'sign',  'sin',   'sinh',   'sngl',
                  'sqrt',   'tan',   'tanh'                                 ]

# Convert to dictionary for faster access
dAllIntrinsics = {}
for i in lAllIntrinsics:
    dAllIntrinsics[i]=1
    
# Returns 1 if the string in s is an intrinsic function.
def bIsIntrinsic(s):
    s = string.lower(s)
    return dAllIntrinsics.get(s, 0)

            
# ------------------------------------------------------------------------------
