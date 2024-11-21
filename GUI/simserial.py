import os
import sys
import time
import numpy as np
from clicker import EarSelect, Clicker
import subprocess



# Board parameters
STANDARD_FREQUENCIES_DICT = {0: 250, 1: 500, 2: 1000, 3: 2000, 4: 4000, 5: 8000}
EVOKED_PATH = "simulated_signals/evoked.npy"
NOISE_PATH = "simulated_signals/noise.npy"
SAMPLINGRATE = 8_000

# Player parameters
# Path to the C executable
PLAYER_PATH_WINDOWS = "audio_playback.exe"
PLAYER_PATH_LINUX = "./audio_playback_linux"
TEMP_FILE = "~.wav"

class Actions:
    RECORD = 0
    RESET = 1
    EXIT = 2

    def __iter__(self):
        yield Actions.RECORD
        yield Actions.RESET
        yield Actions.EXIT

class Simulator:
    """
    Simulates the operation of the board
    """

    def __init__(self, clicker: Clicker):
        self.clicker = clicker
        self.player = self._init_player()
        self.audio_profile = self.build_fake_patient_profile()

    @staticmethod
    def build_fake_patient_profile():
        audio_profile = {}
        for freq_index in STANDARD_FREQUENCIES_DICT:
            audio_profile[freq_index] = (np.random.randint(-5, 15), np.random.randint(-5, 15))
        return audio_profile

    def _init_player(self):
        platform_name = sys.platform
        if platform_name == 'win32':
            return subprocess.Popen([PLAYER_PATH_WINDOWS], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
        elif platform_name == 'linux':
            return subprocess.Popen([PLAYER_PATH_LINUX], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)
        else:
            raise OSError(F"Platform {platform_name} not supported")

    def set_clicker(self, clicker: Clicker):
        """
        Set the clicker
        :param clicker: new clicker
        """
        self.clicker = clicker

    def send_command(self, command: str, expected_response: str):
        """
        Send the command to the player
        """
        self.player.stdin.write(command + "\n")
        self.player.stdin.flush()
        response = self.player.stdout.readline().strip()
        return response == expected_response

    def simulate_recording(self):
        """
        Simply plays the audio
        """
        self.clicker.saveToneBurst(TEMP_FILE)
        self.send_command(TEMP_FILE, "U")
        self.send_command("L", "D")
        response = self.send_command("S", "F")
        if not response:
            raise ValueError("Error in the player")
        # Simulate recording by sleeping while the audio plays
        sleep_time = self.clicker.cycle_duration * self.clicker.nclicks / 1000
        time.sleep(sleep_time)


def manage_input():
    """
    Data receiving operation
    arg0: action
    if arg0 == Actions.RECORD:
        arg1: nclicks
        arg2: freq_index
        arg3: ear
        arg4: click_dbamp    (db)
        arg5: click_duration (ms)
        arg6: cycle_duration (ms)
    """
    try:
        control = sys.stdin.readline().split()
        action = int(control[0])
        if action not in list(Actions()):
            raise ValueError(F"Action should be one of {list(Actions())}, got {action} instead.")
        if action == Actions.RECORD:
            nclicks = int(control[1])
            if nclicks < 1:
                raise ValueError(F"Number of clicks should be greater than 1, got {nclicks} instead.")
            freq_index = int(control[2])
            if freq_index not in STANDARD_FREQUENCIES_DICT:
                raise ValueError(F"Frequency index should be one of {list(STANDARD_FREQUENCIES_DICT.keys())}, got {freq_index} instead.")
            ear = int(control[3])
            if ear not in list(EarSelect()):
                raise ValueError(F"Ear should be one of {list(EarSelect())}, got {ear} instead.")
            click_dbamp = int(control[4])
            if not -10 <= click_dbamp <= 40:
                raise ValueError(F"Click amplitude should be between -10 and 40 dB, got {click_dbamp} instead.")
            click_duration = int(control[5])
            if click_duration < 1:
                raise ValueError(F"Click duration should be greater than 1, got {click_duration} instead.")
            cycle_duration = int(control[6])
            if cycle_duration < click_duration:
                raise ValueError(F"Cycle duration should be greater than click duration, got {cycle_duration} instead.")
            return action, [nclicks, freq_index, ear, click_dbamp, click_duration, cycle_duration]
        else:
            return action, None
    except ValueError:
        sys.stderr.write('3')
        sys.stderr.flush()
        return None, None
    except KeyboardInterrupt:
        return Actions.EXIT, None
    except IndexError:
        sys.stderr.write('3')
        sys.stderr.flush()
        return None, None


def main():
    # SIM SETUP
    # print("SIMULATION STARTED\n")
    simulator = Simulator(Clicker())
    fake_audio_limits = simulator.audio_profile
    stop = False
    while not stop:
        action, params = manage_input()
        match action:
            case Actions.RECORD:
                nclicks, freq_index, ear, click_dbamp, click_duration, cycle_duration = params
                frequency = STANDARD_FREQUENCIES_DICT[freq_index]
                clicker = Clicker(freq=frequency,
                                  ear=ear,
                                  dbamp=click_dbamp,
                                  click_duration=click_duration,
                                  cycle_duration=cycle_duration,
                                  nclicks=nclicks)
                simulator.set_clicker(clicker)

                # Play clicks and simulate recording
                simulator.simulate_recording()
                # 0 500 5 3 20 10 30
                # Write the path to the corresponding file
                audio_limit = fake_audio_limits[freq_index][0 if ear == EarSelect.LEFT else 1]
                out_path = EVOKED_PATH if click_dbamp >= audio_limit else NOISE_PATH
                n_reps = np.random.randint(nclicks//2, nclicks)
                msg = f"{out_path};{n_reps}"
                sys.stdout.write(msg)
                sys.stdout.flush()
            case Actions.RESET:
                pass
            case Actions.EXIT:
                # Delete temporary file and quit
                os.remove(TEMP_FILE)
                stop = True


if __name__ == '__main__':
    main()
