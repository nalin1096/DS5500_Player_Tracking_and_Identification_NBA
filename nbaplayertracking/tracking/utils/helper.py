import subprocess
import os


def create_frames(video_file, out_folder):
    process = subprocess.run(['ffmpeg', '-i', video_file, '-vf', 'fps=25', os.path.join(out_folder, 'out%07d.png')])
    return
