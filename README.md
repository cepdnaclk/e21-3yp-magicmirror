# ReflectStudio: Intelligent Smart Mirror Platform

**ReflectStudio** is a hybrid AI–IoT smart mirror system designed to enhance everyday productivity, smart living, and assisted care. By combining computer vision, environmental sensing, AI interaction, and cloud connectivity, **ReflectStudio** transforms a standard mirror into an intelligent home companion that fits naturally into daily routines for all users.

---

## Key Features

- **Face Recognition & Profile Personalization** Users are identified through face recognition using local face encoding combined with cloud-based recognition via **AWS Rekognition**, enabling personalized dashboards and experiences.

- **Remote Profile & Reminder Management** Guardians or family members can create user profiles and schedule reminders through the mobile app, which are displayed directly on the mirror.

- **"Wind Guardian" – Smart Climate Awareness** Room temperature and humidity are continuously monitored, and cooling fans are automatically triggered when unusual or uncomfortable conditions are detected.

- **AI Persona Interaction** An AI-powered conversational persona allows users—especially elderly individuals—to interact naturally using voice, providing companionship and easy access to information.

- **Presence & Gesture-Based Control** Radar-based presence detection wakes the system automatically, while gesture and voice controls enable fully hands-free interaction.

- **Smart Daily Services** Displays calendar events, weather updates, emails, and music playback, helping users make productive use of time while getting ready.

---

## Hardware Architecture

The **ReflectStudio** system is built around a central computing unit and multiple peripheral modules that enable intelligent interaction and smart environment control:

| Unit | Hardware Components | Primary Function |
|:---|:---|:---|
| **Unit A: Computing Core** | Raspberry Pi 4 Model B | Runs system logic, AI processing, and smart mirror interface |
| **Unit B: Visual Interface** | Display Panel, Two-Way Mirror | Displays the smart mirror UI and user information |
| **Unit C: Sensing Array** | BME280, OPT3001, Camera Module 3, Radar Sensor | Captures environmental data, light levels, presence, and facial data |
| **Unit D: Interaction Layer** | Gesture Sensor, Microphone | Enables touchless voice and gesture control |
| **Unit E: Actuation Hub** | ESP32, Relay Module, Fan, LED Strip | Controls smart devices such as fans and lighting |



---

## Mobile App & Cloud Connectivity

- **Companion Mobile App** Built using **Flutter**, the mobile app provides a cross-platform interface for profile management, reminder scheduling, and remote monitoring.

- **Cloud Integration** The system uses **AWS S3** for image storage and **AWS Rekognition** for cloud-based facial recognition, ensuring secure and scalable identity management.

- **Remote Interaction** Guardians can manage user profiles, send reminders, and control mirror features remotely through secure cloud APIs.



---

## Installation & Connectivity

**ReflectStudio** uses standard GPIO connections for sensors and actuators.  
All communication between the mirror, cloud services, and mobile app is handled via secure Wi-Fi connections with encrypted APIs, ensuring privacy and reliability.

---

*Developed as a 3rd Year Undergraduate Group Project in Computer Engineering, University of Peradeniya.*
