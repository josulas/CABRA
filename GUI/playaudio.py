import simpleaudio as sa
import numpy as np
import matplotlib.pyplot as plt
import time

NCLICKS = 2000  
CYCLE_DURATION = 30 # ms (including pause)
CLICK_DURATION = 10 # ms
SAMPLINGRATE = 96_000 # Hz
MAXINT16 = 2**15 - 1 # Maximum value for a 16-bit integer

class Clicker(object):
    def __init__(self, 
                 freq: int=1000,
                 duration: int=CLICK_DURATION,
                 samplingrate: int=SAMPLINGRATE,
                 nclicks: int = NCLICKS,
                 smooth_period: float=0.05):
        self.freq = freq
        self.duration = duration # ms
        self.samplingrate = samplingrate
        self.nclicks = nclicks
        self.smooth_period = smooth_period
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

        Returns:
            np.ndarray: an array with the click
        """
        t = np.linspace(0, self.duration/1000, int(self.duration/1000 * self.samplingrate), False)
        click = np.sin(2 * np.pi * self.freq * t)
        if smooth:
            click[:int(self.smooth_period * len(click))] *= np.linspace(0, 1, int(self.smooth_period * len(click)), False)
            click[-int(self.smooth_period * len(click)):] *= np.linspace(0, 1, int(self.smooth_period * len(click)), False)[::-1]
        return np.int16(click*MAXINT16)
    
    def getSingleCycle(self) -> np.ndarray:
        """
        Generates a single cycle of a click + silence
        Returns:
            np.ndarray: an array with the single cycle
        """
        return np.concatenate([self.single_click, np.zeros(int((CYCLE_DURATION - CLICK_DURATION) / 1000 * self.samplingrate), np.int16)])


    def getToneBurst(self) -> np.ndarray:
        """
        Generates a tone burst of a given number of clicks

        Returns:
            np.ndarray: an array with the tone burst
        """
        return np.tile(self.single_cycle, self.nclicks)

    def playToneBurst(self, wait = True):
        """
        Plays the tone burst
        """
        play_obj = sa.play_buffer(self.tone_burst, 1, 2, self.samplingrate)
        play_obj.wait_done() if wait else None

if __name__ == "__main__":
    clicker = Clicker(freq=8000, nclicks=100)
    t = np.linspace(0, CYCLE_DURATION/1000, int(CYCLE_DURATION/1000 * SAMPLINGRATE), False)
    plt.plot(t, clicker.single_cycle)
    plt.show()
    a = time.time()
    clicker.playToneBurst()
    b = time.time()
    print((b - a) * 1000)