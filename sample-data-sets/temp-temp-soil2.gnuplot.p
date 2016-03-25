# Gnuplot script file for plotting data in file "temp-temp-soil2.dat"
# This file is called   temp-temp-soil2.p
# Run it: gnuplot> load 'temp-temp-soil2.p'

# to file:
# set term png

# set output "filename.ps"
# set terminal postscript portrait
# set size .75,.75

set autoscale                        # scale axes automatically
set xdata time
set timefmt "\'%Y-%m-%d %H:%M:%S\'"
set format x "%H:%M:%S"
set xtics rotate by 90 offset 0,-2.5 out nomirror

#This places the key in the bottom left corner, left-justifies the text, gives it a title, and draws a box around it in linetype 3: 
set key below 
#outside bmargin bottom Left title 'Legend' box 

unset log                              # remove any log-scaling
unset label                            # remove any previous labels
set xtic auto                          # set xtics automatically
set ytic auto                          # set ytics automatically
set title "Data file"
set xlabel "Datetime"
set ylabel "Temp (deg F)"

# Comments:
# set label "Yield Point" at 0.003,260
# set arrow from 0.0028,250 to 0.003,280

 
plot  "temp-temp-soil2.dat" using 1:3 with points title 'Ch 1 Temp ',\
      "temp-temp-soil2.dat" using 1:4 with points title 'Ch 2 Temp '

   
