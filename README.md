# Plate Recognition Access Control System

Embedded AI-based vehicle license plate recognition and automated barrier control system using YOLO, Python, and ESP32.

## Overview

This project was developed as the final project for the Electronics Technician degree of **Franco Heis** and **Juan Ignacio Tovo**.

The system combines Artificial Intelligence, Computer Vision, and Embedded Systems to automate vehicle access control in a parking garage. Through computer vision techniques, the system detects and recognizes vehicle license plates, verifies whether the vehicle is authorized, and controls a motorized access barrier.

The project is divided into two main stages.

### Stage 1: License Plate Recognition System

The first stage focuses on implementing the license plate recognition system on a computer using Python.

A camera captures images of incoming vehicles, which are processed using a YOLO-based model to detect the license plate. Once the plate is detected, OCR techniques are used to extract and recognize its characters.

The recognized plate can then be validated by the software to determine whether the vehicle is allowed to access the parking area. When access is authorized, the computer sends a command to the ESP32 through serial communication using an FT232RL USB-to-TTL converter.

#### Main Features

- Real-time license plate detection.
- Character recognition using OCR.
- License plate validation.
- AI-powered computer vision.
- Python-based image processing.
- Serial communication with the ESP32.

### Stage 2: Barrier Control System

The second stage focuses on implementing the physical access control system using an ESP32 microcontroller.

The ESP32 is responsible for controlling the barrier motor, monitoring the sensors, and managing the opening and closing sequence.

When the ESP32 receives the authorization command from the computer, it activates the motor to raise the barrier. The system uses sensors to determine the position of the barrier and detect the passage of the vehicle, allowing the ESP32 to safely control the complete opening and closing sequence.

#### Main Features

- Barrier motor control.
- Barrier position monitoring.
- Vehicle presence detection.
- Automatic opening and closing sequence.
- Safety and operation monitoring.
- Serial communication with the recognition system.

## System Architecture

The system follows the following general sequence:

1. A camera captures the incoming vehicle.
2. The computer processes the image using the YOLO model.
3. The license plate is detected.
4. OCR is used to recognize the characters of the plate.
5. The software validates the detected license plate.
6. If access is authorized, the computer sends a command through the FT232RL USB-to-TTL converter.
7. The ESP32 receives the command through UART communication.
8. The ESP32 activates the barrier motor.
9. Sensors monitor the barrier position and vehicle passage.
10. Once the vehicle has passed, the ESP32 controls the closing sequence.

## Technologies Used

### Software

- Python
- YOLO
- OpenCV
- Tesseract OCR
- PySerial

### Hardware

- Computer
- Camera
- ESP32
- FT232RL USB-to-TTL converter
- Vehicle detection sensor
- Limit switches
- L298N motor driver
- Barrier motor

## Communication

Communication between the license plate recognition software and the barrier control system is performed through UART serial communication.

The computer communicates with the ESP32 using an FT232RL USB-to-TTL converter. Once the software determines that the barrier should be opened, it sends the corresponding command to the ESP32.

The ESP32 interprets the received command and executes the barrier control sequence.

## Project Objectives

- Automate vehicle access control.
- Detect and recognize vehicle license plates using Artificial Intelligence.
- Integrate computer vision with embedded systems.
- Control a motorized barrier automatically.
- Implement communication between a computer and an ESP32.
- Improve access control through automatic license plate recognition.
- Develop a functional and low-cost prototype.

## Future Development

The current implementation represents a functional prototype of an intelligent vehicle access control system. However, several additional features could be incorporated in future versions to improve functionality, usability, and scalability.

### Planned Improvements

- **Parking Occupancy Display:** Integration of a display screen at the parking entrance showing the number of available parking spaces in real time. This feature would provide drivers with immediate information about parking availability before entering the facility.
- Web-based monitoring and management interface.
- Event logging and access history storage.
- Cloud database synchronization for remote administration.
- Support for multiple access points and barriers.
- Mobile application for monitoring and configuration.
- Integration with RFID or QR-based identification systems as a secondary authentication method.
- Automatic notification system for unauthorized access attempts.

---

## Authors

- **Franco Heis**
- **Juan Ignacio Tovo**

Final Project – Electronics Technician Degree
