import simpleaudio as sa
import numpy as np
import wave


NCLICKS = 2000  
CYCLE_DURATION = 30 # ms (including pause)
CLICK_DURATION = 10 # ms
AUDIO_RATE = 48_000 # Hz


class EarSelect(object):
    RIGHT = 2
    LEFT = 3
    BOTH = 6
    def __iter__(self):
        yield EarSelect.RIGHT
        yield EarSelect.LEFT
        yield EarSelect.BOTH


class Clicker(object):
    F0 = 250 # Frequency of the click at whick NDB0VALF0 is defined
    NDB0VALF0 = 250 # ndB value for 0 amplitude at F0
    ALFA = -1.2
    MAXINT16 = 2**15 - 1 # Maximum value for a 16-bit integer
    
    def __init__(self, 
                 freq: int=1000,
                 cycle_duration: int=CYCLE_DURATION,
                 click_duration: int=CLICK_DURATION,
                 samplingrate: int=AUDIO_RATE,
                 nclicks: int = NCLICKS,
                 dbamp: int = 0,
                 ear: int = EarSelect.BOTH,
                 smooth_period_percentage: float=0.05,
                 ndB0val: float = NDB0VALF0):
        self.freq = freq
        self.cycle_duration = cycle_duration # ms
        self.click_duration = click_duration # ms
        self.samplingrate = samplingrate
        self.nclicks = nclicks
        self.ndb0val = ndB0val * (freq / Clicker.F0) ** Clicker.ALFA
        self.mindbamp = int(np.log10(1 / self.ndb0val) * 20)
        self.maxdbamp = int(np.log10(Clicker.MAXINT16 / self.ndb0val) * 20)
        if not self.mindbamp <= dbamp <= self.maxdbamp:
            raise ValueError(F"Amplitude should be between {self.mindbamp} and {self.maxdbamp} dB, got {dbamp} dB instead.")
        self.dbamp = dbamp
        if ear not in list(EarSelect()):
            raise ValueError(F"Ear should be one of {list(EarSelect())}, got {ear} instead.")
        self.ear = ear
        self.amp = self.ndb0val * 10 ** (dbamp / 20)
        self.smooth_period_percentage = smooth_period_percentage
        self.single_click = self.getSingleClick()
        self.single_cycle = self.getSingleCycle()
        self.tone_burst = self.getToneBurst()

    def getSingleClick(self, smooth: bool = True) -> np.ndarray:
        """
        Generates a click array of a given duration and sampling rate

        Args:
            duration (int): duration of the click in ms
            samplingrate (int): sampling rate of the click in Hz
            smooth (bool, optional): Indicates if the click should be smoothed. Defaults to True.
hh
        Returns:
            np.ndarray: an array with the click
        """
        t = np.linspace(0, self.click_duration/1000, int(self.click_duration/1000 * self.samplingrate), False)
        click = np.sin(2 * np.pi * self.freq * t)
        if smooth:
            click[:int(self.smooth_period_percentage * len(click))] *= np.linspace(0, 1, int(self.smooth_period_percentage * len(click)), False)
            click[-int(self.smooth_period_percentage * len(click)):] *= np.linspace(0, 1, int(self.smooth_period_percentage * len(click)), False)[::-1]
        return np.int16(click*self.amp)
    
    def getSingleCycle(self) -> np.ndarray:
        """
        Generates a single cycle of a click + silence
        Returns:
            np.ndarray: an array with the single cycle
        """
        return np.concatenate([self.single_click, np.zeros(int((self.cycle_duration - self.click_duration) / 1000 * self.samplingrate), np.int16)])

    def getToneBurst(self) -> np.ndarray:
        """
        Generates a tone burst of a given number of clicks

        Returns:
            np.ndarray: an array with the tone burst
        """
        return np.tile(self.single_cycle, self.nclicks)

    
    def saveToneBurst(self, filename: str):
        """
        Saves the tone burst to a file

        Args:
            filename (str): the name of the file
        """
        buffer = np.zeros(2 * len(self.tone_burst), np.int16)
        if not self.ear % EarSelect.LEFT:
            buffer[::2] = self.tone_burst
        if not self.ear % EarSelect.RIGHT:
            buffer[1::2] = self.tone_burst
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.samplingrate)
            wav_file.writeframes(buffer.tobytes())

    
    def playToneBurst(self, wait = True):
        """
        Plays the tone burst
        """
        buffer = np.zeros(2 * len(self.tone_burst), np.int16)
        if not self.ear % EarSelect.LEFT:
            buffer[::2] = self.tone_burst
        if not self.ear % EarSelect.RIGHT:
            buffer[1::2] = self.tone_burst
        play_obj = sa.play_buffer(buffer, 2, 2, self.samplingrate)
        play_obj.wait_done() if wait else None


if __name__ == "__main__":
    import os
    clicker = Clicker(freq=1000, nclicks=100, ear=EarSelect.LEFT, dbamp=40)
    clicker.saveToneBurst('~.wav')
    input()
    os.remove('~.wav')
