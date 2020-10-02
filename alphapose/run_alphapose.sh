ffmpeg -i test/test.mp4 -vf fps=25 test/demo-images/out%07d.png

git clone -b pytorch https://github.com/MVIG-SJTU/AlphaPose.git

cd AlphaPose

pip install -r requirements.txt

python3 demo.py --indir /Users/dgrubis/Desktop/DS5500/alphapose/test/demo-images --outdir /Users/dgrubis/Desktop/DS5500/alphapose/test/demo-results
