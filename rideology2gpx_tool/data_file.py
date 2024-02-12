import plotly.express as px
from plotly.graph_objects import Figure, Table
from pathlib import Path
from datetime import timedelta
from datetime import datetime
from tabulate import tabulate
from collections import namedtuple
from pandas import DataFrame, Series, to_numeric
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
                        'acceleration', 'throttle_position',
                        'accel_grip_position', 'boost_pressure',
                        'gear_position', 'brake_pressure_fr_caliper',
                        'lean_angle', 'rideology_score']
            
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
                if len(line_list)==len(all_names) and \
                        line_list[0].replace('"', '')!=all_names[0]:
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

    def __len__(self):
        return len(self.table)

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
        try:
            return int(self._lst_avg([r['wheel_speed'] for r in self.table if r['wheel_speed']]))
        except ZeroDivisionError:
            return None

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

    def _table_report(self, tablefmt='github'):

        table = []

        F = lambda x: x
        if tablefmt=='plain':
            F = lambda x: f"{x}:"

        table.append([F('Max engine speed'), f"{self.max_engine_rpm} rpm"])
        table.append([F('Max wheel speed'), f"{self.max_wheel_speed} km/h"])
        table.append([F('Max water temp'), f"{self.max_water_temperature} ℃"])

        if self.avg_idle_speed:
            table.append([F('Avg idle speed'), f"{self.avg_idle_speed} rpm"])

        if self.avg_speed:
            table.append([F('Avg speed'), f"{self.avg_speed} km/h"])
        
        table.append([F('Total time'), f"{self._timedelta_str(self.elapsed_time)}"])
        table.append([F('Distance'), f"{self.distance:.2f} km"])
        table.append([F('Starting point'), str(self.start)])
        table.append([F('Ending point'), str(self.end)])

        return table

    def _table_report_str(self, tablefmt='plain'):

        table = self._table_report(tablefmt=tablefmt)
       
        kargs = {'tablefmt': tablefmt}
        if tablefmt=='github':
            kargs['headers'] = ['Item', 'Value']

        return tabulate(table, **kargs)

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
    
{self._table_report_str()}

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

    def data_frame(self, start_time=None):

        if start_time is None:
            start_time = datetime.now()

        columns = ['Time', 'Latitude', 'Longitude', 'Water temperature',
                   'Engine RPM', 'Wheel speed', 'Gear position']
        keys = {
            'Time': 'elapsed_time',
            'Latitude': 'gps_latitude',
            'Longitude': 'gps_longitude',
            'Water temperature': 'water_temperature',
            'Engine RPM': 'engine_rpm',
            'Wheel speed': 'wheel_speed',
            'Gear position': 'gear_position'
        }

        transform = {
            'elapsed_time': lambda x: x + start_time,
            'gear_position': lambda x: (0 if x=='N' else int(x)),
            'default': lambda x: x
        }

        df = DataFrame(columns=columns)
        
        for i, r in enumerate(self.table):
            row = {}
            for c in columns:
                k = keys[c]
                fnc = transform.get(k, transform.get('default', lambda x: x))
                row[c] = fnc(r[k])
            df.loc[i+1] = Series(row)

        for field in ['Latitude', 'Longitude', 'Water temperature',
                      'Engine RPM', 'Wheel speed', 'Gear position']:
            df[field] = to_numeric(df[field])

        return df

    def dump_md(self, basename=None, start_time=None, silent=True,
                output_dir=None):

        if basename is None:
            basename = self.filename.stem
        else:
            basename = Path(basename).stem

        if output_dir is None:
            filename = self.filename.with_name(basename)
        else:
            filename = (output_dir / Path(basename)) 

        for field, unit in [
                ("Wheel speed", "km/h"),
                ("Engine RPM", "rpm"),
                ("Gear position", "Gear")
            ]:

            posname = "_".join([''] + field.strip().split()).lower()
            title = f"{field}, {' '.join(self.title.split())}"
            
            df = self.data_frame(start_time=start_time)
            
            fig = px.area(df, x='Time', y=field)
            
            base_kargs = dict(showgrid=True, gridwidth=1,
                              gridcolor='LightPink',
                minor=dict(ticklen=6 if field!="Gear position" else 0,
                           tickcolor="black", showgrid=True))
            
            fig.update_xaxes(title=None, tickformat="%H:%M:%S",
                             tickangle=30, **base_kargs)
            
            fig.update_yaxes(title=unit, **base_kargs)

            if field=="Gear position":
                fig.update_yaxes(tickvals=[0,1,2,3,4,5,6], ticktext=[
                    ' N   ', 
                    '1st  ',
                    '2nd  ',
                    '3rd  ',
                    '4th  ',
                    '5th  ',
                    '6th  '])

            if field in ["Wheel speed", "Engine RPM"]:
                
                max_y = df.loc[df[field].idxmax()][field]
                max_x = df.loc[df[field].idxmax()]['Time']

                fig.add_annotation(
                    text=f"Max {max_y} {unit}", x=max_x, y=max_y*1.01,
                    arrowhead=1, showarrow=True
                )

            fig.update_layout(title=title)

            image_filename = filename.with_name(
                f"{basename}{posname}").with_suffix('.jpeg')

            if not silent:
                print(f"Make file {repr(str(image_filename))}...", end="")
            
            fig.write_image(image_filename, width=800, height=350)

            if not silent:
                print(" Ok")

        def get_values(table):
            values = []
            if table:
                for i in range(len(table[0])):
                    values.append([x[i] for x in table])
            return values

        table = self._table_report()
        values = get_values(table)

        fig = Figure(
            data=[Table(
                columnorder = [1, 2],
                columnwidth = [45, 55],
                cells = dict(values=values, align = 'left',
                             line_color='darkslategray'),
                header = dict(values=['Item', 'Value'], align = 'center',
                              line_color='darkslategray')
            )])
        
        title = f"Info, {' '.join(self.title.split())}"

        fig.update_layout(title=title)

        image_filename = filename.with_name(
            f"{basename}_table").with_suffix('.jpeg')

        if not silent:
            print(f"Make file {repr(str(image_filename))}...", end="")
        
        fig.write_image(image_filename, width=500, height=450)

        if not silent:
            print(" Ok")

        table = [[r[k] for k in ['gear', 'rpm', 'kmh']
                  ] for r in self.max_for_each_gear]
        values = get_values(table)

        fig = Figure(
            data=[Table(
                cells = dict(values=values, align = 'right',
                             line_color='darkslategray'),
                header = dict(values=['Gear', 'rpm', 'km/h'],
                              align = 'center',
                              line_color='darkslategray')
            )])
        
        title = f"Max for each gear, {' '.join(self.title.split())}"

        fig.update_layout(title=title)

        image_filename = filename.with_name(
            f"{basename}_max_for_each_gear").with_suffix('.jpeg')

        if not silent:
            print(f"Make file {repr(str(image_filename))}...", end="")
        
        fig.write_image(image_filename, width=550, height=350)

        if not silent:
            print(" Ok")

        max_for_each_gear_str = tabulate(
            self.max_for_each_gear,
            headers={'gear':'Gear', 'kmh':'km/h'},
            tablefmt='github',
        ).replace('---|', '-: |'
        ).replace('|---', '| --'
        ).replace('|\n| --', '|\n| :-')

        md = f"""# {' '.join(self.title.split())}

{self._table_report_str(tablefmt="github")}

## Max for each gear

{max_for_each_gear_str}

## Graphics

 ![Wheel speed graph]({basename}_wheel_speed.jpeg)
 ![Engine rpm graph]({basename}_engine_rpm.jpeg)
 ![Gear position graph]({basename}_gear_position.jpeg)

"""
        report_filename = filename.with_name(
            f"{basename}_report").with_suffix('.md')

        if not silent:
            print(f"Make file {repr(str(report_filename))}...", end="")

        with open(report_filename, "w") as file:
            print(md, file=file)

        if not silent:
            print(" Ok")

    def dump(self, basename=None, show_report=False, silent=True,
             start_time=None, output_dir=None):

        if basename is None:
            basename = self.filename.stem
        else:
            basename = Path(basename).stem

        if output_dir is None:
            filename = self.filename.with_name(basename)
        else:
            filename = (output_dir / Path(basename)) 

        self.new_gpxfile(start_time=start_time).dump_to_file(
            filename.with_name(basename), silent=silent)
        
        self.new_gpxfile_gear_shifts(start_time=start_time).dump_to_file(
            filename.with_name(f"{basename}_gear_shifts"),
            silent=silent)
        
        self.new_gpxfile_speed_shifts(start_time=start_time).dump_to_file(
            filename.with_name(f"{basename}_speed_shifts"),
            silent=silent)
        
        report_filename = filename.with_name(
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

    def new_gpxfile(self, postitle="", start_time=None):

        gpxfile = GpxFile(start_time=start_time)
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


    def new_gpxfile_speed_shifts(self, chunk=1, postitle=" (speed shifts)", start_time=None):
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
