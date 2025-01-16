**Instructions on setting up environment:**

1. download python 3.9.6
2. clone this github repo into a folder of your choice
3. open a terminal and cd to the root directory of this repo
4. `python3 -m venv .` (_steps 4,5_ set up virtual env - I recommend doing them to avoid polluting your global python env, but not necessary)
5. `source venv/bin/activate` (`venv\Scripts\activate.bat` for windows)
   - refer to https://docs.python.org/3/library/venv.html for more details
   - step 5 needs to be run at the start of every new terminal/shell you create after navigating to root dir of your project
6. `pip install -r requirements.txt`

**Instructions on running code:**

1. `python index.py`

**Files explained:**

- index.py
  - all the code is there currently. I will move it soon into OOP format.
- app.py
  - RESTful API that connects the generated clips and clip_details.json within `output_clips/` to the frontend webpage
- imdb.py
  - Fetches movie data from OMDB and TMDB apis such as name of actors in it and their profile picture
- augment_videos.py
  - Not necessary at the moment. Does data augmentation on existing clips (flipping the image, rotating, adding noise, changing brightness).



  For Zain's extract.py
  run in this order

  start you python env 

  python extract.py

  clips are exported to outputClips
  test videos hardcoded in, present in directory
