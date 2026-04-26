---
layout: home
permalink: index.html

repository-name: e21-3yp-ReflectStudio
title: "ReflectStudio: Intelligent Smart Mirror Platform"
---

# ReflectStudio: Intelligent Smart Mirror Platform

---

## Team
- **e21287**, Sithum Perera, [e21287@eng.pdn.ac.lk](mailto:e21287@eng.pdn.ac.lk)
- **e21229**, Anna Kurera, [e21229@eng.pdn.ac.lk](mailto:e21229@eng.pdn.ac.lk)
- **e21055**, Kasun Lakshan, [e21055@eng.pdn.ac.lk](mailto:e21055@eng.pdn.ac.lk)
- **e21253**, Thenuka Ravindu, [e21253@eng.pdn.ac.lk](mailto:e21253@eng.pdn.ac.lk)

---

#### Table of Contents
1. [Introduction](#introduction)
2. [Solution Architecture](#solution-architecture)
3. [Hardware & Software Designs](#hardware--software-designs)
4. [Testing](#testing)
5. [Detailed Budget](#detailed-budget)
6. [Commercialization Plans](#commercialization-plans)
7. [Conclusion](#conclusion)
8. [Links](#links)

---

## Introduction

### The Real-World Problem

With the rapid growth of smart homes and AI-powered devices, technology often prioritizes features over **human-centered experience**. Users are required to interact with multiple fragmented applications to manage daily tasks such as checking schedules, emails, weather, or controlling smart devices. Even simple daily routines—like getting ready in front of a mirror—remain disconnected from productivity and meaningful interaction.

For elderly users, these challenges are amplified. Complex interfaces, limited interaction, and lack of emotional engagement can make technology feel intimidating and isolating. While homes may collect environmental data such as temperature or humidity, they rarely provide **interactive communication, companionship, or intuitive assistance**. As a result, technology often feels cold, impersonal, and overwhelming instead of supportive and reassuring.

---

## The Solution

**ReflectStudio** transforms a standard mirror into an **intelligent smart mirror platform** that acts as a **personal assistant, smart home hub, and digital companion**.

For everyday users, **ReflectStudio** helps utilize time effectively by displaying **schedules, emails, weather updates, music controls, and reminders** while getting ready—turning idle mirror time into productive moments. For elderly users, **ReflectStudio** provides a **conversational AI persona** that enables natural interaction and companionship, along with **environmental monitoring** that detects unusual temperature or humidity conditions to support comfort and safety.



**ReflectStudio** combines **AI, IoT, and automation** with **voice, gesture, and face recognition**, offering a **hands-free, intuitive, and privacy-aware experience** suitable for both daily living and assisted care scenarios.

---

## Solution Architecture

### High-Level Overview

**ReflectStudio** follows a **Hybrid Edge–Cloud Architecture** consisting of three main layers:

- **User Layer**
  - Interaction via voice, gestures, and presence
  - Personalized dashboard display on the mirror
- **Edge Intelligence Layer**
  - Raspberry Pi handles sensor data processing
  - Local face encoding and recognition for fast authentication
  - Real-time control logic for smart devices
- **Cloud Intelligence Layer**
  - **AWS S3** for secure profile image storage
  - **AWS Rekognition** for cloud-based facial recognition
  - Cloud AI services for conversational intelligence
  - Secure APIs for mobile app communication



---

## Hardware & Software Designs

### Hardware Components

| Component | Description |
|:---|:---|
| **Raspberry Pi 4** | Central processing and control unit |
| **Monitor + Two-Way Mirror** | Visual interface for smart display |
| **Camera Module 3** | Face recognition and user identification |
| **BME280** | Temperature and humidity sensing |
| **OPT3001** | Ambient light sensing |
| **HLK-LD2410 Radar** | Presence detection |
| **Gesture Sensor (VL53L0X)** | Gesture-based interaction |
| **WS2812B LED Strip** | Smart lighting and visual feedback |
| **ESP32** | Smart switch and device control |
| **Relay Module** | Fan and device actuation |
| **Microphone & Speakers** | Voice interaction and AI responses |

---

### Software Components

- **Smart Mirror Application**
  - Python-based backend logic
  - OpenCV for local face processing
  - Real-time sensor monitoring and automation
- **AI Persona**
  - Speech-to-text and text-to-speech pipeline
  - Cloud-based conversational AI integration
- **Mobile Companion App**
  - Built using Flutter
  - Face profile enrollment
  - Reminder scheduling and remote monitoring
  - Guardian/caregiver access
- **Communication Protocols**
  - MQTT for IoT messaging
  - HTTPS for secure cloud communication

---

## Testing

### Hardware Testing
* Sensor accuracy validation for temperature, humidity, and light intensity.
* Presence detection range and reliability testing.
* Relay and smart device response verification.

### Software Testing
* Face recognition accuracy under varying lighting conditions.
* Latency testing for mobile app to mirror communication.
* AI interaction response time evaluation.
* Fail-safe testing for autonomous fan and lighting control.

---

## Detailed Budget

| Item | Status | Cost (Rs.) |
|:---|:---:|:---|
| Raspberry Pi 4 Model B | Available | 26,000 |
| Camera Module 3 | Available | 5,690 |
| Two-Way Mirror | Approx. | 8,500 |
| Monitor Screen | - | 12,000 |
| BME280 Sensor | - | 950 |
| OPT3001 Sensor | - | 995 |
| Frame (Wood / 3D Printed) | Approx. | 6,000 |
| Microphone | - | 950 |
| Speakers | - | 8,570 |
| Gesture Sensors x2 | - | 1,200 |
| WS2812B LED Strip | - | 1,380 |
| ESP32 | - | 1,280 |
| Presence Sensor (HLK-LD2410) | - | 1,285 |
| **Total** | | **74,700** |
| **Excluding Available Items** | | **43,010** |

---

## Commercialization Plans

* **Consumer Smart Home Product**: Daily-use smart mirror for homes.
* **Assisted Living & Elder Care**: Companion-focused versions with caregiver dashboards.
* **Hospitality & Retail**: Smart mirrors for hotels, gyms, and fitting rooms.
* **Modular DIY Kits**: Pre-configured electronics kits for enthusiasts.
* **Premium Models**: High-end mirror designs with luxury finishes.

---

## Conclusion

**ReflectStudio** demonstrates how everyday objects can be transformed into **intelligent, emotionally aware systems** through the integration of AI and IoT. By focusing on **human-centered interaction, privacy-first design, and hybrid intelligence**, **ReflectStudio** delivers a smart mirror platform that supports productivity, companionship, and comfort—making technology feel **natural, supportive, and human**.

---

## Links

- [Project Repository](https://github.com/cepdnaclk/{{ page.repository-name }}){:target="_blank"}
- [Project Page](https://cepdnaclk.github.io/{{ page.repository-name}}){:target="_blank"}
- [Department of Computer Engineering](http://www.ce.pdn.ac.lk/)
- [University of Peradeniya](https://eng.pdn.ac.lk/)
