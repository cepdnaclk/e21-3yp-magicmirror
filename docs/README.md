---
layout: home
permalink: index.html

# Please update this with your repository name and project title
repository-name: eYY-3yp-magicmirror
title: Magic Mirror
---

[comment]: # "This is the standard layout for the project, but you can clean this and use your own template"

# Project Title

---

## Team
-  e21287, Sithum Perera, [email](e21287@eng.pdn.ac.lk)
-  e21229, Anna Kurera, [email](e21229@eng.pdn.ac.lk)
-  e21055, Kasun Lakshan, [email](e21055@eng.pdn.ac.lk)
-  e21253, Thenuka Ravindu, [email](e21253@eng.pdn.ac.lk)

<!-- Image (photo/drawing of the final hardware) should be here -->

<!-- This is a sample image, to show how to add images to your page. To learn more options, please refer [this](https://projects.ce.pdn.ac.lk/docs/faq/how-to-add-an-image/) -->

<!-- ![Sample Image](./images/sample.png) -->

#### Table of Contents
1. [Introduction](#introduction)
2. [Solution Architecture](#solution-architecture )
3. [Hardware & Software Designs](#hardware-and-software-designs)
4. [Testing](#testing)
5. [Detailed budget](#detailed-budget)
6. [Conclusion](#conclusion)
7. [Links](#links)

## Introduction

The Real World Problem

Caring for elderly or less mobile individuals at home often comes with significant challenges:

Intrusive Monitoring: Traditional methods like security cameras can feel invasive and strip users of their dignity and privacy.

Technological Barriers: Smart home interfaces are often too complex for elderly users, leading to frustration and abandonment of helpful technology.

Passive Environments: Standard mirrors and home devices are passive; they don't actively monitor the environment or intervene when safety conditions (like heatwaves) become dangerous.

## The Solution

ReflectOS transforms a standard mirror into an intelligent, proactive "Caregiver Companion." It bridges the gap between passive furniture and active health monitoring. Key features include:

Zero-Friction Biometric Enrollment: Caregivers can register users remotely by taking a selfie via the mobile app, instantly enabling secure, touch-free access on the mirror.

"The Wind Guardian": An autonomous climate control system that monitors room temperature and automatically triggers cooling fans if conditions become unsafe (e.g., >25°C).

Non-Intrusive Dashboard: A mobile app for caregivers that tracks environmental stats (temperature, humidity) and activity logs without using video feeds.

"The Puppeteer" Communication: Family members can type messages in the app that are spoken aloud and displayed on the mirror to ensure important reminders are noticed.

## Impact

ReflectOS empowers elderly users to live independently while giving families peace of mind. It replaces invasive surveillance with smart environmental monitoring and turns a daily object into a safety net, making home care more dignified and responsive.

## Solution Architecture

High-Level Diagram

The system consists of three main layers working in sync:

The Controller (Mobile App): A Flutter app for remote management, user enrollment, and environmental monitoring.

The Bridge (Cloud): Supabase (PostgreSQL + Storage) handles real-time synchronization of settings and biometric data.

The Brain (IoT Device): A Raspberry Pi 4 that powers the display, runs local AI (Face Recognition), and controls physical hardware.

Hardware and Software Designs

Hardware Components

Computing Unit: Raspberry Pi 4 Model B (4GB/8GB) acting as the central processor.

Display: A standard monitor panel housed behind a two-way acrylic mirror.

Sensor Array: BME280 sensor for precise temperature, humidity, and pressure readings.

Actuators: 5V Relay module controlling a DC cooling fan for the "Wind Guardian" feature.

Camera: Raspberry Pi Camera Module V2 for facial recognition.

## Software

Mobile App: Built with Flutter (Dart). Features include "Remote Selfie Enrollment," real-time dashboard graphs, and text-to-speech injection.

Smart Mirror Interface: Built with Node.js/Electron to render the "Glass UI" (Clock, News, Alerts).

AI & Logic: Python scripts using OpenCV/Dlib for face recognition and GPIO libraries for sensor/fan control.

Cloud Backend: Supabase for database management, authentication, and object storage.

## Testing

Hardware Testing

Sensor Calibration: Verified BME280 readings against standard thermometers to ensure accurate triggers for the "Wind Guardian."

Thermal Stress Testing: Tested the cooling fan's response time when the system was subjected to simulated heat loads.

Biometric Range Test: Evaluated the camera's ability to recognize faces at varying distances and lighting conditions.

## Software Testing

Latency Testing: Measured the time delay between toggling a switch in the Flutter app and the physical reaction on the mirror (fan on/off).

Cross-Platform Image Handling: Verified that images taken on both Android and Web platforms are correctly converted to byte data and uploaded to Supabase without file path errors.

Security Audit: Tested the Supabase Row Level Security (RLS) policies to ensure unauthorized users cannot upload or access biometric data.

## Budget

| Item | Status | Cost (Rs.) |
| :--- | :--- | :--- |
| Raspberry Pi 4 Model B | Available | 26,000 |
| Rpi4 camera module 3 | Available | 5,690 |
| Two way mirror | Approx. | 8,500 |
| Monitor screen | - | 12,000 |
| Temperature & Humidity sensor (BME280) | - | 950 |
| Light Intensity Sensor (OPT3001) | - | 995 |
| Wooden / 3D Printed Frame | Approx. | 6,000 |
| Mic | - | 950 |
| Speakers | - | 8,570 |
| Gesture sensor (ST GY-VL53L0XV2) x2 | - | 1,200 |
| Addressable led strip (WS2812B) (2m) | - | 1,380 |
| Esp32 (For the smart switch) | - | 1,280 |
| Presence detector (HLK-LD2410) | - | 1,285 |
| **Total** | | **Rs. 74,700** |
| **Budget (excluding available items)** | | **Rs. 43,010** |

## Commercialization Plans

The project has been designed with a focus on cost-effectiveness and scalability, making it a viable candidate for a commercial consumer product:

Modular DIY Kits: Offering the electronics (pre-configured Raspberry Pi, sensors, and camera) as a modular kit for tech enthusiasts to build into their own frames.

Custom Luxury Models: Developing high-end, fully assembled mirrors with premium wooden or 3D-printed frames for the smart home and hospitality markets (e.g., hotels or fitness studios).

Subscription-Based Customization: Creating a cloud platform where users can purchase and download premium "mirror skins" or advanced AI modules to further personalize their device.

B2B Applications: Marketing specialized versions of the mirror for use as digital notice boards in offices, schools, or retail fitting rooms.

## Links

- [Project Repository](https://github.com/cepdnaclk/{{ page.repository-name }}){:target="_blank"}
- [Project Page](https://cepdnaclk.github.io/{{ page.repository-name}}){:target="_blank"}
- [Department of Computer Engineering](http://www.ce.pdn.ac.lk/)
- [University of Peradeniya](https://eng.pdn.ac.lk/)

[//]: # (Please refer this to learn more about Markdown syntax)
[//]: # (https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)
