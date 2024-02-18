import os
import time
import serial
import cv2
from spot_controller import SpotController
import socket
from flask import Flask, Response

ROBOT_IP = "10.0.0.3"
SPOT_USERNAME = "admin"
SPOT_PASSWORD = "2zqa8dgw7lor"

app = Flask(__name__)

def gen_frames():
    camera_capture = cv2.VideoCapture(0)  # Use the first camera
    while True:
        success, frame = camera_capture.read()  # Read the camera frame
        if not success:
            break
        else:
            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    # This route returns response that streams the camera feed
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# def get_container_ip():
#     try:
#         # Create a socket
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         # Use Google's Public DNS server to find the best route
#         # This does not actually create a connection
#         s.connect(("8.8.8.8", 80))
#         # Get the socket's own address
#         ip_address = s.getsockname()[0]
#         s.close()
#     except Exception as e:
#         ip_address = "Unable to determine IP address"
#     return ip_address

# # Print the container's IP address
# print(f"Container IP Address: {get_container_ip()}")


class ArduinoSerialCommunicator:
    def __init__(self, port="/dev/ttyTHS1", baudrate=4800, spot_controller=None):
        self.serial_port = serial.Serial(port=port, baudrate=baudrate, timeout=0.5)
        self.spot_controller = spot_controller  # SpotController instance
        time.sleep(1)  # Wait for port initialization

    def listen_for_commands(self, duration=30):
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.serial_port.inWaiting() > 0:
                incoming_message = self.serial_port.readline().decode('utf-8').strip()
                print(f"Received: {incoming_message}")

                # Execute Spot commands based on the incoming message
                if self.spot_controller:
                    if incoming_message == "STEP_FORWARD":
                        print("Moving forward...")
                        # Small positive velocity to move forward, with a short duration
                        self.spot_controller.move_by_velocity_control(v_x=0.1, v_y=0.0, v_rot=0.0, cmd_duration=0.5)
                        time.sleep(0.5)


                    elif incoming_message == "STEP_BACK":
                        print("Moving backward...")
                        # Small negative velocity to move backward, with a short duration
                        self.spot_controller.move_by_velocity_control(v_x=-0.1, v_y=0.0, v_rot=0.0, cmd_duration=0.5)
                        time.sleep(0.5)

                    elif incoming_message == "TURN_LEFT":
                        print("Turning left...")
                        # Small positive rotational velocity to turn left, with a short duration
                        self.spot_controller.move_by_velocity_control(v_x=0.0, v_y=0.0, v_rot=0.1, cmd_duration=0.5)
                        time.sleep(0.5)

                    elif incoming_message == "TURN_RIGHT":
                        print("Turning right...")
                        # Small negative rotational velocity to turn right, with a short duration
                        self.spot_controller.move_by_velocity_control(v_x=0.0, v_y=0.0, v_rot=-0.1, cmd_duration=0.5)
                        time.sleep(0.5)

                # Handle other Arduino-specific commands as needed
                elif incoming_message == "SPIN":
                    print("Spinning...")
                    # Add code for spin action here
                elif incoming_message == "STOP":
                    print("Stopping...")
                    # Add code for stop action here

            time.sleep(0.1)  # Small delay to prevent high CPU usage

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
    # arduino_communicator = ArduinoSerialCommunicator()

    # app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)

    #example of using micro and speakers
    # print("Start recording audio")
    # sample_name = "aaaa.wav"
    # cmd = f'arecord -vv --format=cd --device={os.environ["AUDIO_INPUT_DEVICE"]} -r 48000 --duration=10 -c 1 {sample_name}'
    # print(cmd)
    # os.system(cmd)
    # print("Playing sound")
    # os.system(f"ffplay -nodisp -autoexit -loglevel quiet {sample_name}")

    # # Capture image
    # camera_capture = cv2.VideoCapture(0)
    # rv, image = camera_capture.read()
    # print(f"Image Dimensions: {image.shape}")
    # camera_capture.release()


    # Use wrapper in context manager to lease control, turn on E-Stop, power on the robot and stand up at start
    # and to return lease + sit down at the end
    # with SpotController(username=SPOT_USERNAME, password=SPOT_PASSWORD, robot_ip=ROBOT_IP) as spot:
    #     time.sleep(2)

    #     spot.move_head_in_points(yaws=[0.2, 0], pitches=[0.3, 0], rolls=[0.4, 0], sleep_after_point_reached=1)
    #     time.sleep(3)


    #     arduino_communicator.send_message("Test Message")
    #     response = arduino_communicator.receive_message()
    #     print("Received from Arduino:", response)
    # get_container_ip()

    # for _ in range(10):
    #     arduino_communicator.send_message("SPIN")
    #     response = arduino_communicator.receive_message()
    #     print("Received from Arduino:", response)
    #     time.sleep(1)  # Wait for a second before the next iteration
    #     arduino_communicator.send_message("STOP")
    #     response = arduino_communicator.receive_message()
    #     print("Received from Arduino:", response)
    #     time.sleep(1)

    # arduino_communicator.listen_for_commands(30)  # Listen for commands for 30 seconds
    # arduino_communicator.close()

    with SpotController(username=SPOT_USERNAME, password=SPOT_PASSWORD, robot_ip=ROBOT_IP) as spot:
        arduino_communicator = ArduinoSerialCommunicator(spot_controller=spot)
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)
        arduino_communicator.listen_for_commands(30)
        arduino_communicator.close()


if __name__ == '__main__':
    main()