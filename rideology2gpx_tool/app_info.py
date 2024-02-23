version='1.1b3'
author='Juan S. Bokser'
author_email='juan.bokser@gmail.com'
description='A simple command line program to transform log files obtained with the Kawasaki Rideology App into GPX files.'
app_name='rideolgy2gpx'
author_user='jbokser'
repo_url=f"https://github.com/{author_user}/{app_name}"

#######################################

app_info = {} # as dict  
for key, value in dict(locals()).items():
    if key[0]!="_" and key not in ['app_info'] :
        app_info[key] = value
