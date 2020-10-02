cd PoseFlow

pip install -r requirements.txt

python tracker-general.py --imgdir  /Users/dgrubis/Desktop/DS5500/alphapose/test/demo-images
                          --in_json /Users/dgrubis/Desktop/DS5500/alphapose/test/demo-results/alphapose-results.json
                          --out_json /Users/dgrubis/Desktop/DS5500/alphapose/test/demo-results/alphapose-results-forvis-tracked.json
                          --visdir /Users/dgrubis/Desktop/DS5500/alphapose/test/demo-render
cd /Users/dgrubis/Desktop/DS5500/alphapose/test/demo-render

ffmpeg -i out%07d.png.png -c:v libx264 -vf fps=25 out.mp4
