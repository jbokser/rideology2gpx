from pathlib import Path
from datetime import timedelta
from datetime import datetime
from tabulate import tabulate
from collections import namedtuple
from .gpx_file import GpxFile


class Coordinate(namedtuple('Coordinate', ('latitude', 'longitude'))):

    @staticmethod
    def _dec_to_sexagesimal(d):
        S = lambda x: (abs(x)%1)*60
        g = abs(int(d))
        m = int(S(d))
        s = S(S(d))
        return f"{g:03}°{m:02}′{int(s):02}.{int(s%1*100):02}″"
    
    @property
    def sexagesimal(self):
        
        lat_symbol = 'M' if self.latitude>0 else 'S'
        long_symbol = 'W' if self.longitude>0 else 'E'
        
        lat = self._dec_to_sexagesimal(self.latitude)
        long = self._dec_to_sexagesimal(self.longitude)
        
        return f"{lat_symbol}{lat} {long_symbol}{long}"
    
    def __str__(self):
        return f"{self.sexagesimal}"


class DataFile():

    def __init__(self, filename):
        self._filename = Path(filename)
        self._text = None
        self._table = None
        self._title = None

    @property
    def filename(self):
        return self._filename        

    def __str__(self):
        if self._text is None:
            file = open(self._filename, "r")
            self._text = ""
            with file:
                for line in file.readlines():
                    self._text += line
        return self._text
    
    @property
    def table(self):
        if self._table is None:

            sep = ','

            all_names = ['elapsed_msec', 'gps_latitude', 'gps_longitude',
                        'instant_fuel_consumption', 'water_temperature',
                        'boost_temperature', 'engine_rpm', 'wheel_speed',
                        'x', 'acceleration', 'throttle_position',
                        'boost_pressure', 'gear_position',
                        'brake_pressure_fr_caliper', 'lean_angle',
                        'rideology_score']
            
            formulas = {
                'elapsed_time': lambda d: timedelta(
                    seconds=float(int(d['elapsed_msec']))/1000),
                'gps_latitude': lambda d: float(d['gps_latitude']),
                'gps_longitude': lambda d: float(d['gps_longitude']),
                'water_temperature': lambda d: int(
                    float(d['water_temperature'])),
                'engine_rpm': lambda d: int(float(d['engine_rpm'])),
                'wheel_speed': lambda d: int(float(d['wheel_speed'])),
                'gear_position': lambda d: str(d['gear_position'])
            }

            self._table = []
            i=0
            for line in str(self).split('\n'):
                line_list = [f.strip() for f in line.split(sep)]
                if len(line_list)==len(all_names):
                    full_data = dict(zip(all_names, line_list))
                    i+=1
                    row = {'index': i}
                    for name in formulas.keys():
                        row[name] = formulas[name](full_data)
                    self._table.append(row)

        return self._table
    
    def load(self):
        self.table

    def __bool__(self):
        return bool(self.table)

    @property
    def title(self):
        if self._title is None:
            self._title = list(filter(lambda s: s.startswith('Title,,'),
                                      str(self).split('\n')))[0][7:]
        return self._title
        
    @title.setter
    def title(self, value):
        self._title = value

    @staticmethod
    def _lst_avg(lst): 
        return sum(lst) / len(lst)

    @staticmethod
    def _timedelta_str(td):
        return str(timedelta(seconds=int(td.total_seconds())))
    
    @property
    def start(self):
         return Coordinate(
             self.table[0]['gps_latitude'],
             self.table[0]['gps_longitude']
        )

    @property
    def end(self):
         return Coordinate(
             self.table[-1]['gps_latitude'],
             self.table[-1]['gps_longitude']
        )

    @property
    def max_engine_rpm(self):
        return max([r['engine_rpm'] for r in self.table ])

    @property
    def max_wheel_speed(self):
        return max([r['wheel_speed'] for r in self.table ])

    @property
    def max_water_temperature(self):
        return max([r['water_temperature'] for r in self.table ])

    @property
    def elapsed_time(self):
        times = [r['elapsed_time'] for r in self.table ]
        return max(times) - min(times)

    @property
    def avg_idle_speed(self):
        try:   
            return int(self._lst_avg([r['engine_rpm'] for r in self.table if
                r['engine_rpm'] and r['wheel_speed']==0 and r[
                    'water_temperature']>80 and r['gear_position']=='N']))
        except ZeroDivisionError:
            return None

    @property
    def gears_list(self):
        l = list(set([r['gear_position'] for r in self.table ]))
        l.sort()
        return l

    @property
    def max_engine_rpm_for_each_gear(self):
        out = {}
        for gear in self.gears_list:
            if gear!='N':
                out[gear] = max(
                    [r['engine_rpm'] for r in self.table if r[
                        'gear_position']==gear])
        return(out)

    @property
    def gear_shifts(self):
        out = []
        last_row = None
        for row in self.table:
            if not last_row:
                last_row = row
                continue
            if not row['wheel_speed']:
                continue
            if row['gear_position']!=last_row['gear_position']:
                r = {}
                for k in ['elapsed_time', 'gps_latitude', 'gps_longitude',
                        'engine_rpm', 'wheel_speed', 'gear_position']:
                    r[k] = row[k]
                r['last_gear_position']=last_row['gear_position']
                out.append(r)
            last_row = row
        return out

    @property
    def max_wheel_speed_info(self):
        out = []
        top = self.max_wheel_speed
        last = None
        for row in self.table:
            if row['wheel_speed']==top:
                r = {}
                for k in ['index', 'elapsed_time', 'gps_latitude',
                        'gps_longitude', 'engine_rpm', 'wheel_speed',
                        'gear_position']:
                    r[k] = row[k]
                if not last or last['index']+1!=r['index'] :
                    out.append(r)
                last = r
        return out

    @property
    def max_wheel_speed_for_each_gear(self):
        out = {}
        for gear in self.gears_list:
            if gear!='N':
                out[gear] = max(
                    [r['wheel_speed'] for r in self.table if r[
                        'gear_position']==gear])
        return(out)

    @property
    def avg_speed(self):
        return int(self._lst_avg([r['wheel_speed'] for r in self.table if r[
            'wheel_speed']]))

    @property
    def max_for_each_gear(self):
        out = []
        engine_rpm = self.max_engine_rpm_for_each_gear
        wheel_speed = self.max_wheel_speed_for_each_gear
        for key, value in engine_rpm.items():
            out.append({
                'gear': key,
                'rpm': engine_rpm[key],
                'kmh': wheel_speed[key],
            })
        out.sort(key=lambda d: [d['gear'], d['kmh']])
        return out

    @property
    def distance(self):
        km = 0
        prev_latitude = self.table[0]['gps_latitude']
        prev_longitude = self.table[0]['gps_longitude']
        for r in self.table:
            latitude, longitude = r['gps_latitude'], r['gps_longitude']
            delta_latitude = abs(latitude - prev_latitude)
            delta_longitude = abs(longitude - prev_longitude)
            km += ((delta_latitude**2 + delta_longitude**2)**0.5) * 111.321
            prev_latitude, prev_longitude = latitude, longitude
        return km

    @property
    def report(self):  
        return f"""
{' '.join(self.title.split())}
{' '.join([len(x)*'=' for x in self.title.split()])}
    
Max engine speed: {self.max_engine_rpm} rpm
Max wheel speed:  {self.max_wheel_speed} km/h
Max water temp:   {self.max_water_temperature} ℃
Avg idle speed:   {'Unknown' if self.avg_idle_speed is None else str(self.avg_idle_speed) + ' rpm'}
Avg speed:        {self.avg_speed} km/h
Total time:       {self._timedelta_str(self.elapsed_time)}
Distance:         {self.distance:.2f} km
Starting point:   {self.start}
Ending point:     {self.end}

Max for each gear
--- --- ---- ----

{tabulate(self.max_for_each_gear, headers={'gear':'Gear', 'kmh':'km/h'}, tablefmt='plain')}
"""
    
    def filter_by_distance(self, d):
        if not d:
            return self
        if d<0:
            total = self.distance + d
        km = 0
        prev_latitude = self.table[0]['gps_latitude']
        prev_longitude = self.table[0]['gps_longitude']
        new_table = []
        for r in self.table:
            latitude, longitude = r['gps_latitude'], r['gps_longitude']
            delta_latitude = abs(latitude - prev_latitude)
            delta_longitude = abs(longitude - prev_longitude)
            km += ((delta_latitude**2 + delta_longitude**2)**0.5) * 111.321
            if d<0:
                if km<=total:
                    new_table.append(r)
            else:
                if km>=d:
                    new_table.append(r)
            prev_latitude, prev_longitude = latitude, longitude
        self._table = new_table
        return self


    def filter_by_speed(self, min_=0.0, max_=None):

        if max_ is None:
            max_ = self.max_wheel_speed

        new_table_to_max = []
        for r in self.table:
            new_table_to_max.append(r)
            if r['wheel_speed'] >= max_:
                break
        new_table_to_max.reverse()
        
        new_table = []
        for r in new_table_to_max:
            new_table.append(r)
            if r['wheel_speed'] <= min_:
                break
        new_table.reverse()
        
        self._table = new_table
        
        return self


    def dump(self, basenane=None, show_report=False, silent=True, start_time=None):

        if start_time is None:
            self._start_time = datetime.now()
        else:
            self._start_time = start_time

        if basenane is None:
            basename = self.filename.stem

        self.new_gpxfile(start_time=start_time).dump_to_file(
            self.filename.with_name(basename), silent=silent)
        
        self.new_gpxfile_gear_shifts(start_time=start_time).dump_to_file(
            self.filename.with_name(f"{basename}_gear_shifts"),
            silent=silent)
        
        self.new_gpxfile_speed_shifts(start_time=start_time).dump_to_file(
            self.filename.with_name(f"{basename}_speed_shifts"),
            silent=silent)
        
        report_filename = self.filename.with_name(
            f"{basename}_report").with_suffix('.txt')

        if not silent:
            print(f"Make file {repr(str(report_filename))}...", end="")
        
        report_text = self.report

        with open(report_filename, "w") as file:
            print(report_text, file=file)

        if not silent:
            print(" Ok")

        if show_report:
            print(report_text)


    def new_gpxfile(self, postitle="", start_time = None):

        gpxfile = GpxFile(start_time = start_time)
        gpxfile.name = self.title + postitle
        gpxfile.desc = gpxfile.name

        keys = ['gps_latitude', 'gps_longitude', 'elapsed_time']
        
        for p in self.table:
            args = [p[k] for k in keys]
            gpxfile.add_track_point(*args)
        
        keys = ['gps_latitude', 'gps_longitude']
        
        args = [self.table[0][k] for k in keys] + ['Start']
        gpxfile.add_way_point(*args)
        
        args = [self.table[-1][k] for k in keys] + ['End']
        gpxfile.add_way_point(*args)

        for p in self.max_wheel_speed_info:
            name = f"Max speed {p['wheel_speed']} km/h"
            desc = f"{p['engine_rpm']}rpm @ {p['gear_position']} gear"
            args = [p[k] for k in keys] + [name] + [desc]
            gpxfile.add_way_point(*args)

        return gpxfile


    def new_gpxfile_gear_shifts(self, postitle=" (gear shifts)", start_time = None):

        gpxfile = GpxFile(start_time=start_time)
        gpxfile.name = self.title + postitle
        gpxfile.desc = gpxfile.name

        keys = ['gps_latitude', 'gps_longitude']
        
        for p in self.gear_shifts:
            acction = "Up" if p['last_gear_position'] < p['gear_position'] else "Low"
            name = f"{acction} to {p['gear_position']} gear"
            desc = f"{p['wheel_speed']}km/h @ {p['engine_rpm']}rpm"       
            args = [p[k] for k in keys] + [name] + [desc]
            gpxfile.add_way_point(*args)

        return gpxfile


    def new_gpxfile_speed_shifts(self, chunk=1, postitle=" (speed shifts)", start_time = None):
        gpxfile = GpxFile(start_time=start_time)
        gpxfile.name = self.title + postitle
        gpxfile.desc = gpxfile.name
        km = 0
        prev_latitude = self.table[0]['gps_latitude']
        prev_longitude = self.table[0]['gps_longitude']
        m = None
        for r in self.table:
            if m is None or m['wheel_speed']<r['wheel_speed']:
                m = r
            latitude, longitude = r['gps_latitude'], r['gps_longitude']
            delta_latitude = abs(latitude - prev_latitude)
            delta_longitude = abs(longitude - prev_longitude)
            km += ((delta_latitude**2 + delta_longitude**2)**0.5) * 111.321
            if km>=chunk:
                km=0
                name = f"{m['wheel_speed']} km/h"
                desc = f"{m['engine_rpm']} rpm @ {m['gear_position']} gear"
                args = [m[k] for k in ['gps_latitude', 'gps_longitude']] + [name] + [desc]
                gpxfile.add_way_point(*args)
                m = None
            prev_latitude, prev_longitude = latitude, longitude
        return gpxfile
