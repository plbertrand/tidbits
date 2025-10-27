import json
import logging
import os
import re
import subprocess

try:
    from datadog_checks.base import AgentCheck
except ImportError:
    try:
        from checks import AgentCheck
    except ImportError:
        # Define a dummy AgentCheck for testing purposes if not found
        class AgentCheck:
            def gauge(self, metric, value, tags=None):
                pass
            def log(self, *args, **kwargs):
                pass
            def info(self, *args, **kwargs):
                pass
            def debug(self, *args, **kwargs):
                pass
            def warning(self, *args, **kwargs):
                pass
            def error(self, *args, **kwargs):
                pass

__version__ = "1.0.0"


def parse_sensors(data):
    """
    Parses the sensor data and returns a dictionary of sensor names and temperatures.
    """
    sensors = {}
    sensor_blocks = data.strip().split('\n\n')
    log = logging.getLogger(__name__)
    log.debug("Sensor blocks: %s", sensor_blocks)
    for block in sensor_blocks:
        log.debug("Processing block: %s", block)
        lines = block.strip().split('\n')
        sensor_name = lines[0].strip()
        log.debug("Sensor name: %s", sensor_name)
        sensors[sensor_name] = []
        for i, line in enumerate(lines[1:]):
            log.debug("Processing line: %s", line)
            line = line.strip()
            if not line:
                continue

            temp_match = re.search(r'(.+?):\s*\+?(-?\d+\.\d+) C', line)
            if temp_match:
                log.debug("Temp match found: %s", temp_match.groups())
                component = temp_match.group(1).strip()
                temperature = float(temp_match.group(2))                
                sensor_data = {'component': component, 'temp': temperature}
                
                full_line = line
                if i + 2 < len(lines):
                    full_line += lines[i + 2].strip()

                low_match = re.search(r'low\s*=\s*\+?(-?\d+\.\d+)', full_line)
                high_match = re.search(r'high\s*=\s*\+?(-?\d+\.\d+)', full_line)
                crit_match = re.search(r'crit\s*=\s*\+?(-?\d+\.\d+)', full_line)

                if low_match:
                    sensor_data['low'] = float(low_match.group(1))
                if high_match:
                    sensor_data['high'] = float(high_match.group(1))
                if crit_match:
                    sensor_data['crit'] = float(crit_match.group(1))

                sensors[sensor_name].append(sensor_data)
    return sensors


def get_drive_temperatures(log):
    """
    Finds all hard drives, runs smartctl on them in parallel with JSON output, and returns their temperatures.
    """
    log.info("Starting hard drive temperature collection.")
    drive_temps = {}
    processes = {}
    drive_paths = [os.path.join('/dev', device) for device in sorted(os.listdir('/dev')) if re.match(r'^sd[a-z]$', device)]
    log.info(f"Found {len(drive_paths)} drives to check.")
    log.debug(f"Drive paths: {drive_paths}")

    for drive_path in drive_paths:
        device = os.path.basename(drive_path)
        try:
            # Start smartctl process for each drive in parallel
            processes[device] = subprocess.Popen(['sudo', 'smartctl', '--json', '-A', drive_path], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            log.warning(f"Could not run smartctl for {drive_path}: {e}")

    for device, process in processes.items():
        drive_path = os.path.join('/dev', device)
        try:
            # Wait for the process to complete and get the output
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                log.warning(f"smartctl for {drive_path} returned non-zero exit code {process.returncode}. Stdout: {stdout.strip()}. Stderr: {stderr.strip()}")
                continue

            # Parse JSON output
            smart_data = json.loads(stdout)
            log.debug(f"Smart data for {drive_path}: {json.dumps(smart_data, indent=2)}")
            
            # Extract current drive temperature and other relevant temps
            drive_temp_values = {}
            # Try to extract temperature using the new helper function first
            current_temp = _extract_temperature_from_smart_data(smart_data, log)
            log.debug(f"Extracted current_temp for {drive_path}: {current_temp}")
            if current_temp is not None:
                drive_temp_values['current'] = current_temp
                # Attempt to get 'crit' from the top-level 'temperature' section if available
                if 'temperature' in smart_data and 'drive_trip' in smart_data['temperature']:
                    drive_temp_values['crit'] = smart_data['temperature']['drive_trip']
            elif 'temperature' in smart_data: # Fallback to original logic if helper didn't find anything
                temp_data = smart_data['temperature']
                if 'current' in temp_data:
                    drive_temp_values['current'] = temp_data['current']
                if 'drive_trip' in temp_data:
                    drive_temp_values['crit'] = temp_data['drive_trip']
            log.debug(f"Final drive_temp_values for {drive_path}: {drive_temp_values}")

            if drive_temp_values:
                drive_temps[device] = drive_temp_values
            else:
                log.warning(f"No temperature data found in smartctl JSON output for {drive_path}")
        except json.JSONDecodeError as e:
            log.warning(f"Could not decode JSON from smartctl output for {drive_path}: {e}")
        except KeyError as e:
            log.warning(f"Missing expected key in smartctl JSON output for {drive_path}: {e}")

    log.info(f"Successfully collected temperatures for {len(drive_temps)} drives.")
    return drive_temps


def _extract_temperature_from_smart_data(smart_data, log):
    """
    Extracts temperature from smartctl JSON output, trying different known locations.
    """
    # Try to extract from ata_smart_attributes.table (e.g., for HDDs/SSDs)
    if 'ata_smart_attributes' in smart_data and 'table' in smart_data['ata_smart_attributes']:
        for attr in smart_data['ata_smart_attributes']['table']:
            if 'name' in attr and attr['name'] == 'Temperature_Celsius' and 'value' in attr:
                log.debug("Found Temperature_Celsius in ata_smart_attributes.table")
                return attr['value']

    # Fallback to top-level 'temperature' section (e.g., for NVMe drives)
    if 'temperature' in smart_data and 'current' in smart_data['temperature']:
        log.debug("Found current temperature in top-level 'temperature' section")
        return smart_data['temperature']['current']

    log.debug("No temperature found in known locations within smartctl JSON output.")
    return None

class TemperaturesCheck(AgentCheck):
    def __init__(self, name, init_config, agentConfig, instances):
        super(TemperaturesCheck, self).__init__(name, init_config, agentConfig, instances)
        self.log_file_path = instances[0].get('log_file', '/tmp/temp_check.log')
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.DEBUG)
        handler = logging.FileHandler(self.log_file_path)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        if handler not in self.log.handlers:
            self.log.addHandler(handler)

    def _read_thermal_zone(self, zone):
        path = f"/sys/class/thermal/thermal_zone{zone}/temp"
        try:
            with open(path, "r") as f:
                return int(f.read().strip()) / 1000
        except (IOError, ValueError) as e:
            self.log.debug("Cannot read temperature from %s: %s", path, e)
            return None

    def _read_all_thermal_zones(self):
        thermal_zones = []
        thermal_zones_path = "/sys/class/thermal/"
        if os.path.exists(thermal_zones_path):
            for zone_dir in os.listdir(thermal_zones_path):
                if zone_dir.startswith("thermal_zone"):
                    zone_id = zone_dir.replace("thermal_zone", "")
                    cpu_temp = self._read_thermal_zone(zone_id)
                    if cpu_temp is not None:
                        thermal_zones.append({"zone_id": zone_id, "temp": cpu_temp})
        return thermal_zones

    def check(self, instance):
        reported_metrics = []

        self.log.info("Starting temperatures check.") # Added for guaranteed visibility

        try:
            sensors_output = subprocess.check_output(["sensors"], universal_newlines=True)
        except (OSError, subprocess.CalledProcessError) as e:
            self.log.error("Unable to run 'sensors' command: %s", e)
            # Do not return here, as we might still be able to read thermal zones
        else:
            self.log.info("Successfully ran 'sensors' command.")
            parsed_sensors = parse_sensors(sensors_output)
            self.log.info("Parsed sensors: %s", parsed_sensors)

            for sensor_name, sensor_data_list in parsed_sensors.items():
                self.log.info("Processing sensor: %s", sensor_name)
                for sensor_data in sensor_data_list:
                    tags = [f"sensor:{sensor_name}", f"component:{sensor_data['component']}"]
                    if 'temp' in sensor_data:
                        self.gauge("custom.temperature.temp", sensor_data['temp'], tags=tags)
                    if 'low' in sensor_data:
                        self.gauge("custom.temperature.low", sensor_data['low'], tags=tags)
                        reported_metrics.append({"metric": "custom.temperature.low", "value": sensor_data['low'], "tags": tags})
                    if 'high' in sensor_data:
                        self.gauge("custom.temperature.high", sensor_data['high'], tags=tags)
                        reported_metrics.append({"metric": "custom.temperature.high", "value": sensor_data['high'], "tags": tags})
                    if 'crit' in sensor_data:
                        self.gauge("custom.temperature.crit", sensor_data['crit'], tags=tags)
                        reported_metrics.append({"metric": "custom.temperature.crit", "value": sensor_data['crit'], "tags": tags})

                    # If it's an NVMe drive, also report the special metrics
                    self.log.info("Checking for NVMe sensor: %s", sensor_name)
                    if "nvme" in sensor_name:
                        self.log.info("NVMe sensor detected: %s", sensor_name)
                        nvme_tags = [f"drive:{sensor_name}"]
                        self.log.info("NVMe tags: %s", nvme_tags)
                        self.log.info("NVMe sensor_data: %s", sensor_data)
                        if 'temp' in sensor_data:
                            self.gauge("custom.temperature.nvme.current", sensor_data['temp'], tags=nvme_tags)
                            reported_metrics.append({"metric": "custom.temperature.nvme.current", "value": sensor_data['temp'], "tags": nvme_tags})
                        if 'low' in sensor_data:
                            self.gauge("custom.temperature.nvme.low", sensor_data['low'], tags=nvme_tags)
                            reported_metrics.append({"metric": "custom.temperature.nvme.low", "value": sensor_data['low'], "tags": nvme_tags})
                        if 'high' in sensor_data:
                            self.gauge("custom.temperature.nvme.high", sensor_data['high'], tags=nvme_tags)
                            reported_metrics.append({"metric": "custom.temperature.nvme.high", "value": sensor_data['high'], "tags": nvme_tags})
                        if 'crit' in sensor_data:
                            self.gauge("custom.temperature.nvme.crit", sensor_data['crit'], tags=nvme_tags)
                            reported_metrics.append({"metric": "custom.temperature.nvme.crit", "value": sensor_data['crit'], "tags": nvme_tags})

        # Collect CPU temperatures from thermal zones
        all_thermal_zones = self._read_all_thermal_zones()
        for zone in all_thermal_zones:
            self.gauge("custom.temperature.cpu", zone['temp'], tags=[f"cpu:{zone['zone_id']}"])
            reported_metrics.append({"metric": "custom.temperature.cpu", "value": zone['temp'], "tags": [f"cpu:{zone['zone_id']}"]})

        hdd_temps = get_drive_temperatures(self.log)
        for drive, temps_dict in hdd_temps.items():
            tags = [f"drive:{drive}"]
            if 'current' in temps_dict:
                self.gauge("custom.temperature.hdd.current", temps_dict['current'], tags=tags)
                reported_metrics.append({"metric": "custom.temperature.hdd.current", "value": temps_dict['current'], "tags": tags})
            if 'crit' in temps_dict:
                self.gauge("custom.temperature.hdd.crit", temps_dict['crit'], tags=tags)
                reported_metrics.append({"metric": "custom.temperature.hdd.crit", "value": temps_dict['crit'], "tags": tags})

        self.log.info("--- Metrics Exported Summary ---")
        for metric_data in reported_metrics:
            self.log.info(f"Metric: {metric_data['metric']}, Value: {metric_data['value']}, Tags: {metric_data['tags']}")
        self.log.info("--- End of Metrics Summary ---")

import unittest
from unittest.mock import Mock

class TestTemperatureExtraction(unittest.TestCase):
    def test_extract_temperature_from_smart_data_new_machine(self):
        mock_smart_data = {
            "json_format_version": [1, 0],
            "smartctl": {
                "version": [7, 3],
                "svn_revision": "5338",
                "platform_info": "x86_64-linux-6.8.12-15-pve",
                "build_info": "(local build)",
                "argv": ["smartctl", "--json", "-A", "/dev/sda"],
                "drive_database_version": {"string": "7.3/5319"},
                "exit_status": 0
            },
            "local_time": {
                "time_t": 1761580032,
                "asctime": "Mon Oct 27 10:47:12 2025 EST"
            },
            "device": {
                "name": "/dev/sda",
                "info_name": "/dev/sda [SAT]",
                "type": "sat",
                "protocol": "ATA"
            },
            "ata_smart_attributes": {
                "revision": 10,
                "table": [
                    {
                        "id": 1,
                        "name": "Raw_Read_Error_Rate",
                        "value": 67,
                        "worst": 64,
                        "thresh": 44,
                        "when_failed": "",
                        "flags": {"value": 15, "string": "POSR-- ", "prefailure": True, "updated_online": True, "performance": True, "error_rate": True, "event_count": False, "auto_keep": False},
                        "raw": {"value": 4983200, "string": "4983200"}
                    },
                    {
                        "id": 194,
                        "name": "Temperature_Celsius",
                        "value": 36,
                        "worst": 44,
                        "thresh": 0,
                        "when_failed": "",
                        "flags": {"value": 34, "string": "-O---K ", "prefailure": False, "updated_online": True, "performance": False, "error_rate": False, "event_count": False, "auto_keep": True},
                        "raw": {"value": 42949672996, "string": "36 (0 10 0 0 0)"}
                    },
                    {
                        "id": 197,
                        "name": "Current_Pending_Sector",
                        "value": 100,
                        "worst": 100,
                        "thresh": 0,
                        "when_failed": "",
                        "flags": {"value": 18, "string": "-O--C- ", "prefailure": False, "updated_online": True, "performance": False, "error_rate": False, "event_count": True, "auto_keep": False},
                        "raw": {"value": 0, "string": "0"}
                    }
                ]
            },
            "power_on_time": {"hours": 14500},
            "power_cycle_count": 98,
            "temperature": {"current": 35}
        }
        mock_log = Mock()
        
        # Test extraction from ata_smart_attributes.table
        extracted_temp = _extract_temperature_from_smart_data(mock_smart_data, mock_log)
        self.assertEqual(extracted_temp, 36)

        # Test fallback to top-level 'temperature' if ata_smart_attributes.table doesn't have Temperature_Celsius
        mock_smart_data_no_attr_temp = mock_smart_data.copy()
        mock_smart_data_no_attr_temp['ata_smart_attributes']['table'] = [
            attr for attr in mock_smart_data_no_attr_temp['ata_smart_attributes']['table']
            if attr['name'] != 'Temperature_Celsius'
        ]
        extracted_temp_fallback = _extract_temperature_from_smart_data(mock_smart_data_no_attr_temp, mock_log)
        self.assertEqual(extracted_temp_fallback, 35) # Expecting 35 from top-level 'temperature'

        # Test no temperature found
        mock_smart_data_no_temp = mock_smart_data_no_attr_temp.copy()
        del mock_smart_data_no_temp['temperature']
        extracted_temp_none = _extract_temperature_from_smart_data(mock_smart_data_no_temp, mock_log)
        self.assertIsNone(extracted_temp_none)

if __name__ == '__main__':
    unittest.main()