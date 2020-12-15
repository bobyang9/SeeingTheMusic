import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import scipy
import scipy.io.wavfile
import wave
import scipy.signal
import celluloid
from celluloid import Camera
from matplotlib.animation import FuncAnimation
import time
import random
import ffmpeg
import sys


def get_bin_average(column_no, bin_start, bin_end, Zxx):
    """
    get_bin_average gets the average of a range of elements in a particular frame (aka column) in Zxx
    to calculate the value for one bin in one frame

    Input: column_no - the timestep number in Zxx to take the average of
           bin_start - the row number (counting from 0 Hz) that is the start of the range to
                       take an average over for a bin (inclusive)
           bin_end   - the end of the range (exclusive) starting in bin_start
           Zxx       - the frequency domain 2DArray output from scipy short-time Fourier transform
    Output: average of range of rows from bin_start to bin_end in the column column_no
    """
    return np.average(Zxx[bin_start:bin_end, column_no])


def wav_to_bins(filename, mono, bin_boundaries):
    """
    wav_to_bins converts a wav file to frequency-domain using short-time Fourier
    transform (STFT) and then bins the result.
    Input: filename - name of .WAV file to input
           mono - a value in {True, False}. If True, signifies one channel; if False, signifies two channels.
           bin_boundaries - an array specifying the boundaries of each bin
    Output: an array of bins with dimension (number of bins, number of frames)
    """
    rate, data = scipy.io.wavfile.read(filename)
    f0, t0, Zxx0 = scipy.signal.stft(data[:, 0], fs=rate, window='hann', nperseg=8192, noverlap=6721, nfft=None,
                                     detrend=False, return_onesided=True, boundary='zeros', padded=True, axis=- 1)
    zeros = np.zeros((Zxx0.shape[0], 1))
    Zxx0 = np.concatenate((Zxx0, zeros), axis=1)
    Zxx0 = np.flip(Zxx0, axis=0)

    bins0 = np.zeros((len(bin_boundaries) - 1, Zxx0.shape[1]))

    for column in range(Zxx0.shape[1]):
        for i in range(len(bins0)):
            bins0[i, column] = np.abs(get_bin_average(column, bin_boundaries[i], bin_boundaries[i + 1], Zxx0))

    bins0 = normalization_and_zooming(bins0)

    if (mono == False):
        f1, t1, Zxx1 = scipy.signal.stft(data[:, 1], fs=rate, window='hann', nperseg=8192, noverlap=6721, nfft=None,
                                         detrend=False, return_onesided=True, boundary='zeros', padded=True, axis=- 1)
        zeros = np.zeros((Zxx1.shape[0], 1))
        Zxx1 = np.concatenate((Zxx1, zeros), axis=1)
        Zxx1 = np.flip(Zxx1, axis=0)

        bins1 = np.zeros((len(bin_boundaries) - 1, Zxx1.shape[1]))

        for column in range(Zxx1.shape[1]):
            for i in range(len(bins1)):
                bins1[i, column] = np.abs(get_bin_average(column, bin_boundaries[i], bin_boundaries[i + 1], Zxx1))

        bins1 = normalization_and_zooming(bins1)

    if (mono == False):
        return (bins0, bins1)
    else:
        return bins0


def normalization_and_zooming(bins):
    """
    normalization_and_zooming operates on the bins array in the following manner:
        0. takes log of the array for better representation of sound magnitude
        1. sets undefined numbers to the minimum of the array
        2. normalizes minimum of array to 0 and maximum of array to 1
        3. zooms in to the top 75% of the array for greater effect
    Input: bins - (number of bins, number of frames) shape array
    Output: normalized, zoomed in version of log(bins)
    """
    bins[bins == 0] = 1
    bins = np.log(bins)
    # Normalization
    bins[bins == 0] = np.amin(bins)
    bins = bins - np.amin(bins)
    bins = bins / np.amax(bins)
    # Zooming in
    bins[bins < 0.25] = 0.25
    bins = bins - 0.25
    bins = bins / np.amax(bins)
    return bins


def find_points(threshold, horizon):
    """
    Used for the beat detection feature. find_points uses non-maximum suppression to find emphasis points.
    Input: threshold - used to evaluate if each point should be added to the list of emphasis points
           horizon   - how far on each side to look
    Output: list of emphasis points
    """
    test1 = np.average(bins0, axis=0)
    keep = []
    for i in range(test1.shape[0]):
        neighbors = test1[max(0, i - horizon):min(test1.shape[0], i + horizon + 1)]
        num_geq = 0
        for neighbor in neighbors:
            if (neighbor >= test1[i]):
                num_geq += 1
        result = (num_geq - 1) / (neighbors.shape[0] - 1)
        if (result >= threshold):
            keep.append(i)
    return keep


def bar_mode(bins, names, save_name):
    """
    Makes a bar plot animation.
    Input: bins      - (number of bins, number of frames) shape array
           names     - name of each bin
           save_name - name to save the animation as (must have .mp4 extension)
    """
    start = time.time()

    fig = plt.figure()
    camera = Camera(fig)

    for i in range(bins.shape[1]):
        plt.bar(names, bins[:, i], color='blue', width=0.4)
        camera.snap()

    animation = camera.animate()
    animation.save(save_name, fps=30)
    print("time: ", time.time() - start)


def ratio(a, b):
    """
    Calculates, given the weights of a and b, the "balance point" that can balance them.
    Input: a - a number.
           b - another number.
    Output: how much a should be favored over b as a decimal between 0 and 1
    """
    return b / (a + b)


def circle_mode(bins0, bins1, save_name, color_changing, circle_width=15):
    """
    Makes a circle animation.
    Input: bins0 - left channel
           bins1 - right channel
           save_name - name to save the animation as (must have .mp4 extension)
           color_changing - if True, background changes along with song
    """
    start = time.time()
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_position([0, -0.38888, 1, 1.77777])
    camera = Camera(fig)
    if (bins1 is not None):
        mono = False
    else:
        mono = True

    if (color_changing == True):
        points = find_points(27 / 30, 7)

    color = (1, 1, 1)
    colors = ['magenta', 'yellow', 'cyan', 'red', 'green', 'blue']

    for i in range(bins0.shape[1]):
        if (color_changing == True):
            if (i in points):
                color = (random.random(), random.random(), random.random())
            else:
                color = (color[0] * 0.9, color[1] * 0.9, color[2] * 0.9)
        circles = []
        if (mono == True):
            for j in range(bins0.shape[0]):
                circles.append(
                    plt.Circle((0.5, 0.5), bins0[j, i] / 2, color=colors[j % len(colors)], alpha=0.6, fill=False,
                               linewidth=circle_width))
        else:
            for j in range(bins0.shape[0]):
                circles.append(plt.Circle((ratio(bins0[j, i], bins1[j, i]), 0.5), (bins0[j, i] + bins1[j, i]) / 4,
                                          color=colors[j % len(colors)], alpha=0.6, fill=False, linewidth=circle_width))
        rectangle = plt.Rectangle((-0.5, -0.5), 2, 2, facecolor=color)
        ax.set_xlim((0, 1))
        ax.set_ylim((0, 1))
        plt.axis('off')
        ax.add_artist(rectangle)
        for circle in circles:
            ax.add_artist(circle)
        camera.snap()

    animation = camera.animate()
    animation.save(save_name, fps=30, writer='ffmpeg')
    print("time: ", time.time() - start)
    # processing is done at 10fps so processing time is 3x running time


def add_audio(input_video_filename, added_audio_filename, output_filename):
    """
    Adds original audio to the video.
    Input: input_video_filename - the filename of the input video (generated from circle or bar function above), must be .mp4
           added_audio_filename - the audio of the input video, must be .wav
           output_filename - the filename of the output video, must be .mp4
    """
    input_video = ffmpeg.input(input_video_filename)
    added_audio = ffmpeg.input(added_audio_filename).audio

    (
        ffmpeg
            .concat(input_video, added_audio, v=1, a=1)
            .output(output_filename)
            .run(overwrite_output=True)
    )

if __name__ == '__main__':
    args = sys.argv
    assert len(args) == 6 or len(args) == 7
    assert args[1][-4:] == '.wav'
    assert args[2] in ['0', '1']
    assert args[3][-4:] == '.mp4'
    assert args[4][-4:] == '.mp4'
    assert args[5] in ['0', '1']
    input_audio_filename = args[1]
    mono = int(args[2])
    no_sound_video_output_filename = args[3]
    with_sound_video_output_filename = args[4]
    color_changing = int(args[5])
    if(len(args) == 6):
        circle_width = 15
    else:
        circle_width = int(args[6])
    bins0, bins1 = wav_to_bins(input_audio_filename, mono=mono, bin_boundaries=[4, 37, 93, 371])
    circle_mode(bins0, bins1, no_sound_video_output_filename, color_changing=color_changing, circle_width=circle_width)
    add_audio(no_sound_video_output_filename, input_audio_filename, with_sound_video_output_filename)