import serial

# Define your COM port and baud rate
ser = serial.Serial('COM7', 9600)  # Change 'COM3' to your actual port (e.g., '/dev/ttyUSB0' on Linux/Mac)

def red_led_triggered():
    print("Red LED is ON – custom function called!")

print("Listening to Arduino...")

while True:
    if ser.in_waiting:
        line = ser.readline().decode().strip()
        print(f"Received: {line}")

        if line == '3':
            red_led_triggered()
