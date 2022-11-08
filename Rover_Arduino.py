from ublox_gps import UbloxGps
import serial
import socket
import pickle
import sys
import glob
from serial import Serial
from serial import SerialException
from serial import serialutil
import struct
import time
from tqdm.auto import tqdm


def serial_ports():
    """ Lists serial port names
        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = Serial(port)
            s.close()
            result.append(port)
        except (OSError, SerialException):
            pass
    return result


def get_data_from_arduino():
    while True:
        if ard.inWaiting() > 0:
            current_data = ard.read(4)
            packet = struct.unpack('<f', current_data)[0]
            if abs(packet) > 1e+30:
                establish_connection(False, 115200, 'COM9')
            return packet


def get_data(show_raw_data):
    keys = ['Gyroscope', 'Accelerometer', 'Magnetometer']
    serial_keys = [1000001.0, 1000002.0, 1000003.0]
    all_imu_data = []

    for key in keys:
        current_data_for_sens_type = [key]
        counter = 0
        current_data = 0
        while current_data != serial_keys[keys.index(key)]:
            current_data = get_data_from_arduino()
            if show_raw_data:
                sys.stdout.write("\r" + f"Establishing connection, the current value read from the "
                                        f"controller is: {current_data}")
                sys.stdout.flush()
            if counter > 100:
                return None
            counter += 1
        for j in range(3):
            raw = get_data_from_arduino()
            current_data_for_sens_type.append(raw)
        all_imu_data.append(current_data_for_sens_type)

    # print(f'Got raw data\n{all_imu_data}\n\n')
    return all_imu_data


def establish_connection(show_raw_data, baud_rate, COM):
    counter = 0
    plural = ["attempts", "attempt"]
    while True:
        global ard
        try:
            ard = Serial(COM, baud_rate)
        except serialutil.SerialException:
            return "Connection to Arduino lost."
            # sys.exit(0)
            pass

        if get_data(show_raw_data) is not None:
            # print("\n\nConnection established, Data record will begin soon.\n")
            if counter == 1:
                return f'\nConnectivity report:\n' \
                       f'{counter} Failed {plural[1]} before establishing good connectivity to controller.\n'
            else:
                return f'\nConnectivity report:\n' \
                       f'{counter} Failed {plural[0]} before establishing good connectivity to controller.\n'
        ard.close()
        counter += 1


def stable_the_ard():
    temp_time = time.time()
    for i in tqdm(range(300)):
        a = get_data(False)
        delt = time.time() - temp_time
        temp_time = time.time()
    if delt > (1 / 20.0):
        return 'bad_data'


def get_imu_read():
    single_loop = []
    while len(single_loop) == 0:
        a = get_data(False)
        # print(f'Got a read from the arduino\n {a}\n\n')
        if isinstance(a, list):
            single_loop = {}
            for sensor in a:
                single_loop[sensor[0]] = {'x': sensor[1], 'y': sensor[2], 'z': sensor[3]}

    return single_loop


def get_coordinates(_rtk):
    try:
        _coordinates = _rtk.geo_coords()
        return {'longitude': _coordinates.lon, 'latitude': _coordinates.lat}
    except (ValueError, IOError) as err:
        return None


# Set client port for communication with laptop
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = 'DESKTOP-C60OGE1'
s.connect((host, 1243))
header_size = 10


# Set GPS-RTK configurations
# https://github.com/sparkfun/Qwiic_Ublox_Gps_Py
rtk_usb_port = serial.Serial('COM8', baudrate=38400, timeout=1)
rtk = UbloxGps(rtk_usb_port)

# Set IMU configurations
available_ports = serial_ports()
arduino_connection = establish_connection(True, 115200, available_ports[-1])


# Main loop
if stable_the_ard() != 'bad_data':
    while True:
        coordinates = get_coordinates(rtk)
        imu_data = get_imu_read()

        current_data = {'rover_GPS': coordinates, 'IMU': imu_data}
        print(coordinates)

        data_to_server = pickle.dumps(current_data)
        data_to_server = bytes(f"{len(data_to_server):<{header_size}}", 'utf-8') + data_to_server
        s.send(data_to_server)
