import sys
import os

iota2dir, _ = os.path.split(__file__)
if iota2dir not in sys.path:
    sys.path.append(iota2dir)