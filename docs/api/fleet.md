# Fleet API Reference

The Fleet module provides classes and functions for managing multiple OpenWRT devices.

## Fleet Configuration

::: wrtkit.fleet.FleetDefaults
    options:
      show_source: true

::: wrtkit.fleet.FleetDevice
    options:
      show_source: true

::: wrtkit.fleet.FleetConfig
    options:
      show_source: true

## Fleet Functions

::: wrtkit.fleet.load_fleet
    options:
      show_source: true

::: wrtkit.fleet.merge_device_configs
    options:
      show_source: true

::: wrtkit.fleet.filter_devices
    options:
      show_source: true

::: wrtkit.fleet.get_device_connection_params
    options:
      show_source: true

## Fleet Executor

::: wrtkit.fleet_executor.DeviceResult
    options:
      show_source: true

::: wrtkit.fleet_executor.FleetResult
    options:
      show_source: true

::: wrtkit.fleet_executor.FleetExecutor
    options:
      show_source: true
      members:
        - __init__
        - preview
        - stage
        - commit
        - apply
        - cleanup
