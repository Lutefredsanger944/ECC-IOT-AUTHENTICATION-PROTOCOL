from ecc_math import (
    random_scalar,
    point_multiply,
    scalar_mod_q
)
from hash_functions import h
import time


class Sensor:

    # initialization
    def __init__(self, reg_data, r_ta):

        # Identity and keys
        self.ID_s = reg_data["ID_s"]
        self.r_s = reg_data["r_s"]
        self.PK_s = reg_data["PK_s"]
        self.TCssp = reg_data["TCssp"]

        self.enable_novelty = True
        self.enable_attack_handling = True

        # k_s = (r_s + r_ta) mod q
        self.k_s = scalar_mod_q(self.r_s + r_ta)

        # Protocol state
        self.WT_s = None
        self.ID_sp = None

        self.x_s = None
        self.A_s = None

        # trust management
        self.trust_score = 5
        self.max_trust = 10
        self.min_trust = 0

        # time control
        self.base_expiry = 2
        self.expiry_window = self.base_expiry
        self.last_auth_time = time.time()

        # Device lock flag
        self.locked = False

    # trust decay over time
    def decay_trust(self):

        idle_time = time.time() - self.last_auth_time

        if idle_time > 60:

            decay_steps = int(idle_time / 60)

            self.trust_score = max(
                self.min_trust,
                self.trust_score - decay_steps
            )

            if self.trust_score <= self.min_trust:
                self.locked = True
                raise ValueError("Device locked due to trust decay")

    # R4 complete registration
    def complete_registration(self, server_PK_sp, ID_sp):

        self.ID_sp = ID_sp

        # WT_s = k_s · PK_sp
        self.WT_s = point_multiply(self.k_s, server_PK_sp)

    # A1 sensor authentication start
    def authentication_step_A1(self):

        #  Lock + trust logic ONLY if novelty enabled
        if self.enable_novelty:

            if self.locked:
                raise ValueError("Device locked due to low trust")

            self.decay_trust()

            # Adaptive expiry window
            self.expiry_window = self.base_expiry * max(1, self.trust_score)

        # CORE PROTOCOL (unchanged)
        self.x_s = random_scalar()
        self.A_s = point_multiply(self.x_s, self.PK_s)

        hash_value = h(self.A_s, self.WT_s)
        ETCssp = self.TCssp ^ hash_value

        Vs1 = h(self.ID_s, self.TCssp, self.A_s, self.WT_s)

        return self.A_s, ETCssp, Vs1

    # A4 sensor verification
    def authentication_step_A4(self, A_sp, V_sp, server_obj):

        # CORE ECC (unchanged)
        temp = point_multiply(self.k_s, A_sp)
        SK_s = point_multiply(self.x_s, temp)

        SSK = h(self.ID_s, server_obj.ID_sp, SK_s)

        TC_new = self.TCssp ^ h(SK_s, A_sp)

        expected_Vsp = h(
            self.WT_s,
            self.ID_s,
            TC_new,
            A_sp,
            SSK
        )

        if expected_Vsp != V_sp:

            #  Trust penalty ONLY if novelty enabled
            if self.enable_novelty:
                self.trust_score = max(
                    self.min_trust,
                    self.trust_score - 1
                )

                if self.trust_score <= self.min_trust:
                    self.locked = True

            raise ValueError("V_sp verification failed")

        # CORE update (must always happen)
        self.TCssp = TC_new

        #  Trust increase ONLY if novelty enabled
        if self.enable_novelty:
            self.trust_score = min(
                self.max_trust,
                self.trust_score + 1
            )

            self.expiry_window = self.base_expiry * self.trust_score

        # Timestamp ALWAYS update (protocol consistency)
        self.last_auth_time = time.time()

        return True

    # SR1 Sensor resynchronization
    def resync_request(self, server_obj):

        #  Lock check only if novelty enabled
        if self.enable_novelty and self.locked:
            raise ValueError("Locked device cannot resynchronize")

        u_s = random_scalar()
        TCs_new = self.TCssp ^ h(u_s, self.WT_s)

        return self.ID_s, u_s, TCs_new