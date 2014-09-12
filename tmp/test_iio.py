import sys
import string

high_channel = int(sys.argv[1])
neutral_channel =  int(sys.argv[2])
count = 0
first_error = True

prev_voltage = 0

while True:
  line = sys.stdin.readline()
  if not line:
    break
  values = line.split(",")
  voltage = int(values[high_channel]) - int(values[neutral_channel])
  if voltage >=0 and prev_voltage < 0:
    mod = count % 128
    if mod <127 and mod > 1:
      if first_error:
        first_error = False
      else:
        print "Error at sample ", count, " ", mod, " is not near 128... reseting"
      count = 0
  count+=1;


  prev_voltage = voltage

