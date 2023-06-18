# Server code
import network
import ubinascii
import socket
import time

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

# Connect to WiFi network
while not wifi.isconnected():
    try:
        wifi.connect("SSID", "PASS")
        print('Connecting to the WiFi network...')
        time.sleep(5)
    except:
        print('Could not connect to the WiFi network. Retrying...')
        pass

print('Connected to WiFi network')
print('WiFi details:', wifi.ifconfig())

# Get the MAC address
mac_address = ubinascii.hexlify(wifi.config('mac'),':').decode()
print('MAC address:', mac_address)

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('0.0.0.0', 1234)
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

print("Listening for the other device...")

while True:
    conn, addr = sock.accept()
    print('Connected by', addr)

    while True:
        data = conn.recv(1024)
        print(data.decode())
        if not data: break
        conn.sendall(data)
    conn.close()
