import os
import re

def find(basedir='.'):

    return [f for f in os.listdir(basedir) if re.match('^(romulus|cosmo|h).*\.[\d]*$', f)]
