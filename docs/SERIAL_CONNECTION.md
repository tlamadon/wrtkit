# Serial Connection Support

WRTKit now supports serial console connections in addition to SSH, making it perfect for:
- Initial device setup without network access
- Recovery scenarios when SSH is unavailable
- Development with devices connected via USB-to-serial adapters
- Compatibility with picocom, minicom, and other serial tools

## Quick Start

```python
from wrtkit import UCIConfig, SerialConnection
from wrtkit.network import NetworkInterface

# Create your configuration
config = UCIConfig()

# Add LAN interface with static IP
lan = NetworkInterface("lan")\
    .with_proto("static")\
    .with_ipaddr("192.168.1.1")\
    .with_netmask("255.255.255.0")
config.network.add_interface(lan)

# Connect via serial console
with SerialConnection(port="/dev/ttyUSB0", baudrate=115200) as serial:
    # Works exactly like SSH!
    diff = config.diff(serial)
    print(diff.to_tree())
    config.apply(serial)
```

## Features

✅ **Same Interface as SSH** - SerialConnection implements the same methods as SSHConnection
✅ **Auto-login Support** - Handles login prompts automatically if credentials provided
✅ **Prompt Detection** - Configurable regex for shell prompt detection
✅ **Exit Code Support** - Captures command exit codes via `echo $?`
✅ **Context Manager** - Use with `with` statement for automatic cleanup
✅ **Cross-platform** - Works on Linux, macOS, and Windows

## Connection Parameters

```python
SerialConnection(
    port="/dev/ttyUSB0",           # Serial port (required)
    baudrate=115200,                # Baud rate (default: 115200)
    timeout=5.0,                    # Command timeout in seconds
    prompt=r"root@[^:]+:.*[#\$]",  # Shell prompt regex pattern
    login_username=None,            # Login username (if needed)
    login_password=None,            # Login password (if needed)
)
```

## Common Serial Ports

- **Linux**: `/dev/ttyUSB0`, `/dev/ttyACM0`, `/dev/ttyS0`
- **macOS**: `/dev/tty.usbserial-*`, `/dev/cu.usbserial-*`
- **Windows**: `COM3`, `COM4`, `COM5`, etc.

## Common Baudrates

- 9600, 19200, 38400, 57600, **115200** (most common for OpenWRT), 230400

## Permissions (Linux)

Add your user to the `dialout` group to access serial ports:

```bash
sudo usermod -a -G dialout $USER
# Log out and back in for changes to take effect
```

## Troubleshooting

### "Permission denied" error
- Add your user to the `dialout` group (see above)
- Or run with `sudo` (not recommended)

### "Port already in use" error
- Close other programs using the port (picocom, minicom, screen, etc.)
- Check with: `lsof | grep ttyUSB`

### No response / timeout
- Verify the baudrate matches your device (try 9600, 57600, 115200)
- Check the port with: `ls -l /dev/ttyUSB*`
- Test with picocom: `picocom -b 115200 /dev/ttyUSB0`

### Login not working
- Provide `login_username` and `login_password` parameters
- Check if prompt pattern matches your shell

## Examples

See `examples/serial_example.py` in the repository for a complete working example.

## Implementation Details

The `SerialConnection` class uses `pyserial` to communicate with the device via serial port. It:

1. Opens the serial port with specified parameters
2. Handles login if credentials are provided
3. Sends commands and waits for the shell prompt
4. Captures command output and exit codes
5. Provides the same interface as `SSHConnection` for compatibility

All WRTKit features (diff, apply, commit, reload) work identically over serial as they do over SSH!
