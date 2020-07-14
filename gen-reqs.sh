echo 'pipreqs is required to run this file. Install by running: "sudo pip install pipreqs"'
pipreqs --savepath ./requirements.txt --force ./scripts
read -p "Press [Enter] key to continue..."