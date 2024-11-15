import sys
import time
import numpy as np
from GUI.serial_comm.clicker import EarSelect


# Board parameters
STANDARD_FREQUENCIES_DICT = {0: 250, 1: 500, 2: 1000, 3: 2000, 4: 4000, 5: 8000}
EVOKED_PATH = "saved_audiometries/evoked.npy"
NOISE_PATH = "saved_audiometries/noise.npy"
SAMPLINGRATE = 10_000


class Actions:
    RECORD = 0
    RESET = 1
    EXIT = 2

    def __iter__(self):
        yield Actions.RECORD
        yield Actions.RESET
        yield Actions.EXIT


def build_fake_patient_profile():
    audio_profile = {}
    for freq_index in STANDARD_FREQUENCIES_DICT:
        audio_profile[freq_index] = (np.random.randint(-5, 15), np.random.randint(-5, 15))
    return audio_profile


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
    fake_audio_limits = build_fake_patient_profile()
    stop = False
    while not stop:
        action, params = manage_input()
        match action:
            case Actions.RECORD:
                _, freq_index, ear, click_dbamp, _, _ = params
                audio_limit = fake_audio_limits[freq_index][0 if ear == EarSelect.LEFT else 1]
                out_path = EVOKED_PATH if click_dbamp >= audio_limit else NOISE_PATH
                # Simulate recording for 3 seconds, and write output
                # time.sleep(1)
                sys.stdout.write(out_path)
                sys.stdout.flush()
            case Actions.RESET:
                pass
            case Actions.EXIT:
                stop = True


if __name__ == '__main__':
    main()
