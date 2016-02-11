# raspberrypi-data-acq

Scripts for using a Raspberry Pi 2 B+ as a data acquisition box.

## Supported Platforms

Raspberry Pi 2 B+

## Attributes

<table>
  <tr>
    <th>Key</th>
    <th>Type</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><tt>-s,--sleep</tt></td>
    <td>Float</td>
    <td>Time to sleep between measurements. Like a polling frequency, if set to 1 it will take a new measurement roughly every second, .5 is every half second, etc.</td>
  </tr>
  <tr>
    <td><tt>-c,--channels</tt></td>
    <td>Integer</td>
    <td>Number of channels to record</td>
  </tr>
  <tr>
    <td><tt>-o,--outfile</tt></td>
    <td>String</td>
    <td>CSV Output file to use</td>
  </tr>
  <tr>
    <td><tt>-d,--debug</tt></td>
    <td>String</td>
    <td>Output extra messages for debugging</td>
  </tr>
  <tr>
    <td><tt>-t,--type</tt></td>
    <td>String</td>
    <td>Data Type for each channel. (See explanation below)</td>
  </tr>
</table>

### Data Type

Data type is the type of data coming on the channel, automatic conversions can ve done. If none specified then it uses 'raw' as the default which is the straight reading from the GPIO pin (values 0-1024). Other supported types are 'ctemp' which converts the value to a Temperature in Celsius, and 'ftype' which converts the value to a Temperature in Fahrenheit. Data types can be mixed and matched, assume a three channel setup, you could do raw for the first channel, ctemp for the 2nd and ftemp for the third. Such a setup would look like:

```python
sudo python collectdata.py -c 3 -t raw ctemp ftemp
```

## Usage

Basic Program flow:
* Specify the number of channels, output file, and/or any other parameters.
* The script runs indefinitely logging data to the output file and displaying on screen
* Use Ctrl-C to quit.

### python collectdata.py

Run normally using all defaults:
```python
raspberrypi-pin-onoff $ sudo python ./collectdata.py
```

Record data from 4 different sources:
```python
raspberrypi-pin-onoff $ sudo python ./collectdata.py -c 4
```

Record data from 4 different sources at 1/10 of a second intervals:
```python
raspberrypi-pin-onoff $ sudo python ./collectdata.py -c 4 -s 0.1
```

Record data from 4 different sources at 1/10 of a second intervals, output to mydata.csv in the home directory:
```python
raspberrypi-pin-onoff $ sudo python ./collectdata.py -c 4 -s 0.1 -o ~/mydata.csv
```

Record data from 3 different sources the first as raw data, Celsius Temperature for the 2nd and 3rd:
```python
raspberrypi-pin-onoff $ sudo python ./collectdata.py -c 3 -t raw ctemp ctemp
```

## License and Authors

Author:: Kevin Kingsbury (@kmkingsbury)

Apache 2.0
