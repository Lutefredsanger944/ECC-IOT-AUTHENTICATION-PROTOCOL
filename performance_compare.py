import time
from ta import TrustedAuthority
from sensor import Sensor
from server import Server
from ecc_math import random_scalar, point_multiply
import matplotlib.pyplot as plt


ITERATIONS = 100  


def run_single_test(enable_novelty, enable_attack):

    start = time.time()

    for _ in range(ITERATIONS):

        # Setup
        ta = TrustedAuthority()

        sensor_reg = ta.register_sensor("Sensor01")
        server_reg = ta.register_server("Server01")

        sensor = Sensor(sensor_reg, ta.r_ta)
        server = Server(server_reg, ta.r_ta)

        # MODE CONTROL
        sensor.enable_novelty = enable_novelty
        server.enable_novelty = enable_novelty

        # Registration
        sensor.complete_registration(server.PK_sp, server.ID_sp)
        server.complete_registration(sensor.PK_s, sensor.ID_s, sensor.TCssp)

        # Authentication
        A_s, ETCssp, Vs1 = sensor.authentication_step_A1()
        A_sp, V_sp, _ = server.authentication_step_A2_A3(A_s, ETCssp, Vs1, sensor)
        sensor.authentication_step_A4(A_sp, V_sp, server)

        #  OPTIONAL ATTACK SIMULATION
        if enable_attack:

            try:
                # Replay
                server.authentication_step_A2_A3(A_s, ETCssp, Vs1, sensor)
            except:
                pass

            try:
                # Impersonation
                fake_x = random_scalar()
                fake_A = point_multiply(fake_x, sensor.PK_s)
                server.authentication_step_A2_A3(fake_A, 123, 456, sensor)
            except:
                pass

    end = time.time()

    return (end - start) / ITERATIONS


def main():

    print("\n===== PERFORMANCE COMPARISON =====\n")

    cases = [
        ("Original", False, False),
        ("Original + Attack", False, True),
        ("Enhanced", True, False),
        ("Enhanced + Attack", True, True),
    ]

    results = []

    for name, novelty, attack in cases:

        avg_time = run_single_test(novelty, attack)

        print(f"{name} → {avg_time:.6f} sec")

        results.append((name, avg_time))

    # GRAPH
    labels = [c[0] for c in cases]

    plt.figure()
    times = [t for _, t in results]
    plt.bar(labels, times)
    
    plt.xlabel("Protocol Configuration")
    plt.ylabel("Average Time (seconds)")
    plt.title("Performance Comparison of IoT Authentication Protocol")

    plt.xticks(rotation=20)

    plt.tight_layout()
    plt.savefig("results/performance_graph.png")
    for name, t in results:
        print(f"{name:40} : {t:.6f} sec")


if __name__ == "__main__":
    main()