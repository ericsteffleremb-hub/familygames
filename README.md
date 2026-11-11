"# familygames" 

--------Initial startup--------
You will be restricted from running the run.bat file if you've downloaded it because
bat files are potentially malicious files. To get around this you will have to create
your own .bat file and copy over the contents.

after running it the first time if you don't have python 3.12 installed it will prompt you
to install python 3.12 then quit when it is done to reset the terminal.

You will then have to run it again and it will create a venv to install pygame into. The
venv will have to be in python 3.12 and "py -3.12 -m venv .venv" should guarantee that.
pygame 2.6.1 is the version this is currently working with
ngrok 1.7.0 is being used to run the serverSide.py file 
the run.bat file can just be double clicked in browser after this to run the FamilyGame.py application

--------Running the application--------
the serverSide can be run locally if start_ngrok() is commented out in main
or it can be run with a TCP tunnel if start_ngrok() is not commented out. This
requires setting up an account with ngrok and getting an authentication key. 

the FamilyGame.py side will have to be updated with the server IP & port to connect
to the server. Then the run.bat can be doubled clicked to run it, or called in command line. 