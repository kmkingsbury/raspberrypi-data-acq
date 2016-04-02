# Gnuplot script file for plotting data in file "data-2016-04-02_173628.dat"
# This file is called   data-2016-04-02_173628.gnuplot.p
# Run it: gnuplot> load 'data-2016-04-02_173628.gnuplot.p'
reset
# to file:
# set term png
set term aqua

set output "data-2016-04-02_173628.gnuplot_freq.png
set terminal pngcairo size 800,600 enhanced font 'Verdana,10'

set autoscale                        # scale axes automatically
#set xtics rotate by 90 offset 0,-.5 out nomirror

#This places the key in the bottom left corner, left-justifies the text, gives it a title, and draws a box around it in linetype 3:
set key right bmargin
set xtic auto                          # set xtics automatically
set ytic auto                          # set ytics automatically
set title "Frequency of Reading Value from GPIO with Nothing Attached"
set xlabel "Value"
set ylabel "Freq"
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

set xrange [-10:410]
#Labels based off of MK Events:
#set label "Boiling Point" at "\'2016-04-02 16:23:36.10:36.10\'",400 tc ls 2
#set arrow from "\'2016-04-02 16:23:36.10:36.10\'",402 to "\'2016-04-02 16:23:36.10\'",452  ls 2

#set boxwidth 0.05 absolute
set style fill solid 1.0 noborder
bin_width = 1;

bin_number(x) = floor(x/bin_width)

rounded(x) = bin_width * ( bin_number(x) + 0.5 )

plot 'data-2016-04-02_173628_2.dat' using (rounded($1)):(2) smooth frequency with boxes
