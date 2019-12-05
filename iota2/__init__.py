import sys
import os

iota2dir, _ = os.path.split(__file__)
if not iota2dir in sys.path:
    sys.path.append(iota2dir)
