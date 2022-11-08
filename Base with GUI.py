from ublox_gps import UbloxGps
import serial
import cv2
import socket
import pickle
from Arduino_methods import *
from tkinter import *
from PIL import ImageTk, Image
from tkinter import ttk
import os


def save_data():
    global data, save_path

    if isinstance(data, dict):
        save_dir = save_path.get()

        try:
            file_name = os.path.join(save_dir, f"{int(time.time())}.pkl")
            with open(file_name, 'wb') as outp:  # Overwrites any existing file.
                pickle.dump(data, outp, pickle.HIGHEST_PROTOCOL)

        except FileNotFoundError:
            print("Enter a valid save directory path.")

    else:
        print('Capture data first...')


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
    data_to_server = pickle.dumps('Stop')
    data_to_server = bytes(f"{len(data_to_server):<{header_size}}", 'utf-8') + data_to_server
    clientsocket.send(data_to_server)

    rtk_port.close()
    close_connection()
    cam.release()
    if get_msg() == 'client left':
        sock.close()

    print("Bye bye.")
    exit()


def get_msg():
    global data, clientsocket, header_size
    full_msg = b''
    new_msg = True
    while True:
        msg = clientsocket.recv(259)
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


def capture_data():
    global data, clientsocket, header_size

    data_to_server = pickle.dumps('Capture')
    data_to_server = bytes(f"{len(data_to_server):<{header_size}}", 'utf-8') + data_to_server
    clientsocket.send(data_to_server)
    data = get_msg()

    print(data)
    imu_data = get_imu_read()
    print(imu_data)
    base_coordinates = get_coordinates(rtk)
    print(base_coordinates)
    image = get_frame()
    print(len(image))

    data['image'] = image
    data['base_GPS'] = base_coordinates
    data['base_IMU'] = imu_data

    update_shown_data()


def calculate_relative_imu(rover_imu, base_imu):
    relative_imu = {}.fromkeys(rover_imu)

    for sensor in relative_imu:
        relative_imu[sensor] = {}.fromkeys(rover_imu[sensor])
        for axis in relative_imu[sensor]:
            relative_imu[sensor][axis] = rover_imu[sensor][axis] - base_imu[sensor][axis]

    return relative_imu


def update_imu(rover_imu, base_imu):
    imu = calculate_relative_imu(rover_imu, base_imu)

    accelerometer_x.delete(0, END)
    accelerometer_x.insert(END, str(round(imu['Accelerometer']['x'], 3)))
    accelerometer_y.delete(0, END)
    accelerometer_y.insert(END, str(round(imu['Accelerometer']['y'], 3)))
    accelerometer_z.delete(0, END)
    accelerometer_z.insert(END, str(round(imu['Accelerometer']['z'], 3)))

    gyroscope_x.delete(0, END)
    gyroscope_x.insert(END, str(round(imu['Gyroscope']['x'], 3)))
    gyroscope_y.delete(0, END)
    gyroscope_y.insert(END, str(round(imu['Gyroscope']['y'], 3)))
    gyroscope_z.delete(0, END)
    gyroscope_z.insert(END, str(round(imu['Gyroscope']['z'], 3)))

    magnetometer_x.delete(0, END)
    magnetometer_x.insert(END, str(round(imu['Magnetometer']['x'], 3)))
    magnetometer_y.delete(0, END)
    magnetometer_y.insert(END, str(round(imu['Magnetometer']['y'], 3)))
    magnetometer_z.delete(0, END)
    magnetometer_z.insert(END, str(round(imu['Magnetometer']['z'], 3)))


def update_gps_rtk(rover_gps):
    latitude.delete(0, END)
    latitude.insert(END, str(round(rover_gps['latitude'], 3)))

    longitude.delete(0, END)
    longitude.insert(END, str(round(rover_gps['longitude'], 3)))


def update_image(image):
    global img, panel

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(image).convert('RGB')
    img = img.resize((int(0.6 * 640), int(0.6 * 480)))
    img = ImageTk.PhotoImage(img)
    panel.configure(image=img)


def update_shown_data():
    global data

    rover_imu = data['rover_IMU']
    base_imu = data['base_IMU']

    image = data['image']

    rover_gps = data['rover_GPS']
    base_gps = data['base_GPS']

    update_imu(rover_imu, base_imu)
    update_gps_rtk(rover_gps)
    update_image(image)


if __name__ == '__main__':
    # Set IMU configurations
    # available_ports = serial_ports()
    arduino_connection = establish_connection(True, 115200, 'COM11')

    header_size = 10
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostname()
    print(f'\n\nEnter "{host}" in the host variable in the client side.')
    sock.bind((host, 1243))
    sock.listen(5)

    # https://github.com/sparkfun/Qwiic_Ublox_Gps_Py
    rtk_port = serial.Serial('COM8', baudrate=38400, timeout=1)
    rtk = UbloxGps(rtk_port)
    cam_port = 0
    cam = cv2.VideoCapture(cam_port)

    if stable_the_ard() != 'bad_data':
        clientsocket, address = sock.accept()
        print(f"Connection from {address} has been established.")

    data = None

    master = Tk()
    bg_color = 'white'
    master.configure(bg=bg_color)
    master.attributes("-fullscreen", True)
    style = ttk.Style()
    style.theme_names()
    ('clam', 'alt', 'default', 'classic')
    style.theme_use('clam')

    master.title('Pointing dataset collector V1.0')
    master.resizable(width=True, height=True)
    entry_width = 10
    #################################################################################################################
    text = '  Welcome to the pointing dataset collector control panel.\n\n' \
           "  Capture - Obtain data from moving target (GPS-RTK & IMU).\n" \
           "  Save - If the captured data if suitable, save it to a desired folder.\n" \
           "  Exit - Exit the program.\n\n"
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=0, column=1, columnspan=7, rowspan=6)

    img = Image.open(r'C:\Users\kahan\PycharmProjects\GPS_RTK\ROBTAU.png')
    img = img.resize((int(0.6 * 640), int(0.6 * 480)))
    img = ImageTk.PhotoImage(img)
    panel = Label(master, image=img, anchor="e", justify=LEFT, bg=bg_color)
    panel.grid(row=1, column=0, columnspan=1)
    #################################################################################################################
    tab_text = "___________________________________________________________________________________________________" \
               "___________________________________________________________________________________________________" \
               "\nIMU Data:\n"
    Label(master, text=tab_text, anchor="n", justify=LEFT, bg=bg_color).grid(row=2, column=0, columnspan=8)
    #################################################################################################################
    text = 'Accelerometer [g]:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=3, column=1, columnspan=1)
    #################################################################################################################
    text = 'X:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=4, column=2, columnspan=1)
    accelerometer_x = Entry(master, width=20)
    accelerometer_x.insert(END, str(0))
    accelerometer_x.grid(row=4, column=3, columnspan=1)

    text = 'Y:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=4, column=4, columnspan=1)
    accelerometer_y = Entry(master, width=20)
    accelerometer_y.insert(END, str(0))
    accelerometer_y.grid(row=4, column=5, columnspan=1)

    text = 'Z:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=4, column=6, columnspan=1)
    accelerometer_z = Entry(master, width=20)
    accelerometer_z.insert(END, str(0))
    accelerometer_z.grid(row=4, column=7, columnspan=1)
    #################################################################################################################
    text = 'Gyroscope [deg/sec]:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=5, column=1, columnspan=1)
    #################################################################################################################
    text = 'X:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=6, column=2)
    gyroscope_x = Entry(master, width=20)
    gyroscope_x.insert(END, str(0))
    gyroscope_x.grid(row=6, column=3, columnspan=1)

    text = 'Y:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=6, column=4)
    gyroscope_y = Entry(master, width=20)
    gyroscope_y.insert(END, str(0))
    gyroscope_y.grid(row=6, column=5)

    text = 'Z:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=6, column=6)
    gyroscope_z = Entry(master, width=20)
    gyroscope_z.insert(END, str(0))
    gyroscope_z.grid(row=6, column=7)
    #################################################################################################################
    text = 'Magnetometer [Gauss]:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=7, column=1, columnspan=1)
    #################################################################################################################
    text = 'X:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=8, column=2)
    magnetometer_x = Entry(master, width=20)
    magnetometer_x.insert(END, str(0))
    magnetometer_x.grid(row=8, column=3, columnspan=1)

    text = 'Y:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=8, column=4)
    magnetometer_y = Entry(master, width=20)
    magnetometer_y.insert(END, str(0))
    magnetometer_y.grid(row=8, column=5)

    text = 'Z:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=8, column=6)
    magnetometer_z = Entry(master, width=20)
    magnetometer_z.insert(END, str(0))
    magnetometer_z.grid(row=8, column=7)
    #################################################################################################################
    tab_text = "___________________________________________________________________________________________________" \
               "___________________________________________________________________________________________________" \
               "\nGPS-RTK Data:\n"
    Label(master, text=tab_text, anchor="n", justify=LEFT, bg=bg_color).grid(row=9, column=0, columnspan=8)
    #################################################################################################################
    text = 'Latitude:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=10, column=2)
    latitude = Entry(master, width=20)
    latitude.insert(END, str(0))
    latitude.grid(row=10, column=3, columnspan=1)

    text = 'Longitude:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=10, column=4)
    longitude = Entry(master, width=20)
    longitude.insert(END, str(0))
    longitude.grid(row=10, column=5)
    #################################################################################################################
    tab_text = "___________________________________________________________________________________________________" \
               "___________________________________________________________________________________________________\n\n"
    Label(master, text=tab_text, anchor="n", justify=LEFT, bg=bg_color).grid(row=11, column=0, columnspan=8)
    #################################################################################################################
    text = 'Save path:'
    Label(master, text=text, anchor="n", justify=LEFT, bg=bg_color).grid(row=12, column=0)
    save_path = Entry(master, width=50)
    save_path.insert(END, r'C:\Users\kahan\PycharmProjects\GPS_RTK\data')
    save_path.grid(row=12, column=1, columnspan=2)

    save_button = ttk.Button(master, text='Save', command=save_data)
    save_button.grid(row=12, column=5, columnspan=1)

    capture_button = ttk.Button(master, text='Capture', command=capture_data)
    capture_button.grid(row=12, column=6, columnspan=1)

    exit_button = ttk.Button(master, text='Exit', command=exit_program)
    exit_button.grid(row=12, column=7, columnspan=1)
    if get_msg() == 'Ready':
        mainloop()
