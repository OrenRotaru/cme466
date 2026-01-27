import multiprocessing as mp
from jsonschema import validate, ValidationError
import json

try:
    with open('command_schema.json', 'r') as f:
        COMMAND_SCHEMA = json.load(f)
except FileNotFoundError:
    print("Error: command_schema.json not found in root directory.")
    COMMAND_SCHEMA = None

def parse_and_validate_command(command: str) -> dict | None:
  """ parse and validate a command from the command queue """
  try:
    data = json.loads(command)
    validate(data, COMMAND_SCHEMA)
    return data
  except json.JSONDecodeError:
    print(f"Error decoding command: {command}")
    return None
  except ValidationError as e:
    print(f"Error validating command: {e}")
    return None

def gpio_main(command_queue: mp.Queue, telemetry_queue: mp.Queue):
  while True:
    if not command_queue.empty():
      command = command_queue.get()
      process_command(command)

    # TODO: periodically read telemetry from sensors and add to telemetry queue



def process_command(command: dict):
  """ process a command from the command queue """
  data = parse_and_validate_command(command)

  if data is None:
    return

  if data["command"] == "display_to_console":
    display_to_console(data["message"])
  elif data["command"] == "warning":
    warning(data["state"])
  else:
    print(f"Invalid command: {data['command']}")


def display_to_console(message: str):
  """ display a message to the console """
  print(f"Displaying message: {message}")

def warning(state: str):
  """ toggle the warning system """
  if state == "on":
    print("Warning system enabled")
    # TODO: enable warning system (turn on the led on and off flashing)
  elif state == "off":
    print("Warning system disabled")
    # TODO: disable warning system (turn off the led and stop the flashing)
  else:
    print(f"Invalid warning state: {state}")

