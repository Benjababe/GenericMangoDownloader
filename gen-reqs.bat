@echo off
echo pipreqs is required to run this file. Install by running: "pip install pipreqs"
pipreqs --savepath ./requirements.txt --force ./scripts
pause