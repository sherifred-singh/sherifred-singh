# Sherifred Singh
### Senior Embedded Firmware & Automotive Systems Engineer
**Coimbatore, India** • [LinkedIn](https://www.linkedin.com/in/sherifredsing/) • [Email](mailto:ssherifred@gmail.com) • [Portfolio](https://sherifred-singh.github.io/PORTFOLIO/)

---

## ⚡ Executive Engineering Summary

Senior Embedded Systems Engineer with **6.5+ years of production experience** delivering robust, safety-critical firmware across automotive, industrial automation, and edge telemetry domains.

Specialized in register-level **Embedded C (C99)**, **ARM Cortex-M4 (STM32F446RE @ 180 MHz)**, **Automotive In-Vehicle Networking (CAN, ISO 14229-1 UDS, ISO 15765-2 DoCAN)**, **Edge DSP / Signal Processing**, **Secure In-Application Programming (IAP) Bootloaders**, and **Python-based automated test frameworks (pytest)**. Strong foundation in hardware-software co-design, MISRA-C compliance, FreeRTOS multi-threading, and Linux kernel drivers.

---

## 🛠 Technical Proficiencies

<p align="left">
  <!-- Core Languages & Systems -->
  <img src="https://img.shields.io/badge/Embedded%20C%20(C99)-00599C?style=for-the-badge&logo=c&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python%203-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FreeRTOS-7F00FF?style=for-the-badge&logoColor=white"/>
  <img src="https://img.shields.io/badge/Linux%20Kernel%20Drivers-FCC624?style=for-the-badge&logo=linux&logoColor=black"/>
  <br>
  <!-- Silicon Architectures -->
  <img src="https://img.shields.io/badge/STM32%20ARM%20Cortex--M4%20(180MHz)-03234B?style=for-the-badge&logo=stmicroelectronics&logoColor=white"/>
  <img src="https://img.shields.io/badge/Microchip%20PIC18-000000?style=for-the-badge&logo=microchip&logoColor=white"/>
  <img src="https://img.shields.io/badge/ESP32%20SoC-E7352C?style=for-the-badge&logo=espressif&logoColor=white"/>
  <br>
  <!-- Automotive & Industrial Protocols -->
  <img src="https://img.shields.io/badge/CAN%20Bus%20%2F%20CAN--FD-004080?style=for-the-badge&logoColor=white"/>
  <img src="https://img.shields.io/badge/ISO%2014229--1%20UDS-darkred?style=for-the-badge&logoColor=white"/>
  <img src="https://img.shields.io/badge/ISO%2015765--2%20DoCAN-indigo?style=for-the-badge&logoColor=white"/>
  <img src="https://img.shields.io/badge/Modbus%20RTU%20(RS--485)-darkgreen?style=for-the-badge&logoColor=white"/>
  <br>
  <!-- Tools, CI & Testing -->
  <img src="https://img.shields.io/badge/Pytest%20Automation-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white"/>
  <img src="https://img.shields.io/badge/Unity%20C%20Test-brightgreen?style=for-the-badge&logoColor=white"/>
  <img src="https://img.shields.io/badge/GitHub%20Actions%20CI-2088FF?style=for-the-badge&logo=githubactions&logoColor=white"/>
  <img src="https://img.shields.io/badge/STM32CubeIDE-03234B?style=for-the-badge&logo=stmicroelectronics&logoColor=white"/>
  <img src="https://img.shields.io/badge/Git%20Version%20Control-F05032?style=for-the-badge&logo=git&logoColor=white"/>
</p>

* **Architecture & Firmwares:** Bare-metal register drivers, ISR architecture, hardware DMA ping-pong buffering, FSM engines, non-blocking timers, circular ring buffers.
* **Automotive Protocols & Standards:** ISO 14229-1 (Unified Diagnostic Services), ISO 15765-2 (DoCAN), CAN 2.0B / CAN-FD, ISO 10816-3 (Condition Monitoring), Seed-Key Security Access algorithms.
* **Test Automation & Quality:** Automated hardware-in-the-loop (HIL) test suites, Pytest diagnostic test automation, Unity C unit testing, GitHub Actions CI/CD workflows, MISRA-C static safety principles.
* **Hardware & Lab Equipment:** Digital Storage Oscilloscopes (DSO), Saleae Logic Analyzers, CAN transceivers, ST-LINK V2/V3 debugging, Multimeter, Schematic Review (KiCad).

---

## 🏆 Featured Production Repositories (STM32 NUCLEO-F446RE & Automotive)

### 🌐 1. [stm32-esp32-industrial-edge-controller](https://github.com/sherifred-singh/stm32-esp32-industrial-edge-controller)
> **Distributed Dual-MCU Industrial IoT Edge Controller & Gateway (STM32F446RE + ESP32-S3 FreeRTOS)**
* **Architectural Partitioning:** Real-time deterministic sensor acquisition and actuator safety on ARM Cortex-M4 (STM32F446RE @ 180 MHz), offloading wireless BLE 5.0 diagnostics and MQTT telemetry to dual-core ESP32-S3.
* **Deterministic DMA Protocol:** Circular DMA UART with hardware IDLE line interrupt, fast 256-entry CRC-16-CCITT table verification, and compile-time struct static assertions.
* **Fail-Safe Actuation & E-Stop:** Sub-millisecond physical shutdown directly cutting `TIM1->BDTR` Main Output Enable (MOE), clearing PWM duty to 0%, and releasing relay coils.
* **Verification & CI/CD:** 7/7 Native C99 unit tests + 6/6 Python protocol stress tests running in automated GitHub Actions CI.

### 🚗 2. [stm32-automotive-uds-isotp-node](https://github.com/sherifred-singh/stm32-automotive-uds-isotp-node)
> **Production ISO 14229-1 (UDS) Server & ISO 15765-2 (DoCAN) Transport Layer on STM32F446RE (ARM Cortex-M4 @ 180 MHz)**
* Full ISO 15765-2 DoCAN network layer handling Single Frame, First Frame, Flow Control (with `BS` and `STmin`), and Consecutive Frames with strict timeout monitoring (`N_Bs`, `N_Cr`).
* Complete ISO 14229-1 UDS diagnostic server supporting services `0x10`, `0x11`, `0x14`, `0x19`, `0x22`, `0x27` (with 3-attempt lockout), `0x2E`, `0x31`, and `0x3E`.
* Hardware bxCAN peripheral driver configured at 500 kbps with dual 32-bit hardware identifier filtering.
* **Verification:** 15/15 Unity C unit tests passing + 9/9 Python diagnostic client validation tests.

### ⚙️ 3. [stm32-dsp-vibration-spectral-analyzer](https://github.com/sherifred-singh/stm32-dsp-vibration-spectral-analyzer)
> **Real-Time 1024-Point Real FFT & Ping-Pong DMA Edge DSP Engine on STM32F446RE FPU**
* Continuous 50 kHz accelerometer sampling triggered via TIM2 TRGO into ADC1 with zero CPU overhead using DMA2 Stream 0 double-buffering.
* 1024-point Real FFT decomposition on ARM Cortex-M4 hardware FPU executing in under 1.1 ms (5.3% CPU budget).
* Raised-cosine Hanning windowing, parabolic sub-bin peak interpolation, Total Harmonic Distortion (THD %) computation, and automated ISO 10816-3 machinery vibration health evaluation.
* **Verification:** 7/7 Unity C unit tests + Python real-time spectral waterfall viewer tool.

### 🛡️ 4. [stm32-failsafe-iap-bootloader](https://github.com/sherifred-singh/stm32-failsafe-iap-bootloader)
> **Brick-Proof Dual-Slot In-Application Programming (IAP) Bootloader on STM32F446RE (512 KB Flash)**
* Asymmetric NOR Flash partitioning (Slot A: 192 KB, Slot B: 256 KB) strictly aligned to physical erase sector boundaries.
* Hardware CRC-32 accelerator (`0x04C11DB7`) over entire image payload with structured 40-byte `image_header_t`.
* Main Stack Pointer (MSP) sanity checking within physical SRAM bounds (`0x20000000`–`0x20020000`), vector table relocation (`SCB->VTOR`), and execution handover.
* Watchdog probation window (`SLOT_STATE_TESTING`) with automatic rollback to alternate slot if firmware crashes repeatedly.
* **Verification:** 10/10 Unity C unit tests + Python IAP packager and UART flasher utility.

### 🔋 5. [pytest-bms-diagnostic-framework](https://github.com/sherifred-singh/pytest-bms-diagnostic-framework)
> **Automotive EV Battery Management System (BMS) Diagnostic Test Automation in Python**
* Production Pytest test harness validating cell balancing, overvoltage/undervoltage thresholds, thermal runaway alerts, and UDS diagnostic routines.
* Automated CAN bus telemetry decoding, log assertions, and test report generation.

### 🐧 6. [linux-telemetry-char-driver](https://github.com/sherifred-singh/linux-telemetry-char-driver)
> **Linux Kernel Character Device Driver with Concurrency Control & Ring Buffering**
* Kernel character driver with non-blocking I/O, wait queues, mutex concurrency protection, and ioctl telemetry control.

### 🏎️ 7. [automotive-tft-cluster](https://github.com/sherifred-singh/automotive-tft-cluster)
> **Real-Time Automotive Digital Instrument Cluster with High-Speed CAN Bus Ingestion**
* High-performance instrument cluster displaying real-time speed, RPM, battery telemetry, and ISO warning telltales.

---

## 📂 Core Firmware Modules & Driver Architecture (Open Source)

* ⭐ **[embedded-c-ring-buffer](https://github.com/sherifred-singh/embedded-c-ring-buffer)** — Lock-free, thread-safe FIFO circular ring buffer in C99 for UART/SPI ISR-to-main communication.
* ⭐ **[embedded-fsm-engine](https://github.com/sherifred-singh/embedded-fsm-engine)** — Table-driven Finite State Machine (FSM) framework with an Automatic Transfer Switch (ATS) industrial model.
* ⭐ **[embedded-software-timer](https://github.com/sherifred-singh/embedded-software-timer)** — Deterministic software timer service with delta-tick queue management and sub-millisecond precision.
* ⭐ **[embedded-nvm-fault-logger](https://github.com/sherifred-singh/embedded-nvm-fault-logger)** — Anti-tearing wear-leveled NVM blackbox fault recorder in C99 with CRC-16-CCITT integrity.
* ⭐ **[smart-industrial-disinfection-controller](https://github.com/sherifred-singh/smart-industrial-disinfection-controller)** — Industrial multi-phase ozone & UV-C sterilization system with Modbus RTU telemetry and safety interlocks.
* ⭐ **[stm32-can-telemetry-prototype](https://github.com/sherifred-singh/stm32-can-telemetry-prototype)** — Automotive bxCAN 500 kbps telemetry acquisition, hardware acceptance filtering, and safety heartbeat monitor.
* ⭐ **[stm32-freertos-sensor-hub](https://github.com/sherifred-singh/stm32-freertos-sensor-hub)** — Multi-tasking sensor acquisition and telemetry with FreeRTOS queues, mutexes, and watchdog supervision on STM32.
* ⭐ **[industrial-sensor-hal](https://github.com/sherifred-singh/industrial-sensor-hal)** — Decoupled sensor driver library for MAX6675 (SPI), DS18B20 (1-Wire with CRC8), and NTC ADC LUT interpolation.
* ⭐ **[modbus-rtu-slave-c](https://github.com/sherifred-singh/modbus-rtu-slave-c)** — Lightweight Modbus-RTU slave protocol stack with fast table CRC-16 for RS-485 industrial networks.

---

## 🏭 Commercial Products & Track Record

### 🔹 Automatic Transfer Switch (ATS) Controller
**Target:** Microchip PIC18 • **Status:** Commercial Product *(Source Code Confidential)*  
* Industrial power automation controller for automated, fail-safe switching between mains grid and backup generator.
* Implemented multi-state generator & mains transfer logic with strict *break-before-make* relay interlocking.
* Configured calibrated ADC sampling for rapid undervoltage, overvoltage, and phase-imbalance detection with persistent EEPROM fault logging.

### 🔹 16-Loom Textile Production Monitor
**Target:** PIC18 / STM32 • **Status:** Commercial Product *(Source Code Confidential)*  
* Edge monitoring and logging system deployed across industrial weaving facilities collecting shift-wise metrics from 16 looms simultaneously.
* Built a power-fail-safe state snapshotting mechanism to EEPROM with RTC (DS3231) timestamping.

### 🔹 Multi-Stage Industrial Temperature Controller
**Target:** PIC18F46K22 • **Status:** Commercial Product *(Source Code Confidential)*  
* Precision cooling and compressor management controller for commercial refrigeration units.
* Interfaced analog NTC (calibrated LUT linearisation), 1-Wire (DS18B20), and SPI (MAX6675) with anti-short-cycle delay timers.

---

<div align="center">
  <table border="0">
    <tr>
      <td align="center" valign="middle">
        <a href="https://github.com/sherifred-singh">
          <img src="https://streak-stats.demolab.com?user=sherifred-singh&theme=tokyonight&hide_border=true&date_format=j%20M%5B%20Y%5D&v=1020" height="145" alt="GitHub Streak" />
        </a>
      </td>
      <td align="center" valign="middle">
        <a href="https://github.com/sherifred-singh">
          <img src="https://github-profile-summary-cards.vercel.app/api/cards/profile-details?username=sherifred-singh&theme=tokyonight&v=1020" height="145" alt="GitHub Profile Details" />
        </a>
      </td>
    </tr>
  </table>
</div>
