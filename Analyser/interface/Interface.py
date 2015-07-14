#!/usr/bin/env python

from AOR.BasicStatement import BasicStatement
from AOR.ProgUnit       import ProgUnit

# Well, an interface isn't really a ProgUnit in the sense of Fortran, but
# it is a collection of (declaration) statements, so I think they are similar
# enough to justify this. The special advantage: Interfaces can be printed
# via any stylesheet, since they are ProgUnits.

class Interface(ProgUnit):
    def __init__(self):
        ProgUnit.__init__(self)

# ==============================================================================
