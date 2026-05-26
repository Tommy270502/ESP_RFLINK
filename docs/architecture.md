# Architecture

System architecture for Wireless Dev Bridge V1.

## Host Tools And Transports

```mermaid
graph LR
    subgraph Host
        CLI["Python CLI<br/>(wdb)"]
        SDK["Python SDK<br/>(WirelessDevBridge)"]
        WB["Local Web Workbench<br/>(FastAPI + browser)"]
        Script["User Scripts"]
    end

    subgraph Dongle["ESP32-S3 Dongle"]
        Serial["USB CDC Serial"]
        HTTP["HTTP API"]
        WS["WebSocket"]
        BLE["BLE GATT"]
        CMD["CommandService"]
    end

    CLI --> SDK
    WB --> SDK
    Script --> SDK

    SDK -->|JSONL| Serial
    SDK -->|JSON| HTTP
    SDK -->|JSON| WS
    SDK -->|JSON| BLE

    Serial --> CMD
    HTTP --> CMD
    WS --> CMD
    BLE --> CMD
```

## Firmware Module Structure

```mermaid
graph TD
    main["main.cpp<br/>setup / loop"]

    main --> AppState["AppState<br/>Shared runtime state"]
    main --> CMD["CommandService<br/>JSON command dispatcher"]
    main --> Radio["RadioService<br/>nRF24L01+ driver"]
    main --> Web["WebService<br/>SoftAP, HTTP, WebSocket"]
    main --> BLE_S["BleService<br/>BLE UART transport"]
    main --> Bridge["BridgeService<br/>RF-to-WiFi/BLE forwarding"]
    main --> Settings["SettingsService<br/>NVS persistence"]
    main --> WebUi["WebUi<br/>Firmware browser dashboard"]

    CMD --> Radio
    CMD --> Settings
    CMD --> Bridge
    CMD --> AppState

    Bridge --> Web
    Bridge --> BLE_S

    Radio -->|RX packets| Bridge
```

## Command Layer

All transports share one command request/response envelope:

```
Request:  {"cmd":"<name>", ...params}
Response: {"ok":true|false, "cmd":"<name>", "data":{...}, "error":null|"..."}
```

```mermaid
graph LR
    subgraph Transports
        S["USB Serial"]
        H["HTTP POST"]
        W["WebSocket"]
        B["BLE Write"]
    end

    subgraph CommandService
        Parse["Parse JSON"]
        Dispatch["Dispatch by cmd"]
        Reply["Build response"]
    end

    subgraph Services
        RF["RF Config / Send / Listen"]
        Addr["Address Management"]
        Br["Bridge Toggles"]
        Set["Settings CRUD"]
        Diag["Diagnostics / Identify"]
        Auth["Optional Token Auth"]
    end

    S --> Parse
    H --> Parse
    W --> Parse
    B --> Parse

    Parse --> Auth
    Auth --> Dispatch

    Dispatch --> RF
    Dispatch --> Addr
    Dispatch --> Br
    Dispatch --> Set
    Dispatch --> Diag

    RF --> Reply
    Addr --> Reply
    Br --> Reply
    Set --> Reply
    Diag --> Reply
```

## RF And Settings Services

```mermaid
graph TD
    subgraph Runtime
        RFConfig["RF Config<br/>channel, datarate, power, auto_ack"]
        Addresses["Pipe Addresses<br/>5-byte RX/TX"]
        BridgeState["Bridge State<br/>rf_to_wifi, rf_to_ble"]
        ListenState["Listen State<br/>start/stop"]
    end

    subgraph Persistence["NVS Persistence"]
        Save["settings_save"]
        Load["settings_get"]
        Reset["settings_reset"]
    end

    RFConfig -->|"settings_set"| Save
    Addresses -->|"settings_set"| Save
    BridgeState -->|"settings_set"| Save
    Save -->|reboot| Load
    Load --> RFConfig
    Load --> Addresses
    Load --> BridgeState
    Reset -->|"factory defaults"| Load
```

## Hardware Block Diagram

```mermaid
graph LR
    USB["USB-C<br/>Data + Power"] --> ESP["ESP32-S3<br/>Wi-Fi, BLE, USB CDC"]
    ESP -->|SPI| NRF["nRF24L01+<br/>2.4 GHz RF"]
    ESP --> LED["Status LED"]
    ESP --> Flash["4 MB Flash<br/>NVS + App"]
    NRF --> ANT["PCB Antenna<br/>or u.FL"]
```
