#  Example

`ride.csv` is the file exported from the *Rideology App*

```shell
user@host:~/tmp/rideology2gpx/example$ rideology2gpx ride.csv -d "1979-08-09 09:25:00" --graph
Make file 'ride.gpx'... Ok
Make file 'ride_gear_shifts.gpx'... Ok
Make file 'ride_speed_shifts.gpx'... Ok
Make file 'ride_report.txt'... Ok
Make file 'ride_wheel_speed.jpeg'... Ok
Make file 'ride_engine_rpm.jpeg'... Ok
Make file 'ride_gear_position.jpeg'... Ok
Make file 'ride_table.jpeg'... Ok
Make file 'ride_max_for_each_gear.jpeg'... Ok
Make file 'ride_report.md'... Ok

From gas station to next gas station
==== === ======= == ==== === =======
    
Max engine speed:  3846 rpm
Max wheel speed:   60 km/h
Max water temp:    101 ℃
Avg idle speed:    1202 rpm
Avg speed:         30 km/h
Total time:        0:07:49
Distance:          1.87 km
Starting point:    S034°30′29.52″ E058°28′46.70″
Ending point:      S034°29′53.65″ E058°29′02.93″

Max for each gear
--- --- ---- ----

  Gear    rpm    km/h
     1   3137      29
     2   3611      45
     3   3784      58
     4   3846      60

user@host:~/tmp/rideology2gpx$ 
```

You get these `.gpx` files:

- `ride.gpx`
- `ride_gear_shifts.gpx`
- `ride_speed_shifts.gpx`

You get these `.jpeg` files:

- `ride_wheel_speed.jpeg`
- `ride_engine_rpm.jpeg`
- `ride_gear_position.jpeg`
- `ride_table.jpeg`
- `ride_max_for_each_gear.jpeg`

And reports:

- `ride_report.txt`
- `ride_report.md`
