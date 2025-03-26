# Raspberry Pi MPU6050 Real-Time Dashboard

This project provides a real-time web dashboard for monitoring data from an MPU6050 accelerometer/gyroscope sensor connected to a Raspberry Pi 4B.

## Features

- Real-time visualization of accelerometer and gyroscope data
- 3D visualization of sensor orientation
- Temperature monitoring
- Historical data charting
- Responsive web interface accessible from any device on the network

## Hardware Requirements

- Raspberry Pi 4B
- MPU6050 sensor module
- Jumper wires

## Software Requirements

- Python 3.7+
- Flask
- Flask-SocketIO
- smbus2

## Hardware Connection

Connect the MPU6050 to the Raspberry Pi as follows:

| MPU6050 Pin | Raspberry Pi Pin |
|-------------|------------------|
| VCC         | 3.3V (Pin 1)     |
| GND         | Ground (Pin 6)   |
| SCL         | SCL (Pin 5)      |
| SDA         | SDA (Pin 3)      |

## Installation

1. Enable I2C on your Raspberry Pi:
   ```
   sudo raspi-config
   ```
   Navigate to "Interface Options" > "I2C" > "Yes" to enable I2C.

2. Install required system packages:
   ```
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-smbus i2c-tools
   ```

3. Check if the sensor is detected:
   ```
   sudo i2cdetect -y 1
   ```
   You should see a device at address 0x68 (the default address for MPU6050).

4. Clone this repository:
   ```
   git clone https://github.com/yourusername/rpi-mpu6050-dashboard.git
   cd rpi-mpu6050-dashboard
   ```

5. Install Python dependencies:
   ```
   pip3 install -r requirements.txt
   ```

6. Create project structure:
   ```
   mkdir -p static templates
   ```

7. Create the following files with the provided code:
   - `app.py` - Main Python application
   - `templates/index.html` - Dashboard HTML template
   - `static/dashboard.js` - Dashboard JavaScript code

## Running the Application

1. Start the application:
   ```
   python3 app.py
   ```

2. Access the dashboard by navigating to `http://[raspberry_pi_ip]:5000` in a web browser from any device on the same network.

## Project Structure

```
rpi-mpu6050-dashboard/
├── app.py              # Main Python application
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Dashboard HTML template
└── static/
    └── dashboard.js    # Dashboard JavaScript
```

## Requirements.txt Content

```
flask==2.0.1
flask-socketio==5.1.1
smbus2==0.4.1
```

## Customization

- To change the sampling rate, modify the `time.sleep()` value in the `read_sensor()` function in `app.py`.
- To adjust the accelerometer or gyroscope sensitivity, modify the scale values in the `read_raw_data()` function.
- To customize the dashboard appearance, edit the HTML and CSS in `templates/index.html`.

## Troubleshooting

- If the sensor is not detected, check your wiring connections and ensure I2C is enabled.
- If the web interface shows "Disconnected", check that the Flask application is running on the Raspberry Pi.
- If data values seem incorrect, you may need to calibrate your sensor.

## License

This project is released under the MIT License.

## Credits

- [Flask](https://flask.palletsprojects.com/)
- [Socket.IO](https://socket.io/)
- [Three.js](https://threejs.org/)
- [Chart.js](https://www.chartjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)