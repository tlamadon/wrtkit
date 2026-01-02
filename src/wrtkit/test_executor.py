"""Test execution logic for network testing."""

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

from .ssh import SSHConnection
from .serial_connection import SerialConnection
from .testing import ResolvedIperfTest, ResolvedPingTest, ResolvedTest

Connection = Union[SSHConnection, SerialConnection]


@dataclass
class PingResult:
    """Result of a ping test."""

    name: str
    source: str
    destination: str
    packets_sent: int = 0
    packets_received: int = 0
    packet_loss_pct: float = 100.0
    rtt_min: Optional[float] = None
    rtt_avg: Optional[float] = None
    rtt_max: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    raw_output: str = ""


@dataclass
class IperfResult:
    """Result of an iperf test."""

    name: str
    server: str
    client: str
    protocol: str = "tcp"
    duration: float = 0.0
    sent_bytes: int = 0
    sent_bps: float = 0.0
    received_bytes: int = 0
    received_bps: float = 0.0
    retransmits: Optional[int] = None
    jitter_ms: Optional[float] = None
    lost_packets: Optional[int] = None
    lost_percent: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    raw_output: str = ""


TestResult = Union[PingResult, IperfResult]


def _create_connection(params: Dict[str, Any]) -> Connection:
    """Create a connection from parameters dict."""
    target = params["target"]

    # Check if it's a serial port
    if target.startswith("/dev/") or target.upper().startswith("COM"):
        return SerialConnection(
            port=target,
            timeout=float(params.get("timeout", 30)),
            login_username=params.get("username", "root"),
            login_password=params.get("password"),
        )
    else:
        return SSHConnection(
            host=target,
            port=22,
            username=params.get("username", "root"),
            password=params.get("password"),
            key_filename=params.get("key_file"),
            timeout=params.get("timeout", 30),
        )


def _parse_ping_output(output: str) -> Dict[str, Any]:
    """
    Parse ping command output.

    Returns dict with:
        packets_sent, packets_received, packet_loss_pct,
        rtt_min, rtt_avg, rtt_max
    """
    result: Dict[str, Any] = {
        "packets_sent": 0,
        "packets_received": 0,
        "packet_loss_pct": 100.0,
        "rtt_min": None,
        "rtt_avg": None,
        "rtt_max": None,
    }

    # Parse packet statistics line
    # "4 packets transmitted, 4 packets received, 0% packet loss"
    stats_match = re.search(
        r"(\d+)\s+packets\s+transmitted,\s+(\d+)\s+(?:packets\s+)?received,\s+(\d+)%\s+packet\s+loss",
        output,
    )
    if stats_match:
        result["packets_sent"] = int(stats_match.group(1))
        result["packets_received"] = int(stats_match.group(2))
        result["packet_loss_pct"] = float(stats_match.group(3))

    # Parse RTT statistics line
    # "round-trip min/avg/max = 0.123/0.456/0.789 ms"
    # or "rtt min/avg/max/mdev = 0.123/0.456/0.789/0.012 ms"
    rtt_match = re.search(
        r"(?:round-trip|rtt)\s+min/avg/max(?:/mdev)?\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)",
        output,
    )
    if rtt_match:
        result["rtt_min"] = float(rtt_match.group(1))
        result["rtt_avg"] = float(rtt_match.group(2))
        result["rtt_max"] = float(rtt_match.group(3))

    return result


def _parse_iperf_json(output: str) -> Dict[str, Any]:
    """
    Parse iperf3 JSON output.

    Returns dict with test results.
    """
    result: Dict[str, Any] = {
        "duration": 0.0,
        "sent_bytes": 0,
        "sent_bps": 0.0,
        "received_bytes": 0,
        "received_bps": 0.0,
        "retransmits": None,
        "jitter_ms": None,
        "lost_packets": None,
        "lost_percent": None,
    }

    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return result

    # Check for error
    if "error" in data:
        return result

    end = data.get("end", {})

    # TCP results
    if "sum_sent" in end:
        sum_sent = end["sum_sent"]
        sum_received = end.get("sum_received", {})

        result["duration"] = sum_sent.get("seconds", 0.0)
        result["sent_bytes"] = sum_sent.get("bytes", 0)
        result["sent_bps"] = sum_sent.get("bits_per_second", 0.0)
        result["received_bytes"] = sum_received.get("bytes", 0)
        result["received_bps"] = sum_received.get("bits_per_second", 0.0)
        result["retransmits"] = sum_sent.get("retransmits")

    # UDP results
    elif "sum" in end:
        sum_data = end["sum"]
        result["duration"] = sum_data.get("seconds", 0.0)
        result["sent_bytes"] = sum_data.get("bytes", 0)
        result["sent_bps"] = sum_data.get("bits_per_second", 0.0)
        result["received_bytes"] = sum_data.get("bytes", 0)
        result["received_bps"] = sum_data.get("bits_per_second", 0.0)
        result["jitter_ms"] = sum_data.get("jitter_ms")
        result["lost_packets"] = sum_data.get("lost_packets")
        result["lost_percent"] = sum_data.get("lost_percent")

    return result


class TestExecutor:
    """Executes network tests on devices."""

    def __init__(
        self,
        on_test_start: Optional[Callable[[str], None]] = None,
        on_test_complete: Optional[Callable[[TestResult], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize test executor.

        Args:
            on_test_start: Callback when a test starts (receives test name)
            on_test_complete: Callback when a test completes (receives result)
            on_status: Callback for status updates (receives message)
        """
        self.on_test_start = on_test_start
        self.on_test_complete = on_test_complete
        self.on_status = on_status

    def _status(self, message: str) -> None:
        """Send status update."""
        if self.on_status:
            self.on_status(message)

    def run_ping_test(self, test: ResolvedPingTest) -> PingResult:
        """
        Execute a ping test.

        Args:
            test: Resolved ping test definition

        Returns:
            PingResult with test results
        """
        if self.on_test_start:
            self.on_test_start(test.name)

        result = PingResult(
            name=test.name,
            source=test.source_device,
            destination=test.destination,
        )

        try:
            self._status(f"Connecting to {test.source_device}...")
            conn = _create_connection(test.source_params)

            with conn:
                # Build ping command
                # OpenWRT uses busybox ping with slightly different options
                cmd = f"ping -c {test.count} -W {test.timeout} {test.destination}"
                if test.interval != 1.0:
                    # Note: busybox ping may not support -i for non-root
                    cmd = f"ping -c {test.count} -W {test.timeout} -i {test.interval} {test.destination}"

                self._status(f"Running ping from {test.source_device} to {test.destination}...")
                stdout, stderr, exit_code = conn.execute(cmd)

                result.raw_output = stdout + stderr

                # Parse output
                parsed = _parse_ping_output(stdout)
                result.packets_sent = parsed["packets_sent"]
                result.packets_received = parsed["packets_received"]
                result.packet_loss_pct = parsed["packet_loss_pct"]
                result.rtt_min = parsed["rtt_min"]
                result.rtt_avg = parsed["rtt_avg"]
                result.rtt_max = parsed["rtt_max"]

                # Success if we received any packets
                result.success = result.packets_received > 0

        except Exception as e:
            result.error = str(e)
            result.success = False

        if self.on_test_complete:
            self.on_test_complete(result)

        return result

    def run_iperf_test(self, test: ResolvedIperfTest) -> IperfResult:
        """
        Execute an iperf test.

        This orchestrates:
        1. Start iperf server on server device
        2. Wait for server to be ready
        3. Run iperf client on client device
        4. Collect results
        5. Stop iperf server

        Args:
            test: Resolved iperf test definition

        Returns:
            IperfResult with test results
        """
        if self.on_test_start:
            self.on_test_start(test.name)

        result = IperfResult(
            name=test.name,
            server=test.server_device,
            client=test.client_device,
            protocol=test.protocol,
        )

        server_conn: Optional[Connection] = None
        client_conn: Optional[Connection] = None
        server_started = False

        try:
            # Connect to server device
            self._status(f"Connecting to server ({test.server_device})...")
            server_conn = _create_connection(test.server_params)
            server_conn.connect()

            # Check if iperf3 is available on server
            stdout, stderr, exit_code = server_conn.execute("which iperf3")
            if exit_code != 0:
                raise RuntimeError(f"iperf3 not found on server device {test.server_device}")

            # Kill any existing iperf3 server on this port
            server_conn.execute(f"pkill -f 'iperf3.*-p {test.port}' 2>/dev/null || true")
            time.sleep(0.5)

            # Start iperf server in background
            self._status(f"Starting iperf server on {test.server_device}:{test.port}...")
            server_cmd = f"iperf3 -s -p {test.port} -D --pidfile /tmp/iperf3_{test.port}.pid"
            stdout, stderr, exit_code = server_conn.execute(server_cmd)

            if exit_code != 0:
                raise RuntimeError(f"Failed to start iperf server: {stderr}")

            server_started = True

            # Wait for server to be ready
            time.sleep(1.5)

            # Verify server is running
            stdout, stderr, exit_code = server_conn.execute(f"cat /tmp/iperf3_{test.port}.pid 2>/dev/null")
            if exit_code != 0:
                raise RuntimeError("iperf server failed to start (no PID file)")

            # Connect to client device
            self._status(f"Connecting to client ({test.client_device})...")
            client_conn = _create_connection(test.client_params)
            client_conn.connect()

            # Check if iperf3 is available on client
            stdout, stderr, exit_code = client_conn.execute("which iperf3")
            if exit_code != 0:
                raise RuntimeError(f"iperf3 not found on client device {test.client_device}")

            # Build client command
            client_cmd = f"iperf3 -c {test.server_target} -p {test.port} -t {test.duration} -J"

            if test.parallel > 1:
                client_cmd += f" -P {test.parallel}"

            if test.reverse:
                client_cmd += " -R"

            if test.protocol == "udp":
                client_cmd += " -u"
                if test.bitrate:
                    client_cmd += f" -b {test.bitrate}"

            # Run iperf client
            self._status(f"Running iperf test ({test.duration}s)...")
            stdout, stderr, exit_code = client_conn.execute(client_cmd)

            result.raw_output = stdout + stderr

            if exit_code != 0:
                # Try to extract error from JSON or stderr
                try:
                    data = json.loads(stdout)
                    if "error" in data:
                        raise RuntimeError(f"iperf error: {data['error']}")
                except json.JSONDecodeError:
                    pass
                raise RuntimeError(f"iperf client failed: {stderr}")

            # Parse results
            parsed = _parse_iperf_json(stdout)
            result.duration = parsed["duration"]
            result.sent_bytes = parsed["sent_bytes"]
            result.sent_bps = parsed["sent_bps"]
            result.received_bytes = parsed["received_bytes"]
            result.received_bps = parsed["received_bps"]
            result.retransmits = parsed["retransmits"]
            result.jitter_ms = parsed["jitter_ms"]
            result.lost_packets = parsed["lost_packets"]
            result.lost_percent = parsed["lost_percent"]
            result.success = True

        except Exception as e:
            result.error = str(e)
            result.success = False

        finally:
            # Clean up: stop iperf server
            if server_conn and server_started:
                self._status("Stopping iperf server...")
                try:
                    server_conn.execute(f"kill $(cat /tmp/iperf3_{test.port}.pid 2>/dev/null) 2>/dev/null || true")
                    server_conn.execute(f"rm -f /tmp/iperf3_{test.port}.pid")
                except Exception:
                    pass

            # Close connections
            if server_conn:
                try:
                    server_conn.disconnect()
                except Exception:
                    pass

            if client_conn:
                try:
                    client_conn.disconnect()
                except Exception:
                    pass

        if self.on_test_complete:
            self.on_test_complete(result)

        return result

    def run_test(self, test: ResolvedTest) -> TestResult:
        """
        Run a single test based on its type.

        Args:
            test: Resolved test definition

        Returns:
            Test result
        """
        if isinstance(test, ResolvedPingTest):
            return self.run_ping_test(test)
        elif isinstance(test, ResolvedIperfTest):
            return self.run_iperf_test(test)
        else:
            raise ValueError(f"Unknown test type: {type(test)}")

    def run_tests(self, tests: List[ResolvedTest]) -> List[TestResult]:
        """
        Run multiple tests sequentially.

        Args:
            tests: List of resolved test definitions

        Returns:
            List of test results
        """
        results: List[TestResult] = []

        for test in tests:
            result = self.run_test(test)
            results.append(result)

        return results


def format_ping_result(result: PingResult, use_color: bool = True) -> str:
    """Format a ping result for display."""
    lines = []

    # Status indicator
    if result.success:
        status = "\033[32m✓ PASS\033[0m" if use_color else "✓ PASS"
    else:
        status = "\033[31m✗ FAIL\033[0m" if use_color else "✗ FAIL"

    lines.append(f"{status} {result.name}")
    lines.append(f"  Source: {result.source} → Destination: {result.destination}")
    lines.append(
        f"  Packets: {result.packets_received}/{result.packets_sent} received "
        f"({result.packet_loss_pct:.1f}% loss)"
    )

    if result.rtt_avg is not None:
        lines.append(
            f"  RTT: min={result.rtt_min:.3f}ms avg={result.rtt_avg:.3f}ms max={result.rtt_max:.3f}ms"
        )

    if result.error:
        error_text = f"\033[31m{result.error}\033[0m" if use_color else result.error
        lines.append(f"  Error: {error_text}")

    return "\n".join(lines)


def format_iperf_result(result: IperfResult, use_color: bool = True) -> str:
    """Format an iperf result for display."""
    lines = []

    # Status indicator
    if result.success:
        status = "\033[32m✓ PASS\033[0m" if use_color else "✓ PASS"
    else:
        status = "\033[31m✗ FAIL\033[0m" if use_color else "✗ FAIL"

    lines.append(f"{status} {result.name}")
    lines.append(f"  Server: {result.server} ← Client: {result.client}")
    lines.append(f"  Protocol: {result.protocol.upper()}, Duration: {result.duration:.1f}s")

    if result.success:
        # Format bandwidth in human-readable units
        def format_bps(bps: float) -> str:
            if bps >= 1e9:
                return f"{bps / 1e9:.2f} Gbps"
            elif bps >= 1e6:
                return f"{bps / 1e6:.2f} Mbps"
            elif bps >= 1e3:
                return f"{bps / 1e3:.2f} Kbps"
            else:
                return f"{bps:.2f} bps"

        def format_bytes(b: int) -> str:
            if b >= 1e9:
                return f"{b / 1e9:.2f} GB"
            elif b >= 1e6:
                return f"{b / 1e6:.2f} MB"
            elif b >= 1e3:
                return f"{b / 1e3:.2f} KB"
            else:
                return f"{b} B"

        lines.append(f"  Sent: {format_bytes(result.sent_bytes)} @ {format_bps(result.sent_bps)}")
        lines.append(f"  Received: {format_bytes(result.received_bytes)} @ {format_bps(result.received_bps)}")

        if result.retransmits is not None:
            lines.append(f"  Retransmits: {result.retransmits}")

        if result.jitter_ms is not None:
            lines.append(f"  Jitter: {result.jitter_ms:.3f}ms")

        if result.lost_packets is not None:
            lines.append(
                f"  Lost: {result.lost_packets} packets ({result.lost_percent:.2f}%)"
            )

    if result.error:
        error_text = f"\033[31m{result.error}\033[0m" if use_color else result.error
        lines.append(f"  Error: {error_text}")

    return "\n".join(lines)


def format_result(result: TestResult, use_color: bool = True) -> str:
    """Format a test result for display."""
    if isinstance(result, PingResult):
        return format_ping_result(result, use_color)
    elif isinstance(result, IperfResult):
        return format_iperf_result(result, use_color)
    else:
        return f"Unknown result type: {type(result)}"
