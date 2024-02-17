import os
import time
import serial
import cv2
from spot_controller import SpotController

ROBOT_IP = "10.0.0.3"
SPOT_USERNAME = "admin"
SPOT_PASSWORD = "asdfadsf"

class ArduinoSerialCommunicator:
    def __init__(self, port="/dev/ttyTHS1", baudrate=9600):
        self.serial_port = serial.Serial(port=port, baudrate=baudrate, timeout=0.5)
        time.sleep(1)  # Wait for port initialization

    def send_message(self, message):
        print("Sending:", message)
        message += "\n"6t
        for char in message:
            self.serial_port.write(char.encode('utf-8'))
            time.sleep(0.1)

    def receive_message(self):
        message = ""
        while True:
            if self.serial_port.inWaiting() > 0:
                data = self.serial_port.read()
                message += data.decode('utf-8')
                if data == b"\n":
                    break
        return message

    def close(self):
        self.serial_port.close()

def main():
    arduino_communicator = ArduinoSerialCommunicator()

    #example of using micro and speakers
    print("Start recording audio")
    sample_name = "aaaa.wav"
    cmd = f'arecord -vv --format=cd --device={os.environ["AUDIO_INPUT_DEVICE"]} -r 48000 --duration=10 -c 1 {sample_name}'
    print(cmd)
    os.system(cmd)
    print("Playing sound")
    os.system(f"ffplay -nodisp -autoexit -loglevel quiet {sample_name}")

    # Capture image
    camera_capture = cv2.VideoCapture(0)
    rv, image = camera_capture.read()
    print(f"Image Dimensions: {image.shape}")
    camera_capture.release()

    # Use wrapper in context manager to lease control, turn on E-Stop, power on the robot and stand up at start
    # and to return lease + sit down at the end
    with SpotController(username=SPOT_USERNAME, password=SPOT_PASSWORD, robot_ip=ROBOT_IP) as spot:
        time.sleep(2)

        spot.move_head_in_points(yaws=[0.2, 0], pitches=[0.3, 0], rolls=[0.4, 0], sleep_after_point_reached=1)
        time.sleep(3)


        arduino_communicator.send_message("Test Message")
        response = arduino_communicator.receive_message()
        print("Received from Arduino:", response)


    arduino_communicator.close()

if __name__ == '__main__':
    main()