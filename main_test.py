from ta import TrustedAuthority
from sensor import Sensor
from server import Server
from ecc_math import random_scalar, point_multiply
import time


def main():

   
    # registration phase (R1–R4)
    

    ta = TrustedAuthority()

    sensor_reg = ta.register_sensor("Sensor01")
    server_reg = ta.register_server("Server01")

    sensor = Sensor(sensor_reg, ta.r_ta)
    server = Server(server_reg, ta.r_ta)

    sensor.enable_novelty = False   # change to True for enhanced version
    server.enable_novelty = False

    # Mode label (for clarity in logs)
    if sensor.enable_novelty:
        print("Running Mode: ENHANCED protocol (with novelty)")
    else:
        print("Running Mode: ORIGINAL protocol (paper baseline)")

    sensor.complete_registration(server.PK_sp, server.ID_sp)
    server.complete_registration(sensor.PK_s, sensor.ID_s, sensor.TCssp)

    print("Registration completed successfully")

    # Authentication phase (A1–A4)
  

    A_s, ETCssp, Vs1 = sensor.authentication_step_A1()

    A_sp, V_sp, TC_new = server.authentication_step_A2_A3(
        A_s, ETCssp, Vs1, sensor
    )

    sensor.authentication_step_A4(A_sp, V_sp, server)

    print("Authentication completed successfully")
    print("Mutual authentication verified")

    # replay attack simulation
   

    print("\n Simulating Replay Attack")

    A_s_old = A_s
    ETCssp_old = ETCssp
    Vs1_old = Vs1

    try:
        server.authentication_step_A2_A3(A_s_old, ETCssp_old, Vs1_old, sensor)
        print("ERROR: Replay attack succeeded!")
    except Exception:
        print("Replay attack prevented successfully")

  
    # Impersonation Attack
   

    print("\n Simulating Impersonation Attack")

    fake_x = random_scalar()
    fake_A_s = point_multiply(fake_x, sensor.PK_s)
    fake_ETCssp = 123456
    fake_Vs1 = 78910

    try:
        server.authentication_step_A2_A3(
            fake_A_s,
            fake_ETCssp,
            fake_Vs1,
            sensor
        )
        print("ERROR: Impersonation attack succeeded!")
    except Exception:
        print("Impersonation attack prevented successfully")

   
    # MITM attack simulation
    

    print("\n Simulating MITM Attack")

    tampered_A_s = point_multiply(2, A_s)

    try:
        server.authentication_step_A2_A3(
            tampered_A_s,
            ETCssp,
            Vs1,
            sensor
        )
        print("ERROR: MITM attack succeeded!")
    except Exception:
        print("MITM attack prevented successfully")
 
    # Time bound expiry simulation
  


    print("\n Simulating Time Expiry")

    # Wait beyond expiry window
    time.sleep(sensor.expiry_window + 2)

    try:
        A_s_exp, ETC_exp, Vs1_exp = sensor.authentication_step_A1()
        server.authentication_step_A2_A3(A_s_exp, ETC_exp, Vs1_exp, sensor)
        print("ERROR: Expired DAC was accepted!")
    except Exception:
        print("Time-bound DAC prevented expired authentication successfully")

    
    # Desynchronization


    print("\n Simulating desynchronization")

    sensor.TCssp ^= 123456

    try:
        A_s2, ETCssp2, Vs12 = sensor.authentication_step_A1()
        server.authentication_step_A2_A3(A_s2, ETCssp2, Vs12, sensor)
        print("ERROR: Desynchronization NOT detected!")
    except Exception:
        print("Authentication failed as expected")
        print("Starting resynchronization")

        ID_s, u_s, TCs_new = sensor.resync_request(server)
        server.resync_process(ID_s, u_s, TCs_new, sensor)

        print("Resynchronization completed successfully")

        # verify authentication again
      

        print("\n Re-attempting authentication after resync")

        A_s3, ETCssp3, Vs13 = sensor.authentication_step_A1()
        A_sp3, V_sp3, TC_new3 = server.authentication_step_A2_A3(
            A_s3, ETCssp3, Vs13, sensor
        )
        sensor.authentication_step_A4(A_sp3, V_sp3, server)

        print("Authentication successful after resynchronization")
        print("System fully restored")


if __name__ == "__main__":
    main()