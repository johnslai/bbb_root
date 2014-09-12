rm dump1.csv
mkfifo dump1.csv  
./gdaq -c gdaq.json& 
cat dump1.csv | python ./test_iio.py 1 0 &

