import plotly.express as px
from math import radians, degrees, sin, cos, atan2
from plotly.graph_objects import Figure, Table
from pathlib import Path
from datetime import timedelta
from datetime import datetime
from tabulate import tabulate
from collections import namedtuple
from pandas import DataFrame, Series, to_numeric
from .gpx_file import GpxFile


G = 9.81

def td_to_str(td: timedelta) -> str:
    h, r = divmod(td.seconds, 3600)
    m, s = divmod(r, 60)
    l = []
    if h:
        l.append(f"{h}h")
    if m or l:
        l.append(f"{m}m")
    if s or not(l):  
        l.append(f"{s}s")       
    str = ' '.join(l)
    return str

def dec_to_sexagesimal(d) -> str:
    S = lambda x: (abs(x)%1)*60
    g = abs(int(d))
    m = int(S(d))
    s = S(S(d))
    return f"{g:03}°{m:02}′{int(s):02}.{int(s%1*100):02}″"


class Course():

    _cardinals_list = ["N", "NW", "W", "SW", "S", "SE", "E", "NE", "N"]

    @property
    def value(self) -> float:
        return self._value
    
    @value.setter
    def value(self, value: float):
        value = (float(value) + 360) % 360
        self._value = value

    def __init__(self, value: float):
        self.value = value

    @property
    def cardinal(self) -> float:
        m = (len(self._cardinals_list)-1)
        return self._cardinals_list[round(self.value / (360/m)) % m]

    def __str__(self) -> str:
        return f"{self.cardinal} {int(self.value)}°"  

    def __format__(self, format_spec) -> str:
        if not format_spec:
            return str(self)
        return f"{self.value:{format_spec}}"


class Coordinate(namedtuple('Coordinate', ('latitude', 'longitude'))):
   
    @property
    def sexagesimal(self):
        
        lat_symbol = 'N' if self.latitude>0 else 'S'
        long_symbol = 'W' if self.longitude>0 else 'E'
        
        lat = dec_to_sexagesimal(self.latitude)
        long = dec_to_sexagesimal(self.longitude)
        
        return f"{lat_symbol}{lat} {long_symbol}{long}"
    
    def __str__(self):
        return f"{self.sexagesimal}"

    def km_to(self, coor) -> float:
        if not isinstance(coor, Coordinate):
            raise TypeError("coor must be a Coordinate instance")
        if coor == self:
            return 0.0        
        delta_latitude = abs(coor.latitude - self.latitude)
        delta_longitude = abs(coor.longitude - self.longitude)
        km = ((delta_latitude**2 + delta_longitude**2)**0.5) * 111.321
        return km

    def course(self, coor) -> float:
        if not isinstance(coor, Coordinate):
            raise TypeError("coor must be a Coordinate instance")

        if coor == self:
            return None

        lat1, lon1, lat2, lon2 = map(radians, [
            self.latitude, -self.longitude, coor.latitude, -coor.longitude])
    
        delta_lon = lon2 - lon1
        
        x = sin(delta_lon) * cos(lat2)
        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_lon)
        
        course = degrees(atan2(x, y))
    
        return Course(course)


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
            def file_to_text():
                for encoding in ['utf-8', 'windows-1252']:
                    file = open(self._filename, "r", encoding=encoding)
                    out = ""
                    error = None
                    try:
                        with file:
                            for line in file.readlines():
                                out += line
                    except UnicodeDecodeError as e:
                        error = e
                    if error is None:
                        break
                if error:
                    raise error
                return out
            self._text = file_to_text()
        return self._text
    
    @property
    def table(self):
        if self._table is None:

            sep = ','

            base_names = ['elapsed_msec', 'gps_latitude', 'gps_longitude',
                        'instant_fuel_consumption', 'water_temperature',
                        'engine_rpm', 'wheel_speed',
                        'acceleration', 'throttle_position']    

            formulas = {
                'elapsed_time': lambda d, r, l: timedelta(seconds=float(int(d[
                    'elapsed_msec']))/1000),
                'gps_latitude': lambda d, r, l: float(d['gps_latitude']),
                'gps_longitude': lambda d, r, l: float(d['gps_longitude']),
                'water_temperature': lambda d, r, l: int(float(d[
                    'water_temperature'])),
                'engine_rpm': lambda d, r, l: int(float(d['engine_rpm'])),
                'wheel_speed': lambda d, r, l: int(float(d['wheel_speed'])),
                'gear_position': lambda d, r, l: str(d['gear_position']),
                'coordinate': lambda d, r, l: Coordinate(r['gps_latitude'], r[
                    'gps_longitude']),
                'last_coordinate': lambda d, r, l: l['coordinate'],
                'delta_distance': lambda d, r, l: r['last_coordinate'].km_to(
                    r['coordinate'])*1000.0,
                'delta_time': lambda d, r, l: r['elapsed_time'] - l[
                    'elapsed_time'],
                'course': lambda d, r, l: r['last_coordinate'].course(r[
                    'coordinate']),
                'gps_speed': lambda d, r, l: 3.6 * r['delta_distance'] / r[
                    'delta_time'].total_seconds() if r['delta_time'
                        ].total_seconds() else 0.0,
                'distance': lambda d, r, l: l.get('distance', 0.0) + (
                    r['delta_distance']/1000),
                'wheel_acceleration': lambda d, r, l: (((r.get('wheel_speed',
                    0.0) - l.get('wheel_speed', 0.0))/3.6)/r['delta_time'
                    ].total_seconds() if r['delta_time'].total_seconds(
                    ) else 0.0)/G,
                'gps_acceleration': lambda d, r, l: (((r.get('gps_speed',
                    0.0) - l.get('gps_speed', 0.0))/3.6)/r['delta_time'
                    ].total_seconds() if r['delta_time'].total_seconds(
                    ) else 0.0)/G,
            }

            self._table = []
            i=0
            last_row = None
            all_names = []
            for line in str(self).split('\n'):
                line_list = [x.strip().replace('"', ''
                    ).split('(')[0].lower() for x in line.split(sep)]
                
                if not(bool(set(base_names)-set(line_list))):
                    all_names = [x for x in line_list]
                    continue
                
                if not all_names:
                    continue

                if len(line_list)==len(all_names):
                    full_data = dict(zip(all_names, line_list))
                    i+=1
                    row = {'index': i}
                    for name in formulas.keys():
                        row[name] = formulas[name](
                            full_data,row,
                            row if last_row is None else last_row)
                    self._table.append(row)
                    last_row = row

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
            self._title = ''.join(c for c in self._title if ord(c) < 128).strip()
        return self._title
        
    @title.setter
    def title(self, value):
        self._title = value

    @staticmethod
    def _lst_avg(numbers: list) -> float: 
        return sum(numbers) / len(numbers)

    @staticmethod
    def _lst_median(numbers: list) -> float:
        """Returns the median of a list of numbers."""
        numbers.sort()
        length = len(numbers)
        middle = length // 2
        
        if length % 2 == 0:
            return (numbers[middle - 1] + numbers[middle]) / 2
        else:
            return numbers[middle]

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
    def max_wheel_acceleration(self):
        return max([r['wheel_acceleration'] for r in self.table ])

    @property
    def max_wheel_brake(self):
        return min([r['wheel_acceleration'] for r in self.table ])

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
    def mediam_speed(self):
        return int(self._lst_median([r['wheel_speed'] for r in self.table if r['wheel_speed']]))

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

        for caption, data, unit, field in [
                ('Max engine speed', self.max_engine_rpm, 'rpm',
                 'engine_rpm'),
                ('Max wheel speed', self.max_wheel_speed, 'km/h',
                 'wheel_speed'),
                ('Max acceleration', self.max_wheel_acceleration, 'g',
                 'wheel_acceleration'),
                ('Max brake', self.max_wheel_brake, 'g',
                 'wheel_acceleration'),
                ('Max water temp', self.max_water_temperature, '°C',
                 'water_temperature')
            ]:
            td_str = ''.join(td_to_str(self._time_above(field, data)).split())
            dd = self._distance_above(field, data)
            dd_unit = 'Km'
            if dd<1:
                dd *= 1000
                dd_unit = 'm'
            str_data = f"{abs(data)}" if type(data) is int else f"{abs(data):.2f}"
            table.append([F(caption), f"{str_data} {unit} (for {td_str} or {int(dd)}{dd_unit})"])

        if self.avg_idle_speed:
            table.append([F('Avg idle speed'), f"{self.avg_idle_speed} rpm"])

        if self.avg_speed:
            table.append([F('Avg speed'), f"{self.avg_speed} km/h"])

        if self.mediam_speed:
            table.append([F('Mediam speed'), f"{self.mediam_speed} km/h"])

        table.append([F('Total time'), f"{self._timedelta_str(self.elapsed_time)}"])
        table.append([F('Distance'), f"{self.distance:.2f} km ({self.start.km_to(self.end):.2f} km straight)"])       
        table.append([F('Course'), f"{self.start.course(self.end)}"])
        table.append([F('Starting point'), str(self.start)])
        table.append([F('Ending point'), str(self.end)])

        return table

    def _table_report_str(self, tablefmt='plain'):

        table = self._table_report(tablefmt=tablefmt)
       
        kargs = {'tablefmt': tablefmt}
        if tablefmt=='github':
            kargs['headers'] = ['Item', 'Value']

        return tabulate(table, **kargs)

    def _time_above(self, field='wheel_speed', threshold=60):
        last_elapsed_time = self.table[0]['elapsed_time']
        time = timedelta(seconds=0) 
        for l in self.table[1:]:
            delta = l['elapsed_time'] - last_elapsed_time
            value = l[field]
            if isinstance(value, str):
                try:
                    value = int(value)
                except ValueError:
                    value = 0
            last_elapsed_time = l['elapsed_time'] 
            if threshold>=0:
                if value>=threshold:
                    time += delta
            else:
                if value<=threshold:
                    time += delta
        return time
    
    def _time_dist(self, field='wheel_speed', step=20):

        threshold=0
        data = []
        while True:
            time = self._time_above(field, threshold)
            if time:
                data.append((threshold, time))
                threshold += step
            else:
                break
        data.reverse()
        out = []
        for i, (threshold, t) in enumerate(data):
            time = (t - data[i-1][1]) if i else t
            out.append(((threshold, threshold+step), time))
        out.reverse()
        return out

    def _distance_above(self, field='wheel_speed', threshold=60):
        km = 0
        prev_coor = Coordinate(
            self.table[0]['gps_latitude'],
            self.table[0]['gps_longitude'])        
        for l in self.table[1:]:
            coor = Coordinate(l['gps_latitude'], l['gps_longitude'])
            delta = prev_coor.km_to(coor)
            value = l[field]
            if isinstance(value, str):
                try:
                    value = int(value)
                except ValueError:
                    value = 0
            prev_coor = coor
            if threshold>=0:
                if value>=threshold:
                    km += delta
            else:
                if value<=threshold:
                    km += delta
        return km
    
    def _distance_dist(self, field='wheel_speed', step=20):

        threshold=0
        data = []
        while True:
            distance = self._distance_above(field, threshold)
            if distance:
                data.append((threshold, distance))
                threshold += step
            else:
                break
        data.reverse()
        out = []
        for i, (threshold, d) in enumerate(data):
            distance = (d - data[i-1][1]) if i else d
            out.append(((threshold, threshold+step), distance))
        out.reverse()
        return out

    @property
    def distance(self):
        km = 0
        prev_coor = Coordinate(
            self.table[0]['gps_latitude'],
            self.table[0]['gps_longitude'])
        for r in self.table:
            coor = Coordinate(r['gps_latitude'], r['gps_longitude'])
            km += prev_coor.km_to(coor)
            prev_coor = coor
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
        prev_coor = Coordinate(
            self.table[0]['gps_latitude'],
            self.table[0]['gps_longitude'])
        new_table = []
        for r in self.table:
            coor = Coordinate(r['gps_latitude'], r['gps_longitude'])
            km += prev_coor.km_to(coor)
            if d<0:
                if km<=total:
                    new_table.append(r)
            else:
                if km>=d:
                    new_table.append(r)
            prev_coor = coor
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
                   'Engine RPM', 'Wheel speed', 'Gear position', 'Distance',
                   'Acceleration', 'Course']
        keys = {
            'Time': 'elapsed_time',
            'Latitude': 'gps_latitude',
            'Longitude': 'gps_longitude',
            'Water temperature': 'water_temperature',
            'Engine RPM': 'engine_rpm',
            'Wheel speed': 'wheel_speed',
            'Gear position': 'gear_position',
            'Distance': 'distance',
            'Acceleration': 'wheel_acceleration',
            'Course': 'course',        
        }

        transform = {
            'elapsed_time': lambda x: x + start_time,
            'gear_position': lambda x: (0 if x=='N' else int(x)),
            'course': lambda x: x.value if x is not None else None,
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
                      'Engine RPM', 'Wheel speed', 'Gear position',
                      'Distance', 'Acceleration', 'Course']:
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
                ("Gear position", "Gear"),
                ("Acceleration", "g"),              
                ("Course", ""),              
            ]:

            posname = "_".join([''] + field.strip().split()).lower()
            title = f"{field} vs. time, {' '.join(self.title.split())}"
            title_d = f"{field} vs. distance, {' '.join(self.title.split())}"
            
            df = self.data_frame(start_time=start_time)
            
            if field in ['Course', 'Acceleration']:
                df = df.dropna(subset=[field]) # remove NaN
                df = df[df[field] != 0] 
            
            p = px.line if field in ['Course', 'Acceleration'] else px.area
            fig = p(df, x='Time', y=field)
            fig_d = p(df, x='Distance', y=field)
            
            base_kargs = dict(showgrid=True, gridwidth=1,
                              gridcolor='LightPink',
                minor=dict(ticklen=0 if field in ["Gear position",
                                                  "Course"] else 6,
                           tickcolor="black", showgrid=True))
            
            fig.update_xaxes(title=None, tickformat="%H:%M:%S",
                             tickangle=30, **base_kargs)

            fig_d.update_xaxes(title='Km', **base_kargs)
            
            fig.update_yaxes(title=unit, **base_kargs)

            fig_d.update_yaxes(title=unit, **base_kargs)

            if field=="Gear position":
                fig.update_yaxes(tickvals=[0,1,2,3,4,5,6], ticktext=[
                    ' N   ', 
                    '1st  ',
                    '2nd  ',
                    '3rd  ',
                    '4th  ',
                    '5th  ',
                    '6th  '])
                fig_d.update_yaxes(tickvals=[0,1,2,3,4,5,6], ticktext=[
                    ' N   ', 
                    '1st  ',
                    '2nd  ',
                    '3rd  ',
                    '4th  ',
                    '5th  ',
                    '6th  '])

            if field=="Course":
                fig.update_yaxes(tickvals=[x for x in range(0, 361, 45)],
                                 ticktext=[str(Course(x)) for x in range(
                                     0, 361, 45)])
                fig_d.update_yaxes(tickvals=[x for x in range(0, 361, 45)],
                                   ticktext=[str(Course(x)) for x in range(
                                       0, 361, 45)])

            if field in ["Wheel speed", "Engine RPM", "Acceleration"]:
                
                max_y = df.loc[df[field].idxmax()][field]
                max_x = df.loc[df[field].idxmax()]['Time']
                max_x_d = df.loc[df[field].idxmax()]['Distance']

                str_max_y = (f"Max {max_y:.02f} {unit}"
                             if isinstance(max_y, float) else
                             f"Max {max_y} {unit}")

                fig.add_annotation(
                    text=str_max_y, x=max_x, y=max_y*1.01,
                    arrowhead=1, showarrow=True
                )

                fig_d.add_annotation(
                    text=str_max_y, x=max_x_d, y=max_y*1.01,
                    arrowhead=1, showarrow=True
                )

            if field in ["Acceleration"]:
                
                min_y = df.loc[df[field].idxmin()][field]
                min_x = df.loc[df[field].idxmin()]['Time']
                min_x_d = df.loc[df[field].idxmin()]['Distance']

                str_min_y = (f"Min {min_y:.02f} {unit}"
                             if isinstance(min_y, float) else
                             f"Min {min_y} {unit}")

                fig.add_annotation(
                    text=str_min_y, x=min_x, y=min_y*1.01,
                    arrowhead=1, showarrow=True
                )

                fig_d.add_annotation(
                    text=str_min_y, x=min_x_d, y=min_y*1.01,
                    arrowhead=1, showarrow=True
                )

            fig.update_layout(title=title)
            fig_d.update_layout(title=title_d)

            image_filename = filename.with_name(
                f"{basename}{posname}_vs_time").with_suffix('.jpg')

            image_filename_d = filename.with_name(
                f"{basename}{posname}_vs_distance").with_suffix('.jpg')

            if not silent:
                print(f"Make file {repr(str(image_filename))}...", end="")
            
            fig.write_image(image_filename, width=800, height=350)

            if not silent:
                print(" Ok")
                print(f"Make file {repr(str(image_filename_d))}...", end="")
            
            fig_d.write_image(image_filename_d, width=800, height=350)

            if not silent:
                print(" Ok")

        #
        # For time distribution graph uncommnet this code
        #
        # for field in ['gear_position', 'engine_rpm', 'wheel_speed']:
        #
        #     title = {
        #         'wheel_speed': 'Time distribution of wheel speed',
        #         'engine_rpm': 'Time distribution of engine RPM',
        #         'gear_position': 'Time distribution of gear position'
        #     }.get(field, field)
        #
        #     xaxes_title = {
        #         'wheel_speed': 'Wheel speed (Km/h)',
        #         'engine_rpm': 'Engine RPM',
        #         'gear_position': 'Gear position'
        #     }.get(field, field)
        #
        #     step = {
        #         'wheel_speed': 20,
        #         'engine_rpm': 1000,
        #         'gear_position': 1
        #     }.get(field, 20)
        #    
        #     row_data = self._time_dist(field, step)
        #
        #     data = [(s[0], t.total_seconds()/60) for (s, t) in row_data]
        #    
        #     df = DataFrame(data, columns=[field, 'time'])
        #        
        #     fig = px.area(df, x=field, y='time')
        #
        #     title = f"{title}, {' '.join(self.title.split())}"
        #
        #     fig.update_layout(title=title)
        #
        #     base_kargs = dict(showgrid=True, gridwidth=1,
        #         gridcolor='LightPink',
        #         minor=dict(ticklen=0, tickcolor="black", showgrid=True))
        #        
        #     fig.update_xaxes(title=xaxes_title, **base_kargs)           
        #     fig.update_yaxes(title='Time (minutes)', **base_kargs)
        #     tickvals = [s[0] for (s, t) in row_data]
        #     if field=='gear_position':
        #         tickvals=[0, 1, 2, 3, 4, 5, 6]
        #         ticktext=['N', '1st', '2nd', '3rd', '4th', '5th', '6th']
        #     else:
        #         fig.update_xaxes(tickangle=60)           
        #         ticktext = [f"{s[0]}~{s[1]}" for (s, t) in row_data]
        #     fig.update_xaxes(tickvals=tickvals, ticktext=ticktext)
        #
        #     max_y = df.loc[df['time'].idxmax()]['time']
        #     max_x = df.loc[df['time'].idxmax()][field]
        #
        #     fig.add_annotation(
        #         text=td_to_str(timedelta(seconds=max_y*60)),
        #         x=max_x, y=max_y*1.01,
        #         arrowhead=1, showarrow=True
        #     )
        #
        #     max_y = df.loc[df.last_valid_index()]['time']
        #     max_x = df.loc[df.last_valid_index()][field]
        #
        #     fig.add_annotation(
        #         text=td_to_str(timedelta(seconds=max_y*60)),
        #         x=max_x, y=max_y*1.01,
        #         arrowhead=1, showarrow=True
        #     )
        #
        #     image_filename = filename.with_name(
        #             f"{basename}_td_{field}").with_suffix('.jpg')
        #
        #     if not silent:
        #         print(f"Make file {repr(str(image_filename))}...", end="")
        #        
        #     fig.write_image(image_filename, width=800, height=350)
        #
        #     if not silent:
        #         print(" Ok")

        for field in ['gear_position', 'engine_rpm', 'wheel_speed']:

            title = {
                'wheel_speed': 'Distance distribution of wheel speed',
                'engine_rpm': 'Distance distribution of engine RPM',
                'gear_position': 'Distance distribution of gear position'
            }.get(field, field)

            xaxes_title = {
                'wheel_speed': 'Wheel speed (Km/h)',
                'engine_rpm': 'Engine RPM',
                'gear_position': 'Gear position'
            }.get(field, field)

            step = {
                'wheel_speed': 20,
                'engine_rpm': 1000,
                'gear_position': 1
            }.get(field, 20)
            
            row_data = self._distance_dist(field, step)
        
            data = [(s[0], d) for (s, d) in row_data]
            
            df = DataFrame(data, columns=[field, 'distance'])
                
            fig = px.area(df, x=field, y='distance')

            title = f"{title}, {' '.join(self.title.split())}"

            fig.update_layout(title=title)

            base_kargs = dict(showgrid=True, gridwidth=1,
                gridcolor='LightPink',
                minor=dict(ticklen=0, tickcolor="black", showgrid=True))
                
            fig.update_xaxes(title=xaxes_title, **base_kargs)           
            fig.update_yaxes(title='Distance (Km)', **base_kargs)
            tickvals = [s[0] for (s, d) in row_data]
            if field=='gear_position':
                tickvals=[0, 1, 2, 3, 4, 5, 6]
                ticktext=['N', '1st', '2nd', '3rd', '4th', '5th', '6th']
            else:
                fig.update_xaxes(tickangle=60)           
                ticktext = [f"{s[0]}~{s[1]}" for (s, d) in row_data]
            fig.update_xaxes(tickvals=tickvals, ticktext=ticktext)

            max_y = df.loc[df['distance'].idxmax()]['distance']
            max_x = df.loc[df['distance'].idxmax()][field]

            fig.add_annotation(
                text=f"{max_y:.2f} Km",
                x=max_x, y=max_y*1.01,
                arrowhead=1, showarrow=True
            )

            max_y = df.loc[df.last_valid_index()]['distance']
            max_x = df.loc[df.last_valid_index()][field]

            fig.add_annotation(
                text=f"{max_y:.2f} Km",
                x=max_x, y=max_y*1.01,
                arrowhead=1, showarrow=True
            )

            image_filename = filename.with_name(
                    f"{basename}_dd_{field}").with_suffix('.jpg')

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
            f"{basename}_table").with_suffix('.jpg')

        if not silent:
            print(f"Make file {repr(str(image_filename))}...", end="")
        
        fig.write_image(image_filename, width=500, height=500)

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
            f"{basename}_max_for_each_gear").with_suffix('.jpg')

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

 ![Wheel speed vs. time graph]({basename}_wheel_speed_vs_time.jpg)
 ![Acceleration vs. time graph]({basename}_acceleration_vs_time.jpg)
 ![Engine rpm vs. time graph]({basename}_engine_rpm_vs_time.jpg)
 ![Gear position vs. time graph]({basename}_gear_position_vs_time.jpg)
 ![Course vs. time graph]({basename}_course_vs_time.jpg)
 ![Wheel speed vs. distance graph]({basename}_wheel_speed_vs_distance.jpg)
 ![Acceleration vs. distance graph]({basename}_acceleration_vs_distance.jpg)
 ![Engine rpm vs. distance graph]({basename}_engine_rpm_vs_distance.jpg)
 ![Gear position vs. distance graph]({basename}_gear_position_vs_distance.jpg)
 ![Course vs. distance graph]({basename}_course_vs_distance.jpg)
 ![Distance distribution of wheel speed graph]({basename}_dd_wheel_speed.jpg)
 ![Distance distribution of engine rpm graph]({basename}_dd_engine_rpm.jpg)
 ![Distance distribution of gear position graph]({basename}_dd_gear_position.jpg)

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
        prev_coor = Coordinate(
            self.table[0]['gps_latitude'],
            self.table[0]['gps_longitude'])
        m = None
        for r in self.table:
            if m is None or m['wheel_speed']<r['wheel_speed']:
                m = r
            coor = Coordinate(r['gps_latitude'], r['gps_longitude'])
            km += prev_coor.km_to(coor)
            if km>=chunk:
                km=0
                name = f"{m['wheel_speed']} km/h"
                desc = f"{m['engine_rpm']} rpm @ {m['gear_position']} gear"
                args = [m[k] for k in ['gps_latitude', 'gps_longitude']] + [name] + [desc]
                gpxfile.add_way_point(*args)
                m = None
            prev_coor = coor
        return gpxfile
