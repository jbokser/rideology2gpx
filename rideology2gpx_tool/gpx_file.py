from bs4 import BeautifulSoup as BS
from warnings import filterwarnings
from pathlib import Path
from datetime import timedelta
from datetime import datetime


# Filter BeautifulSoup warnings
filterwarnings("ignore", category=UserWarning)


class GpxFile():

    def __init__(self, start_time = None):

        content = """
            <gpx xmlns="http://www.topografix.com/GPX/1/1"
                 creator="rideology2gpx"
                 version="1.1"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"> 
                <metadata>
                </metadata>
                <trk>
                    <trkseg>
                    </trkseg>
                </trk>
            </gpx>
        """

        self.soup = BS(content, features="xml")
        self._name = None
        self._desc = None
        if start_time is None:
            self._start_time = datetime.now()
        else:
            self._start_time = start_time


    def _set_tag_and_value(self, value, tag_name, base_tag_name, index=0):
        base_tag = self.soup.find(base_tag_name)
        tag = base_tag.find(tag_name)
        if not tag:
            tag = self.soup.new_tag(tag_name)
            base_tag.insert(index, tag)
        tag.string = value

    def set_name(self, value):
        self._set_tag_and_value(value, 'name', 'metadata', 0)
        self._set_tag_and_value(value, 'name', 'trk', 0)
        self._name = value

    def set_desc(self, value):
        self._set_tag_and_value(value, 'desc', 'metadata', 1)
        self._set_tag_and_value(value, 'desc', 'trk', 1)
        self._desc = value

    def get_name(self):
        return self._name

    def get_desc(self):
        return self._desc

    @property
    def name(self):
        return self.get_name()

    @property
    def desc(self):
        return self.get_desc()

    @name.setter
    def name(self, value):
        self.set_name(value)

    @desc.setter
    def desc(self, value):
        self.set_desc(value)
    
    def add_track_point(self, lat, lon, time_=None, ele=None):

        trkseg_tag = self.soup.find('trkseg')
        trkpt_tag = self.soup.new_tag('trkpt', attrs={'lat': lat, 'lon': lon})
        trkseg_tag.append(trkpt_tag)

        if time_ is not None:

            if isinstance(time_, (int, float)):
                time_ = timedelta(seconds=time_)

            if isinstance(time_, timedelta):
                time_ = self._start_time + time_

            if isinstance(time_, datetime):
                time_ = time_.isoformat() + 'Z'

            time_tag = self.soup.new_tag('time')
            time_tag.string = str(time_)
            trkpt_tag.append(time_tag)

        if ele is not None:

            ele_tag = self.soup.new_tag('ele')
            ele_tag.string = str(ele)
            trkpt_tag.append(ele_tag)

    def add_way_point(self, lat, lon, name, desc=None):
        gpx_tag = self.soup.find('gpx')
        wpt_tag = self.soup.new_tag('wpt', attrs={'lat': lat, 'lon': lon})
        gpx_tag.append(wpt_tag)
        name_tag = self.soup.new_tag('name')
        name_tag.string = str(name)
        wpt_tag.append(name_tag)
        if desc:
            desc_tag = self.soup.new_tag('desc')
            desc_tag.string = str(desc)
            wpt_tag.append(desc_tag)


    def __str__(self):

        out = self.soup.prettify() #FIXME

        # I need to find a better prettify()
        new_lines = []
        lines = out.split('\n')
        fnc_is_tag = lambda s: s.strip().startswith('<')
        max_i = len(lines) - 1
        for i, l in enumerate(lines):
            
            prev_is_tag = fnc_is_tag(lines[i-1]) if i>0 else True
            next_is_tag = fnc_is_tag(lines[i+1]) if i<max_i else True
            is_tag = fnc_is_tag(l)

            if not is_tag and (next_is_tag or prev_is_tag):
                new_lines.append(l.strip())
            elif is_tag and not prev_is_tag:
                new_lines.append(l.strip())
                new_lines.append('\n')
            elif is_tag and not next_is_tag:
                new_lines.append(l)
            else:
                new_lines.append(l)
                new_lines.append('\n')

        return ''.join(new_lines)


    def dump_to_file(self, filename, suffix='.gpx', silent=True):

        path = Path(filename)

        if suffix:
            path = path.with_suffix(suffix)

        # Use path.exists() for future checks 

        if not silent:
            print(f"Make file {repr(str(path))}...", end="")

        with open(path, "w") as file:
            print(self, file=file)
        
        if not silent:
            print(" Ok")
