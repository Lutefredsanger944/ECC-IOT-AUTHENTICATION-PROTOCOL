from ecc_math import random_scalar, point_multiply, point_add, scalar_mod_q, P
from hash_functions import h1

class TrustedAuthority:

    def __init__(self):
        self.r_ta = random_scalar()

    def register_sensor(self, ID_s):
        r_s = random_scalar()
        Rs = point_multiply(r_s, P)

        PK_s = point_add(Rs, point_multiply(self.r_ta, P))

        TCssp = h1(ID_s, self.r_ta)

        return {
            "ID_s": ID_s,
            "r_s": r_s,
            "PK_s": PK_s,
            "TCssp": TCssp
        }

    def register_server(self, ID_sp):
        r_sp = random_scalar()
        Rsp = point_multiply(r_sp, P)

        PK_sp = point_add(Rsp, point_multiply(self.r_ta, P))

        return {
            "ID_sp": ID_sp,
            "r_sp": r_sp,
            "PK_sp": PK_sp
        }