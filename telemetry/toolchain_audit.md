# 🔧 CI Workflow Actions & Embedded Build Toolchain Audit

**Audit Timestamp:** `28-Nov-2026 01:48:47 AM IST` (`2026-11-27 20:18:47 UTC`)
- **Workflow Files Inspected:** `17`
- **Legacy Action Version Flags (`@v1/@v2/@v3`):** `1`

| Repository | Workflow File | Runner | Detected Toolchains | Audit |
| :--- | :--- | :--- | :--- | :--- |
| [`automotive-tft-cluster`](https://github.com/sherifred-singh/automotive-tft-cluster) | `ci.yml` | `ubuntu-latest` | `cppcheck, gcc, make` | ⚠️ Update actions/checkout@v3 |
| [`embedded-c-ring-buffer`](https://github.com/sherifred-singh/embedded-c-ring-buffer) | `c-build.yml` | `ubuntu-latest` | `gcc, make` | ✅ Modern actions |
| [`embedded-c-ring-buffer`](https://github.com/sherifred-singh/embedded-c-ring-buffer) | `ci.yml` | `ubuntu-latest` | `gcc, make` | ✅ Modern actions |
| [`embedded-fsm-engine`](https://github.com/sherifred-singh/embedded-fsm-engine) | `ci.yml` | `ubuntu-latest` | `gcc, make` | ✅ Modern actions |
| [`embedded-nvm-fault-logger`](https://github.com/sherifred-singh/embedded-nvm-fault-logger) | `ci.yml` | `ubuntu-latest` | `cppcheck, gcc, make` | ✅ Modern actions |
| [`embedded-software-timer`](https://github.com/sherifred-singh/embedded-software-timer) | `ci.yml` | `ubuntu-latest` | `gcc, make` | ✅ Modern actions |
| [`industrial-sensor-hal`](https://github.com/sherifred-singh/industrial-sensor-hal) | `ci.yml` | `ubuntu-latest` | `gcc, make` | ✅ Modern actions |
| [`linux-telemetry-char-driver`](https://github.com/sherifred-singh/linux-telemetry-char-driver) | `ci.yml` | `ubuntu-latest` | `cppcheck, make` | ✅ Modern actions |
| [`modbus-rtu-slave-c`](https://github.com/sherifred-singh/modbus-rtu-slave-c) | `ci.yml` | `ubuntu-latest` | `gcc, make` | ✅ Modern actions |
| [`pytest-bms-diagnostic-framework`](https://github.com/sherifred-singh/pytest-bms-diagnostic-framework) | `run_tests.yml` | `ubuntu-latest` | `pytest` | ✅ Modern actions |
| [`smart-industrial-disinfection-controller`](https://github.com/sherifred-singh/smart-industrial-disinfection-controller) | `ci.yml` | `ubuntu-latest` | `cppcheck, gcc, make` | ✅ Modern actions |
| [`stm32-automotive-uds-isotp-node`](https://github.com/sherifred-singh/stm32-automotive-uds-isotp-node) | `ci.yml` | `ubuntu-latest` | `gcc, make` | ✅ Modern actions |
| [`stm32-can-telemetry-prototype`](https://github.com/sherifred-singh/stm32-can-telemetry-prototype) | `ci.yml` | `ubuntu-latest` | `make` | ✅ Modern actions |
| [`stm32-dsp-vibration-spectral-analyzer`](https://github.com/sherifred-singh/stm32-dsp-vibration-spectral-analyzer) | `ci.yml` | `ubuntu-latest` | `gcc, make` | ✅ Modern actions |
| [`stm32-esp32-industrial-edge-controller`](https://github.com/sherifred-singh/stm32-esp32-industrial-edge-controller) | `ci.yml` | `ubuntu-latest` | `gcc, make` | ✅ Modern actions |
| [`stm32-failsafe-iap-bootloader`](https://github.com/sherifred-singh/stm32-failsafe-iap-bootloader) | `ci.yml` | `ubuntu-latest` | `gcc, make` | ✅ Modern actions |
| [`stm32-freertos-sensor-hub`](https://github.com/sherifred-singh/stm32-freertos-sensor-hub) | `ci.yml` | `ubuntu-latest` | `gcc, make` | ✅ Modern actions |

---
*Audited directly from live `.github/workflows/*.yml` definitions across embedded repos.*
