# Client code
import network
import ubinascii
import socket
import time



wifi = network.WLAN(network.STA_IF)

try:
    wifi.disconnect()
except:
    pass

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

# Connect the socket to the port where the server is listening
server_address = ('192.168.211.30', 1234)
print('Connecting to {} port {}'.format(*server_address))
sock.connect(server_address)

try:
    message = 'This is a message from ESP32 client.'
    print('Sending: {!r}'.format(message))
    sock.sendall(message)

    # Wait for the response
    amount_received = 0
    amount_expected = len(message)
    
    while amount_received < amount_expected:
        data = sock.recv(16)
        amount_received += len(data)
        print('Received: {!r}'.format(data))

finally:
    print('Closing socket')
    sock.close()