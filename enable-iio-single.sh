#!/bin/sh

#
# Usage: iio-enable-single
#

#set -x

#delay in seconds
PRU_BUF_DELAY="4/10"
#N: IIO buffer size as a multiple integer of pru size
N=4

#set iio device driver path
IIO_PATH="/sys/bus/iio/devices/iio:device0"
SCRIPT_PATH="/usr/lib/systemd/scripts"

enable_channels() {
  # Disable IIO
  echo 0 > $IIO_PATH/buffer/enable
  # Enable all available channels
  for i in $(find  $IIO_PATH/scan_elements/ -iname in_*_en); do
    echo 1 > $i
  done
}


# In case while loop cannot exit
trap "echo exiting" SIGINT

# Remove module if not up for both channels
if test -d /sys/bus/iio/devices/iio\:device0; then
	rmmod max11166
fi 

# Ensure the module is loaded
modprobe max11166
enable_channels


#eval "num_ch=`find  $IIO_PATH/scan_elements/ -iname in_voltage*_en | wc -l`"
num_ch=`find  $IIO_PATH/scan_elements/ -iname in_voltage*_en | wc -l`
num_ch0=`cat $IIO_PATH/chan_count_master`
num_ch1=`cat $IIO_PATH/chan_count_slave`
#echo "num_ch: " ${num_ch}
# assume 0.4 seconds of pru buffer
# PRUSIZE = num_ch * 2 bytes/ch * 7680 scanlines/sec * 0.4 sec.
PRUSIZE=$(($num_ch *2*7680*$PRU_BUF_DELAY+0))
#echo "PRUSIZE: " ${PRUSIZE}
# set pru size and reload iio
rmmod max11166; modprobe max11166 extram_pool_sz=${PRUSIZE}
# IIO_BUF_LENGTH = 16x 0.4 sec 
IIO_BUF_LENGTH=$(($N*7680*${PRU_BUF_DELAY}))
#echo "IIO_BUF_LENGTH: " ${IIO_BUF_LENGTH}
echo ${IIO_BUF_LENGTH} > $IIO_PATH/buffer/length

enable_channels

echo ${PRUSIZE} > /home/root/pru_size
