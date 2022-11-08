from ublox_gps import UbloxGps
import serial
import socket
import pickle
from Arduino_methods import *


def get_coordinates(_rtk):
    try:
        _coordinates = _rtk.geo_coords()
        return {'longitude': _coordinates.lon, 'latitude': _coordinates.lat}
    except (ValueError, IOError) as err:
        return None


def listen_to_server(server):
    full_msg = b''
    new_msg = True
    while True:
        msg = server.recv(259)
        if new_msg:
            msglen = int(msg[:header_size])
            new_msg = False

        full_msg += msg
        if len(full_msg) - header_size == msglen:
            data = pickle.loads(full_msg[header_size:])
            new_msg = True
            full_msg = b""

        if new_msg:
            return data


def talk_to_server(data):
    data_to_server = pickle.dumps(data)
    data_to_server = bytes(f"{len(data_to_server):<{header_size}}", 'utf-8') + data_to_server
    s.send(data_to_server)
    print(f'Message length: {len(data_to_server)}')


def exit_program():
    talk_to_server('client left')
    s.close()
    rtk_usb_port.close()
    close_connection()
    exit()


# Set IMU configurations
# available_ports = serial_ports()
arduino_connection = establish_connection(True, 115200, 'COM9')

# Set client port for communication with laptop
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = 'DESKTOP-C60OGE1'
s.connect((host, 1243))
header_size = 10

# Set GPS-RTK configurations
# https://github.com/sparkfun/Qwiic_Ublox_Gps_Py
rtk_usb_port = serial.Serial('COM11', baudrate=38400, timeout=1)
rtk = UbloxGps(rtk_usb_port)

# Main loop
if stable_the_ard() != 'bad_data':
    talk_to_server('Ready')
    while True:
        server_msg = listen_to_server(s)

        if server_msg == 'Capture':
            coordinates = get_coordinates(rtk)
            imu_data = get_imu_read()

            current_data = {'rover_GPS': coordinates, 'rover_IMU': imu_data}

            talk_to_server(current_data)
            print(coordinates)
            print(imu_data)
            print("_________________________________________________________________________")

        if server_msg == 'Stop':
            exit_program()
