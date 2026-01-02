# Testing Mode

Testing mode enables running network diagnostics (ping and iperf) between OpenWRT devices defined in a fleet inventory. This is useful for validating network connectivity, measuring throughput, and troubleshooting network issues.

## Overview

Testing mode allows you to:

- **Run ping tests** between devices to check connectivity and measure latency
- **Run iperf tests** to measure bandwidth between devices
- **Reference devices from your fleet inventory** - no need to remember IP addresses
- **Define tests in YAML** for repeatable network validation

## Quick Start

### 1. Create a Test Configuration File

```yaml
# tests.yaml
fleet_file: fleet.yaml  # Reference your fleet inventory

tests:
  # Ping test
  - name: ping-router-to-ap
    type: ping
    source: main-router
    destination: ap-living-room
    count: 10

  # Iperf bandwidth test
  - name: iperf-throughput
    type: iperf
    server: ap-living-room
    client: main-router
    duration: 10
```

### 2. Validate Your Test Config

```bash
wrtkit testing validate tests.yaml
```

### 3. Run Tests

```bash
wrtkit testing run tests.yaml
```

## CLI Commands

### `wrtkit testing run`

Run network tests from a test configuration file.

```bash
# Run all tests
wrtkit testing run tests.yaml

# Run a specific test by name
wrtkit testing run tests.yaml --test ping-router-to-ap

# Output results as JSON (for scripting)
wrtkit testing run tests.yaml --json

# Disable colored output
wrtkit testing run tests.yaml --no-color
```

**Options:**

| Option | Description |
|--------|-------------|
| `--test, -t` | Run only the specified test by name |
| `--json` | Output results as JSON |
| `--no-color` | Disable colored output |

### `wrtkit testing validate`

Validate a test configuration file without running tests.

```bash
wrtkit testing validate tests.yaml
```

This checks:

- Test file syntax and schema
- Fleet file exists and is valid
- All referenced devices exist in the fleet
- Test definitions have required fields

### `wrtkit testing show`

Show the resolved test configuration with all device references expanded.

```bash
# Show as YAML (default)
wrtkit testing show tests.yaml

# Show as JSON
wrtkit testing show tests.yaml --format json
```

## Test Configuration Schema

### Top-Level Structure

```yaml
fleet_file: fleet.yaml  # Path to fleet inventory (relative to test file)

tests:
  - name: test-name
    type: ping  # or iperf
    # ... test-specific options
```

### Ping Tests

Ping tests run from a source device to a destination.

```yaml
- name: ping-router-to-ap
  type: ping
  source: main-router           # Device name from fleet
  destination: ap-living-room   # Device name from fleet, or IP/hostname
  count: 10                     # Number of pings (default: 4)
  interval: 0.5                 # Seconds between pings (default: 1.0)
  timeout: 5                    # Per-ping timeout in seconds (default: 5)
```

**Fields:**

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `name` | Yes | - | Unique test name |
| `type` | Yes | - | Must be `ping` |
| `source` | Yes | - | Source device name from fleet |
| `destination` | Yes | - | Destination device name or IP/hostname |
| `count` | No | 4 | Number of ping requests |
| `interval` | No | 1.0 | Seconds between pings |
| `timeout` | No | 5 | Per-ping timeout in seconds |

**Destination Resolution:**

- If `destination` matches a device name in the fleet, it resolves to that device's target IP
- Otherwise, it's used as-is (e.g., `8.8.8.8` or `google.com`)

### Iperf Tests

Iperf tests measure bandwidth between two devices. The test orchestrates starting an iperf3 server on one device, running the client on another, and collecting results.

```yaml
- name: iperf-throughput
  type: iperf
  server: ap-living-room        # Device to run iperf server on
  client: main-router           # Device to run iperf client on
  duration: 10                  # Test duration in seconds
  parallel: 4                   # Number of parallel streams
  protocol: tcp                 # tcp or udp
  reverse: false                # Reverse direction (server sends)
  bitrate: 100M                 # Target bitrate for UDP
  port: 5201                    # Iperf server port
```

**Fields:**

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `name` | Yes | - | Unique test name |
| `type` | Yes | - | Must be `iperf` |
| `server` | Yes | - | Device to run iperf3 server on |
| `client` | Yes | - | Device to run iperf3 client on |
| `duration` | No | 10 | Test duration in seconds |
| `parallel` | No | 1 | Number of parallel streams |
| `protocol` | No | tcp | Transport protocol (`tcp` or `udp`) |
| `reverse` | No | false | If true, server sends data to client |
| `bitrate` | No | - | Target bitrate for UDP (e.g., `100M`, `1G`) |
| `port` | No | 5201 | Iperf server port |

!!! note "iperf3 Required"
    Both server and client devices must have `iperf3` installed. On OpenWRT:
    ```bash
    opkg update && opkg install iperf3
    ```

## Iperf Test Orchestration

When you run an iperf test, wrtkit handles all the coordination automatically:

1. **Connect to server device** via SSH
2. **Start iperf3 server** in background mode with a PID file
3. **Wait for server** to be ready (1.5 seconds)
4. **Connect to client device** via SSH
5. **Run iperf3 client** with JSON output
6. **Parse results** from JSON output
7. **Stop server** and clean up PID file

This automation eliminates the need to manually SSH into devices and coordinate the server/client startup.

## Example Output

### Running Tests

```
$ wrtkit testing run tests.yaml

Running 3 test(s)...

Running: ping-router-to-ap
  Connecting to main-router...
  Running ping from main-router to 192.168.1.10...
Running: ping-internet
  Connecting to main-router...
  Running ping from main-router to 8.8.8.8...
Running: iperf-throughput
  Connecting to server (ap-living-room)...
  Starting iperf server on ap-living-room:5201...
  Connecting to client (main-router)...
  Running iperf test (10s)...
  Stopping iperf server...

============================================================
Results
============================================================

✓ PASS ping-router-to-ap
  Source: main-router → Destination: 192.168.1.10
  Packets: 10/10 received (0.0% loss)
  RTT: min=0.891ms avg=1.234ms max=2.105ms

✓ PASS ping-internet
  Source: main-router → Destination: 8.8.8.8
  Packets: 4/4 received (0.0% loss)
  RTT: min=12.345ms avg=15.678ms max=20.123ms

✓ PASS iperf-throughput
  Server: ap-living-room ← Client: main-router
  Protocol: TCP, Duration: 10.0s
  Sent: 112.45 MB @ 94.23 Mbps
  Received: 112.42 MB @ 94.21 Mbps
  Retransmits: 12

All 3 test(s) passed
```

### JSON Output

```bash
wrtkit testing run tests.yaml --json
```

```json
[
  {
    "name": "ping-router-to-ap",
    "type": "ping",
    "source": "main-router",
    "destination": "192.168.1.10",
    "packets_sent": 10,
    "packets_received": 10,
    "packet_loss_pct": 0.0,
    "rtt_min": 0.891,
    "rtt_avg": 1.234,
    "rtt_max": 2.105,
    "success": true,
    "error": null
  },
  {
    "name": "iperf-throughput",
    "type": "iperf",
    "server": "ap-living-room",
    "client": "main-router",
    "protocol": "tcp",
    "duration": 10.0,
    "sent_bytes": 117899264,
    "sent_bps": 94232000.0,
    "received_bytes": 117899264,
    "received_bps": 94210000.0,
    "retransmits": 12,
    "jitter_ms": null,
    "lost_packets": null,
    "lost_percent": null,
    "success": true,
    "error": null
  }
]
```

## Integration with Fleet Mode

Testing mode is designed to work seamlessly with fleet inventories. Your test configuration references the same fleet file used for configuration management:

```yaml
# fleet.yaml
defaults:
  timeout: 30
  username: root

devices:
  main-router:
    target: 192.168.1.1
    password: ${oc.env:ROUTER_PASSWORD}
    tags: [core]

  ap-living-room:
    target: 192.168.1.10
    key_file: ~/.ssh/openwrt_key
    tags: [ap]
```

```yaml
# tests.yaml
fleet_file: fleet.yaml

tests:
  - name: connectivity-test
    type: ping
    source: main-router
    destination: ap-living-room
    count: 5
```

Benefits:

- **Single source of truth** for device inventory
- **Consistent credentials** across configuration and testing
- **Device name abstraction** - reference `main-router` instead of remembering IPs

## Best Practices

### 1. Validate Before Running

Always validate your test configuration before running:

```bash
wrtkit testing validate tests.yaml
```

### 2. Start with Ping Tests

Use ping tests to verify basic connectivity before running bandwidth tests:

```yaml
tests:
  # First verify connectivity
  - name: verify-connectivity
    type: ping
    source: main-router
    destination: ap-living-room
    count: 3

  # Then test bandwidth
  - name: bandwidth-test
    type: iperf
    server: ap-living-room
    client: main-router
    duration: 10
```

### 3. Use Tags for Test Categories

Organize tests logically with naming conventions:

```yaml
tests:
  # Connectivity tests
  - name: ping-router-to-ap1
    type: ping
    # ...

  - name: ping-router-to-ap2
    type: ping
    # ...

  # Bandwidth tests
  - name: iperf-wired-throughput
    type: iperf
    # ...

  - name: iperf-wireless-throughput
    type: iperf
    # ...
```

Run specific tests:

```bash
wrtkit testing run tests.yaml --test ping-router-to-ap1
wrtkit testing run tests.yaml --test iperf-wired-throughput
```

### 4. Use JSON Output for Automation

For CI/CD or scripting, use JSON output:

```bash
wrtkit testing run tests.yaml --json > results.json

# Check if all tests passed
if jq -e 'all(.success)' results.json > /dev/null; then
    echo "All tests passed!"
else
    echo "Some tests failed!"
    exit 1
fi
```

### 5. Test Both Directions

For thorough bandwidth testing, test in both directions:

```yaml
tests:
  - name: iperf-router-to-ap
    type: iperf
    server: ap-living-room
    client: main-router
    duration: 10

  - name: iperf-ap-to-router
    type: iperf
    server: main-router
    client: ap-living-room
    duration: 10
```

## Troubleshooting

### iperf3 Not Found

```
Error: iperf3 not found on server device ap-living-room
```

Install iperf3 on the device:

```bash
ssh root@192.168.1.10 "opkg update && opkg install iperf3"
```

### Connection Refused

```
Error: Failed to connect to main-router: Connection refused
```

- Check that the device is reachable
- Verify SSH is enabled on the device
- Check credentials in the fleet file

### Iperf Server Already Running

If a previous test was interrupted, an iperf server might still be running:

```bash
ssh root@192.168.1.10 "pkill iperf3"
```

### Ping Permission Denied

On some systems, ping requires root or specific permissions. OpenWRT typically runs as root, so this shouldn't be an issue.

## Example Test Configuration

See [examples/tests.yaml](https://github.com/tlamadon/wrtkit/blob/main/examples/tests.yaml) for a complete example.

```yaml
# Complete test configuration example
fleet_file: fleet.yaml

tests:
  # Connectivity tests
  - name: ping-router-to-ap-living
    type: ping
    source: main-router
    destination: ap-living-room
    count: 10
    timeout: 5

  - name: ping-router-to-ap-office
    type: ping
    source: main-router
    destination: ap-office
    count: 5

  - name: ping-internet
    type: ping
    source: main-router
    destination: 8.8.8.8
    count: 4
    timeout: 2

  # Bandwidth tests
  - name: iperf-router-to-ap-tcp
    type: iperf
    server: ap-living-room
    client: main-router
    duration: 10
    parallel: 4
    protocol: tcp

  - name: iperf-udp-test
    type: iperf
    server: ap-office
    client: main-router
    duration: 5
    protocol: udp
    bitrate: 100M

  # Mesh performance test
  - name: iperf-ap-mesh
    type: iperf
    server: ap-office
    client: ap-living-room
    duration: 15
    parallel: 2
    protocol: tcp
```
