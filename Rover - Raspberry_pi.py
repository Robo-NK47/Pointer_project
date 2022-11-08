from ublox_gps import UbloxGps
import serial
import time
import socket
import pickle
import smbus


def IMU_setup():
    bus = smbus.SMBus(1)
    # enable gyroscope
    bus.write_byte_data(0x6B, 0x10, 0b11000011)

    # enable accelerometer
    bus.write_byte_data(0x6B, 0x20, 0b11000110)

    # enable magnetometer
    bus.write_byte_data(0x1E, 0x20, 0b11111100)
    bus.write_byte_data(0x1E, 0x21, 0b00000000)
    bus.write_byte_data(0x1E, 0x22, 0b00000000)
    bus.write_byte_data(0x1E, 0x23, 0b00001100)
    return bus


def twos_complement(val, bits):
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val


def get_gyro_data(_bus):
    out_x_g_l = _bus.read_byte_data(0x6B, 0x18)
    out_x_g_h = _bus.read_byte_data(0x6B, 0x19) - 0xf0
    out_x_g = twos_complement((out_x_g_h << 8) | out_x_g_l, 12) / 1e3

    out_y_g_l = _bus.read_byte_data(0x6B, 0x1A)
    out_y_g_h = _bus.read_byte_data(0x6B, 0x1B) - 0xf0
    out_y_g = twos_complement((out_y_g_h << 8) | out_y_g_l, 12) / 1e3

    out_z_g_l = _bus.read_byte_data(0x6B, 0x1C)
    out_z_g_h = _bus.read_byte_data(0x6B, 0x1D) - 0xf0
    out_z_g = twos_complement((out_z_g_h << 8) | out_z_g_l, 12) / 1e3
    return {'x': out_x_g, 'y': out_y_g, 'z': out_z_g}


def get_accelerometer_data(_bus):
    out_x_xl_l = _bus.read_byte_data(0x6B, 0x28)
    out_x_xl_h = _bus.read_byte_data(0x6B, 0x29)
    out_x_xl = twos_complement((out_x_xl_h << 8) | out_x_xl_l, 12) / 1e3

    out_y_xl_l = _bus.read_byte_data(0x6B, 0x2A)
    out_y_xl_h = _bus.read_byte_data(0x6B, 0x2B)
    out_y_xl = twos_complement((out_y_xl_h << 8) | out_y_xl_l, 12) / 1e3

    out_z_xl_l = _bus.read_byte_data(0x6B, 0x2C)
    out_z_xl_h = _bus.read_byte_data(0x6B, 0x2D)
    out_z_xl = twos_complement((out_z_xl_h << 8) | out_z_xl_l, 12) / 1e3

    return {'x': out_x_xl, 'y': out_y_xl, 'z': out_z_xl}


def get_magnetometer_data(_bus):
    out_x_m_l = _bus.read_byte_data(0x1E, 0x28)
    out_x_m_h = _bus.read_byte_data(0x1E, 0x29)
    out_x_m = twos_complement((out_x_m_h << 8) | out_x_m_l, 12) / 1e3

    out_y_m_l = _bus.read_byte_data(0x1E, 0x2A)
    out_y_m_h = _bus.read_byte_data(0x1E, 0x2B)
    out_y_m = twos_complement((out_y_m_h << 8) | out_y_m_l, 12) / 1e3

    out_z_m_l = _bus.read_byte_data(0x1E, 0x2C)
    out_z_m_h = _bus.read_byte_data(0x1E, 0x2D)
    out_z_m = twos_complement((out_z_m_h << 8) | out_z_m_l, 12) / 1e3

    return {'x': out_x_m, 'y': out_y_m, 'z': out_z_m}


def get_coordinates(_rtk):
    try:
        _coordinates = _rtk.geo_coords()
        return {'longitude': _coordinates.lon, 'latitude': _coordinates.lat}
    except (ValueError, IOError) as err:
        return None


def get_imu_read(_bus):
    return {'gyroscope': get_gyro_data(_bus),
            'accelerometer': get_accelerometer_data(_bus),
            'magnetometer': get_magnetometer_data(_bus)}


# Set client port for communication with laptop
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = 'DESKTOP-C60OGE1'
s.connect((host, 1243))
header_size = 10


# Set GPS-RTK configurations
# https://github.com/sparkfun/Qwiic_Ublox_Gps_Py
rtk_usb_port = serial.Serial('/dev/ttyACM0', baudrate=38400, timeout=1)
rtk = UbloxGps(rtk_usb_port)

# Set IMU configurations
imu_bus = IMU_setup()


if __name__ == '__main__':
    while True:
        coordinates = get_coordinates(rtk)
        imu_data = get_imu_read()

        current_data = {'rover_GPS': coordinates, 'IMU': imu_data}
        print(coordinates)

        data_to_server = pickle.dumps(current_data)
        data_to_server = bytes(f"{len(data_to_server):<{header_size}}", 'utf-8') + data_to_server
        s.send(data_to_server)
