import re

_p1 = re.compile(r'(.)([A-Z][a-z]+)')
_p2 = re.compile(r'([a-z0-9])([A-Z])')

def snake_case(name):
    return _p2.sub(r'\1_\2', _p1.sub(r'\1_\2', name)).lower()
