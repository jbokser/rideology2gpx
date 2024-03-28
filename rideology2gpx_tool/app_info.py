version: str = '1.1'
author: str = 'Juan S. Bokser'
author_email: str = 'juan.bokser@gmail.com'
description: str = 'A simple command line program to transform log files obtained with the Kawasaki Rideology App into GPX files.'
app_name: str = 'rideology2gpx'
author_user: str = 'jbokser'
repo_url: str = f"https://github.com/{author_user}/{app_name}"

#######################################

app_info: dict = {}  
for key, value in dict(locals()).items():
    if key[0]!="_" and key not in ['app_info'] :
        app_info[key] = value
