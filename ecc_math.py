from tinyec import registry
import secrets

# Using NIST P-256 as paper requires large prime field curve
curve = registry.get_curve("secp256r1")
P = curve.g
q = curve.field.n

def random_scalar():
    return secrets.randbelow(q - 1) + 1

def point_multiply(k, point):
    return k * point

def point_add(p1, p2):
    return p1 + p2

def scalar_mod_q(x):
    return x % q