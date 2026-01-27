import multiprocessing as mp
import time

from src.mqtt_worker import mqtt_main
from src.gpio_worker import gpio_main


def main():

    # queue for incoming commands
    command_queue = mp.Queue()
    # queue for outgoing telemetry data
    telemetry_queue = mp.Queue()

    # two processes for gpio and mqtt workers
    p_mqtt = mp.Process(target=mqtt_main, args=(command_queue, telemetry_queue))
    p_gpio = mp.Process(target=gpio_main, args=(command_queue, telemetry_queue))

    # start the processes
    p_mqtt.start()
    p_gpio.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        p_mqtt.terminate()
        p_gpio.terminate()

if __name__ == "__main__":
    main()
