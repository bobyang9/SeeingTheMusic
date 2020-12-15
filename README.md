# SeeingTheMusic

SeeingTheMusic is a audio visualization tool for EDM (electronic dance music). 

## Requirements:

```
python 3.7.5
ffmpeg 4.2.2
matplotlib 3.2.1
numpy 1.16.4
scipy 1.5.2
celluloid 0.2.0
```

## Usage:

1. Download audio_visualization.py to the same directory that contains your sound files.
2. Navigate in the command line to that directory.
3. Run the script with the following format: ```audio_visualization.py arg1 arg2 arg3 arg4 arg5 arg6```, where:
  * arg1 is the filename of the audio you are inputting, must be **.wav** format
  * arg2 is either 0 or 1, 0 if you only want one channel to be analyzed, 1 if you want two channels to be analyzed
  * arg3 is the filename of the **soundless** video to be outputted, must have **.mp4** extension
  * arg4 is the filename of the video **including sound** to be outputted, must have **.mp4** extension
  * arg5 is either 0 or 1, 1 if you want a color-changing background, 0 if not
  * arg6 is an integer denoting the width of the circles; this is **optional** and defaults to 15 if not stated
4. Processing is usually fast (~30fps) but on some settings may go as low as 10fps (mostly due to plotting and writing the animation to disk), so running time may approach three times the video duration.
5. You will find the generated videos in the same directory that contains the script and your sound files.

