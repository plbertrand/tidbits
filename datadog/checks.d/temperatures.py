import json
import logging
import os
import re
import subprocess

try:
    from datadog_checks.base import AgentCheck
except ImportError:
    from checks import AgentCheck

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
            
            # Extract current drive temperature and other relevant temps
            if 'temperature' in smart_data:
                temp_data = smart_data['temperature']
                drive_temp_values = {}
                if 'current' in temp_data:
                    drive_temp_values['current'] = temp_data['current']
                if 'drive_trip' in temp_data:
                    drive_temp_values['crit'] = temp_data['drive_trip']

                if drive_temp_values:
                    drive_temps[device] = drive_temp_values
                else:
                    log.warning(f"No temperature data found in smartctl JSON output for {drive_path}")
            else:
                log.warning(f"Temperature section not found in smartctl JSON output for {drive_path}")
        except json.JSONDecodeError as e:
            log.warning(f"Could not decode JSON from smartctl output for {drive_path}: {e}")
        except KeyError as e:
            log.warning(f"Missing expected key in smartctl JSON output for {drive_path}: {e}")

    log.info(f"Successfully collected temperatures for {len(drive_temps)} drives.")
    return drive_temps

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
