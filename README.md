# ReflectOS: Smart Mirror & Caregiver Companion

**ReflectOS** is an innovative hybrid IoT ecosystem designed to support independent living for elderly or less mobile individuals. By combining advanced computer vision, environmental sensing, and cloud connectivity, ReflectOS transforms a standard mirror into a proactive "Caregiver Companion," ensuring safety and connectivity from the comfort of the user's home.

## Key Features

- **Remote Biometric Enrollment**: Caregivers can securely register users remotely by uploading a selfie via the mobile app, which instantly trains the mirror's local AI.
- **"The Wind Guardian"**: An autonomous climate control system that monitors room temperature in real-time and automatically triggers cooling fans if conditions become unsafe.
- **"The Puppeteer" Communication**: Family members can send text messages via the app that are spoken aloud and displayed on the mirror to ensure vital reminders are noticed.
- **Non-Intrusive Monitoring**: A "Wellness Dashboard" allows caregivers to track room temperature, humidity, and activity logs without using invasive video cameras.

## Hardware Architecture

The ReflectOS system is built around a central processing unit and peripheral modules that ensure intelligent interaction and environmental control:

| **Unit** | **Hardware Components** | **Primary Function** |
| :--- | :--- | :--- |
| **Unit A: Computing Core** | Raspberry Pi 4 Model B (4GB/8GB) | Runs the Node.js display interface and Python AI logic. |
| **Unit B: Visual Interface** | Monitor Panel, Two-Way Acrylic Mirror | Displays the "Glass UI" (Clock, News, Alerts) to the user. |
| **Unit C: Sensing Array** | BME280 Sensor, Pi Camera Module V2 | Captures environmental data (Temp/Humidity) and Facial Biometrics. |
| **Unit D: Actuation Hub** | 5V Relay Module, DC Cooling Fan | Executes physical climate control actions based on sensor triggers. |

## Mobile App & Cloud Connectivity

- **Caregiver Dashboard**: Built with **Flutter**, the app provides a cross-platform interface for remote management, visualizing real-time environmental data and system status.
- **Cloud Sync**: Powered by **Supabase**, the system synchronizes settings, biometric data (as byte streams), and sensor logs between the mirror and the mobile app in real-time.
- **Remote Interaction**: Caregivers can toggle mirror modules (News, Calendar) and send voice messages from anywhere in the world.

## Installation & Connectivity

The system utilizes standard GPIO connections for sensors and relays, with a secure Wi-Fi link handling all encrypted data transmission between the IoT device and the Cloud.

---
*Developed as a 3rd Year Undergraduate Project in Computer Engineering.*
