# Gnuplot script file for plotting data in file "data-2016-04-02_160518.dat"
# This file is called   data-2016-04-02_160518.gnuplot.p
# Run it: gnuplot> load 'data-2016-04-02_160518.gnuplot.p'
reset
# to file:
set term png

set output "data-2016-04-02_160518.gnuplot.png
set terminal pngcairo size 800,600 enhanced font 'Verdana,8'

# set terminal postscript portrait
# set size .75,.75

set autoscale                        # scale axes automatically
set xdata time
set timefmt "\'%Y-%m-%d %H:%M:%S\'"
set format x "%H:%M:%S"
set xtics rotate by 90 offset 0,-2.5 out nomirror

#This places the key in the bottom left corner, left-justifies the text, gives it a title, and draws a box around it in linetype 3:
set key right bmargin
set xtic auto                          # set xtics automatically
set ytic auto                          # set ytics automatically
set title "Temperature of Water on Hotplate over Time"
set xlabel "Datetime"
set ylabel "Temp (Raw Sensor Value)"
set style line 1 lc rgb '#666666' lt 1 lw 1 # --- gray
set style line 2 lc rgb '#0060ad' lt 1 lw 1 # --- blue mk1
set style line 3 lc rgb '#dd181f' lt 1 lw 1 # --- red mk2
set style line 4 lc rgb '#66A61E' lt 1 lw 1 # --- green mk3
set style line 5 lc rgb '#000000' lt 1 lw 1 # --- black mk4
set style line 6 lc rgb '#7570B3' lt 1 lw 1 # --- liliac

set grid ytics lc rgb "#bbbbbb" lw 1 lt 0
set grid xtics lc rgb "#bbbbbb" lw 1 lt 0
set mxtics 4
set mytics 4

# Labels based off of MK Events:
set label "Boiling Point" at "\'2016-04-02 16:23:36.10:36.10\'",400 tc ls 2
set arrow from "\'2016-04-02 16:23:36.10:36.10\'",402 to "\'2016-04-02 16:23:36.10\'",452  ls 2

set label "Sensor moved" at "\'2016-04-02 16:17:24.08\'", 318 tc ls 4
set arrow from "\'2016-04-02 16:17:24.08\'", 318 to "\'2016-04-02 16:17:24.08\'", 368  ls 4

set label "Heat Removed" at "\'2016-04-02 16:24:20.52\'", 411 tc ls 3
set arrow from "\'2016-04-02 16:24:20.52\'", 411 to "\'2016-04-02 16:24:20.52\'", 461  ls 3

set label "Sensor moved" at "\'2016-04-02 16:33:35.97\'",470 tc ls 5
set arrow from "\'2016-04-02 16:33:35.97\'", 470 to "\'2016-04-02 16:33:35.97\'", 428  ls 5

set label "Sensor moved" at "\'2016-04-02 16:57:30.68\'",315 tc ls 5
set arrow from "\'2016-04-02 16:57:30.68\'", 315 to "\'2016-04-02 16:57:30.68\'", 365  ls 5


plot  "data-2016-04-02_160518.dat" using 1:3 with line ls 6 title 'Temperature',\
