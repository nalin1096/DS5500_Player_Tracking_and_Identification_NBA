import os
import ffmpeg

def preprocess_video(video_file, out_folder):
    (
        ffmpeg
        .input(video_file)
        .filter('fps', fps=25)
        .output(os.path.join(out_folder, 'out%07d.png'), format='image2', vcodec='mjpeg')
        .run()
    )
    
    return