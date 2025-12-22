"""Tests for SQM configuration."""

from wrtkit.sqm import SQMConfig, SQMQueue
from wrtkit.base import UCICommand


def test_sqm_basic_configuration():
    """Test configuring a basic SQM queue."""
    sqm = SQMConfig()
    queue = SQMQueue("wan")\
        .with_interface("eth0")\
        .with_download(50000)\
        .with_upload(10000)\
        .with_qdisc("cake")\
        .with_script("piece_of_cake.qos")\
        .with_enabled(True)
    sqm.add_queue(queue)

    commands = sqm.get_commands()
    assert len(commands) == 7

    assert commands[0] == UCICommand("set", "sqm.wan", "queue")
    assert any(cmd.path == "sqm.wan.interface" and cmd.value == "eth0" for cmd in commands)
    assert any(cmd.path == "sqm.wan.download" and cmd.value == "50000" for cmd in commands)
    assert any(cmd.path == "sqm.wan.upload" and cmd.value == "10000" for cmd in commands)
    assert any(cmd.path == "sqm.wan.qdisc" and cmd.value == "cake" for cmd in commands)
    assert any(cmd.path == "sqm.wan.script" and cmd.value == "piece_of_cake.qos" for cmd in commands)
    assert any(cmd.path == "sqm.wan.enabled" and cmd.value == "1" for cmd in commands)


def test_sqm_disabled():
    """Test disabling an SQM queue."""
    sqm = SQMConfig()
    queue = SQMQueue("wan")\
        .with_interface("eth0")\
        .with_enabled(False)
    sqm.add_queue(queue)

    commands = sqm.get_commands()

    assert any(cmd.path == "sqm.wan.enabled" and cmd.value == "0" for cmd in commands)


def test_sqm_with_cake():
    """Test the CAKE convenience method."""
    queue = SQMQueue("wan")\
        .with_interface("eth0")\
        .with_cake(100000, 20000)\
        .with_enabled(True)

    sqm = SQMConfig()
    sqm.add_queue(queue)

    commands = sqm.get_commands()

    assert any(cmd.path == "sqm.wan.qdisc" and cmd.value == "cake" for cmd in commands)
    assert any(cmd.path == "sqm.wan.script" and cmd.value == "piece_of_cake.qos" for cmd in commands)
    assert any(cmd.path == "sqm.wan.download" and cmd.value == "100000" for cmd in commands)
    assert any(cmd.path == "sqm.wan.upload" and cmd.value == "20000" for cmd in commands)


def test_sqm_with_fq_codel():
    """Test the fq_codel convenience method."""
    queue = SQMQueue("wan")\
        .with_interface("eth0")\
        .with_fq_codel(50000, 10000)\
        .with_enabled(True)

    sqm = SQMConfig()
    sqm.add_queue(queue)

    commands = sqm.get_commands()

    assert any(cmd.path == "sqm.wan.qdisc" and cmd.value == "fq_codel" for cmd in commands)
    assert any(cmd.path == "sqm.wan.script" and cmd.value == "simple.qos" for cmd in commands)
    assert any(cmd.path == "sqm.wan.download" and cmd.value == "50000" for cmd in commands)
    assert any(cmd.path == "sqm.wan.upload" and cmd.value == "10000" for cmd in commands)


def test_sqm_with_link_layer():
    """Test link layer configuration."""
    queue = SQMQueue("wan")\
        .with_interface("eth0")\
        .with_cake(100000, 20000)\
        .with_link_layer("ethernet", 34)\
        .with_enabled(True)

    sqm = SQMConfig()
    sqm.add_queue(queue)

    commands = sqm.get_commands()

    assert any(cmd.path == "sqm.wan.linklayer" and cmd.value == "ethernet" for cmd in commands)
    assert any(cmd.path == "sqm.wan.overhead" and cmd.value == "34" for cmd in commands)


def test_sqm_multiple_queues():
    """Test configuring multiple SQM queues."""
    sqm = SQMConfig()

    wan_queue = SQMQueue("wan")\
        .with_interface("eth0")\
        .with_cake(100000, 20000)\
        .with_enabled(True)

    guest_queue = SQMQueue("guest")\
        .with_interface("eth1")\
        .with_fq_codel(25000, 5000)\
        .with_enabled(True)

    sqm.add_queue(wan_queue)
    sqm.add_queue(guest_queue)

    commands = sqm.get_commands()

    # Check both queues have section definitions
    assert any(cmd.path == "sqm.wan" and cmd.value == "queue" for cmd in commands)
    assert any(cmd.path == "sqm.guest" and cmd.value == "queue" for cmd in commands)

    # Check each queue has its own interface
    assert any(cmd.path == "sqm.wan.interface" and cmd.value == "eth0" for cmd in commands)
    assert any(cmd.path == "sqm.guest.interface" and cmd.value == "eth1" for cmd in commands)


def test_sqm_ecn_settings():
    """Test ECN configuration."""
    queue = SQMQueue("wan")\
        .with_interface("eth0")\
        .with_cake(100000, 20000)\
        .with_ingress_ecn("ECN")\
        .with_egress_ecn("NOECN")\
        .with_enabled(True)

    sqm = SQMConfig()
    sqm.add_queue(queue)

    commands = sqm.get_commands()

    assert any(cmd.path == "sqm.wan.ingress_ecn" and cmd.value == "ECN" for cmd in commands)
    assert any(cmd.path == "sqm.wan.egress_ecn" and cmd.value == "NOECN" for cmd in commands)


def test_sqm_with_speeds():
    """Test the with_speeds convenience method."""
    queue = SQMQueue("wan")\
        .with_interface("eth0")\
        .with_speeds(100000, 20000)\
        .with_qdisc("cake")\
        .with_script("piece_of_cake.qos")\
        .with_enabled(True)

    sqm = SQMConfig()
    sqm.add_queue(queue)

    commands = sqm.get_commands()

    assert any(cmd.path == "sqm.wan.download" and cmd.value == "100000" for cmd in commands)
    assert any(cmd.path == "sqm.wan.upload" and cmd.value == "20000" for cmd in commands)


def test_sqm_immutability():
    """Test that builder methods return new instances."""
    original = SQMQueue("wan")
    modified = original.with_download(50000)

    assert original.download is None
    assert modified.download == 50000
    assert original is not modified
