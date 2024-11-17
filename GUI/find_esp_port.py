import serial.tools.list_ports

def find_esp_port():
    ports = serial.tools.list_ports.comports()
    for port, desc, _ in sorted(ports):
        if desc != 'n/a':
            print(desc)


if __name__ == '__main__':
    find_esp_port()
