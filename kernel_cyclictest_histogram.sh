#!/bin/bash
#
# Creates an image containing the histogram of average latencies
# recorded when testing PREEMPT_RT with cyclictest
#
# Based on https://www.osadl.org/Create-a-latency-plot-from-cyclictest-hi.bash-script-for-latency-plot.0.html
#
# Dependencies:
# sudo apt install rt-tests
# sudo apt install gnuplot
#
# Usage:
# sudo bash rt_cyclictest_histogram.sh <n_of_cycles> <n_of_hists>
#
# Default values:
# n_of_cycles:  10000000
# n_of_hists:   100
#

N_OF_CYCLES=${1-10000000}
N_OF_HISTS=${2-100}

# 1. Redirect the output of cyclictest to a file
cyclictest -l "$N_OF_CYCLES" -m -Sp90 -i 200 -h "$N_OF_HISTS" -q > output

# 2. Get average latency
avg=$(grep "Avg Latencies" output | tr " " "\n" | sort -n | tail -1 | sed s/^0*//)

# 3. Grep data lines, remove empty lines and create a common field separator
grep -v -e "^#" -e "^$" output | tr " " "\t" > histogram

# 4. Create two-column data sets with latency classes and frequency values for each core
for i in $(seq 1 "$(nproc)")
do
  column=$((i + 1))
  cut -f1,"$column" histogram > histogram"$i"
done

# 5. Create plot command header
echo -n -e "set title \"Latency plot\"\n\
set terminal png\n\
set xlabel \"Latency (us), avg $avg us\"\n\
set logscale y\n\
set xrange [0:$N_OF_HISTS]\n\
set yrange [0.8:*]\n\
set ylabel \"Number of latency samples\"\n\
set output \"plot.png\"\n\
plot " > plotcmd

# 6. Append plot command data references
for i in $(seq 1 "$(nproc)")
do
  if test "$i" != 1
  then
    echo -n ", " >> plotcmd
  fi
  cpuno=$((i - 1))
  if test "$cpuno" -lt 10
  then
    title=" CPU$cpuno"
   else
    title="CPU$cpuno"
  fi
  echo -n "\"histogram$i\" using 1:2 title \"$title\" with histeps" >> plotcmd
done

# 7. Execute plot command
gnuplot -persist < plotcmd

# 8. Display the plot
xdg-open plot.png

# 9. Remove all textual outputs
sudo rm histogram
sudo rm histogram*
sudo rm output
sudo rm plotcmd
