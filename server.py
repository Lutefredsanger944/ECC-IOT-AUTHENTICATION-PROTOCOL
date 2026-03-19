from ecc_math import (
    random_scalar,
    point_multiply,
    scalar_mod_q
)
from hash_functions import h
import time


class Server:

    # initialization
    def __init__(self, reg_data, r_ta):

        self.ID_sp = reg_data["ID_sp"]
        self.r_sp = reg_data["r_sp"]
        self.PK_sp = reg_data["PK_sp"]

        self.enable_novelty = True
        self.enable_attack_handling = True

        # k_sp = (r_sp + r_ta) mod q
        self.k_sp = scalar_mod_q(self.r_sp + r_ta)

        self.WT_sp = None
        self.ID_s = None

        self.prTCssp = None

        self.x_sp = None
        self.A_sp = None

    # Complete Registration
    def complete_registration(self, sensor_PK_s, ID_s, TCssp):

        self.ID_s = ID_s
        self.prTCssp = TCssp

        self.WT_sp = point_multiply(self.k_sp, sensor_PK_s)

    # A2 + A3 — server authentication process
    def authentication_step_A2_A3(self, A_s, ETCssp, Vs1, sensor_obj):

        current_time = time.time()

        # Device lock (ONLY if novelty ON)
        if self.enable_novelty and sensor_obj.locked:
            raise ValueError("Sensor device is locked due to low trust")

        # Expiry (ONLY if novelty ON)
        if self.enable_novelty:
            if current_time - sensor_obj.last_auth_time > sensor_obj.expiry_window:

                sensor_obj.trust_score = max(
                    sensor_obj.min_trust,
                    sensor_obj.trust_score - 1
                )

                if sensor_obj.trust_score <= sensor_obj.min_trust:
                    sensor_obj.locked = True

                raise ValueError("Time-bound DAC expired")

        # Recover TC (CORE LOGIC — DO NOT TOUCH)
        recovered_TC = ETCssp ^ h(A_s, self.WT_sp)

        if recovered_TC != self.prTCssp:

            if self.enable_novelty:
                sensor_obj.trust_score = max(
                    sensor_obj.min_trust,
                    sensor_obj.trust_score - 1
                )

                if sensor_obj.trust_score <= sensor_obj.min_trust:
                    sensor_obj.locked = True

            raise ValueError("TC mismatch — desynchronization detected")

        # Verify Vs1 (CORE LOGIC)
        expected_Vs1 = h(
            self.ID_s,
            self.prTCssp,
            A_s,
            self.WT_sp
        )

        if expected_Vs1 != Vs1:

            if self.enable_novelty:
                sensor_obj.trust_score = max(
                    sensor_obj.min_trust,
                    sensor_obj.trust_score - 1
                )

                if sensor_obj.trust_score <= sensor_obj.min_trust:
                    sensor_obj.locked = True

            raise ValueError("Vs1 verification failed")

        # AUTH CONTINUES 

        self.x_sp = random_scalar()
        self.A_sp = point_multiply(self.x_sp, self.PK_sp)

        temp = point_multiply(self.k_sp, A_s)
        SK_sp = point_multiply(self.x_sp, temp)

        SSK = h(self.ID_s, self.ID_sp, SK_sp)

        TC_new = self.prTCssp ^ h(SK_sp, self.A_sp)

        V_sp = h(
            self.WT_sp,
            self.ID_s,
            TC_new,
            self.A_sp,
            SSK
        )

        #  Trust update (ONLY if novelty ON)
        if self.enable_novelty:
            sensor_obj.trust_score = min(
                sensor_obj.max_trust,
                sensor_obj.trust_score + 1
            )

            sensor_obj.expiry_window = (
                sensor_obj.base_expiry * sensor_obj.trust_score
            )

        # CORE (always)
        self.prTCssp = TC_new

        return self.A_sp, V_sp, TC_new

    # SR2 — server resynchronization
    def resync_process(self, ID_s, u_s, TCs_new, sensor_obj):

        recovered_TC = TCs_new ^ h(u_s, self.WT_sp)

        self.prTCssp = recovered_TC

        #  Only novelty-related reset
        if self.enable_novelty:
            sensor_obj.locked = False

            sensor_obj.trust_score = max(
                3,
                sensor_obj.trust_score
            )

            sensor_obj.expiry_window = (
                sensor_obj.base_expiry * sensor_obj.trust_score
            )

        sensor_obj.last_auth_time = time.time()

        confirmation = h(self.ID_sp, ID_s, recovered_TC)

        return confirmation