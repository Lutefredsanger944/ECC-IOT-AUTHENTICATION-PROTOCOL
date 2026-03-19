import hashlib

def _to_bytes(value):
    if isinstance(value, int):
        return value.to_bytes(32, 'big')
    if isinstance(value, str):
        return value.encode()
    if hasattr(value, 'x'):  # ECC point
        return value.x.to_bytes(32, 'big') + value.y.to_bytes(32, 'big')
    return str(value).encode()

def h(*args):
    data = b''.join(_to_bytes(arg) for arg in args)
    return int(hashlib.sha256(data).hexdigest(), 16)

def h1(*args):
    data = b''.join(_to_bytes(arg) for arg in args)
    return int(hashlib.sha256(data).hexdigest(), 16)