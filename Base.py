from ublox_gps import UbloxGps
import serial
import cv2
import socket
import pickle
from Arduino_methods import *
import tkinter


def get_coordinates(_gps):
    try:
        _coordinates = _gps.geo_coords()
        return {'longitude': _coordinates.lon, 'latitude': _coordinates.lat}
    except (ValueError, IOError) as err:
        return None


def get_frame():
    result, _image = cam.read()

    if result:
        return _image

    else:
        return None


def exit_program():
    # To do - Add exit process to client
    print("Bye bye.")
    exit()


# Set IMU configurations
available_ports = serial_ports()
arduino_connection = establish_connection(True, 115200, 'COM11')


header_size = 10
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostname()
print(f'\n\nEnter "{host}" in the host variable in the client side.')
s.bind((host, 1243))
s.listen(5)


# https://github.com/sparkfun/Qwiic_Ublox_Gps_Py
rtk_port = serial.Serial('COM8', baudrate=38400, timeout=1)
rtk = UbloxGps(rtk_port)
cam_port = 0
cam = cv2.VideoCapture(cam_port)


if __name__ == '__main__':
    if stable_the_ard() != 'bad_data':
        while True:
            clientsocket, address = s.accept()
            print(f"Connection from {address} has been established.")

            full_msg = b''
            new_msg = True
            while True:
                msg = clientsocket.recv(512)
                if new_msg:
                    msglen = int(msg[:header_size])
                    new_msg = False

                full_msg += msg

                if len(full_msg) - header_size == msglen:
                    data = pickle.loads(full_msg[header_size:])
                    new_msg = True
                    full_msg = b""

                if new_msg:
                    imu_data = get_imu_read()
                    base_coordinates = get_coordinates(rtk)
                    image = get_frame()

                    data['image'] = image
                    data['base_GPS'] = base_coordinates
                    data['base_IMU'] = imu_data

                    print(base_coordinates)
