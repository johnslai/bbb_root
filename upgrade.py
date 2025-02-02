#!/usr/bin/python
import pdb
import os.path
import subprocess
import shutil
import os
import urllib2
import sys
import re
_DEBUG_ = False

# get new md5Sum
# get current md5Sum:
# compare
def compare(md5Sum1, md5Sum2):
  return md5Sum1 == md5Sum2

# platform can be "bbb" or "sim"
platform = "bbb"
# Assume partitions are named with partitionPrefix + a number
if platform == "bbb":
  partitionPrefix = "/dev/mmcblk0p"
else:
  partitionPrefix = "/dev/sda"
# The url remote server for fetching
# 1. firmwarePath
# 2. firmwarePath.md5
# It could be either a ip address or a fqdn with an optional port
server = "http://192.168.1.71:8000"
firmwarePath = "/console-image-beaglebone.tar.gz"
#firmwarePath = "/console-image-beaglebone.tar.xz"
md5Path = firmwarePath + ".md5"

# A mountPoint for binding to the spare partion
# It will be created if not already exists
mountPoint = "/mnt/spare/"
bootMountPoint = "/mnt/boot/"

def httpGetFile(url):
  try:
    u = urllib2.urlopen(url)
  except urllib2.URLError as e:
    print "URLError: " 
    print sys.exc_info()[:2]
    raise
  content = u.read()
  u.close()

  print "size of content= " + str(len(content))
  return content

# Get content from url and write to filePath
def httpGetFile2(url, filePath):
  try:
    u = urllib2.urlopen(url)
  except urllib2.URLError as e:
    print "URLError: " 
    print sys.exc_info()[:2]
    raise
  CHUNK = 16*1024
  with open(filePath, 'wb') as fp:
    while True:
      chunk = u.read(CHUNK)
      if not chunk: break
      fp.write(chunk)
  return

def getNewMd5Sum():
  md5Url = server + md5Path
  # keep md5sum, throw away filename
  return httpGetFile(md5Url).split(' ', 1)[0]

def getNewFirmware():
  firmwareUrl = server + firmwarePath
  return httpGetFile(firmwareUrl)

def getNewFirmware2(filePath):
  firmwareUrl = server + firmwarePath
  httpGetFile2(firmwareUrl, filePath)
  return

def getCurrMd5Sum():
  import os.path
  fn = md5Path
  print fn
  if not os.path.isfile(fn): 
    print "Current Firmware has no md5sum " + fn + "."
    return ""
  f = open(fn, 'r')
  currMd5Sum = f.read()
  f.close()
  return currMd5Sum

def calculateMd5Sum(string):
  import hashlib

  #f = open("/tmp/tmpfile", "wb")
  #f.write(string)
  #f.flush()
  #f.close()
  #print "/tmp/tmpfile written"

  m = hashlib.md5()
  m.update(string)
  md5Sum = m.hexdigest()

  #print "md5Sum: " + md5Sum
  #pdb.set_trace()

  return md5Sum

def calculateMd5Sum2(file):
  import hashlib

  #f = open("/tmp/tmpfile", "wb")
  #f.write(string)
  #f.flush()
  #f.close()
  #print "/tmp/tmpfile written"

  m = hashlib.md5()
  CHUNK = 16*1024
  with open(file, "rb") as fp:
    while True:
      chunk = fp.read(CHUNK)
      if not chunk: break
      m.update(chunk)
  md5Sum = m.hexdigest()

  print "calculated md5Sum: " + md5Sum
  #pdb.set_trace()

  return md5Sum

def validateFirmware(firmware, md5Sum):
  calculatedMd5Sum = calculateMd5Sum(firmware)
  isValid = compare(calculatedMd5Sum, md5Sum)
  if not isValid:
    print "calculatedMd5Sum, md5Sum = " + calculatedMd5Sum + " " +  md5Sum
  return isValid

def validateFirmwareFile(firmwareFile, md5Sum):
  calculatedMd5Sum = calculateMd5Sum2(firmwareFile)
  isValid = compare(calculatedMd5Sum, md5Sum)
  if not isValid:
    print "calculatedMd5Sum, md5Sum = " + calculatedMd5Sum + " " +  md5Sum
  return isValid

def getSparePartitionNumber():
  import subprocess
  mount = subprocess.check_output(["mount"])
  pattern = partitionPrefix + ".* / "
  p = re.compile(pattern)
  m = p.findall(mount)
  if m:
    currentPartitionNumber = int(m[0][len(partitionPrefix)])
    # toggle between 2 and 3
    if currentPartitionNumber == 2: 
      sparePartitionNumber = 3
    elif currentPartitionNumber == 3:
      sparePartitionNumber = 2
    else:
      sparePartitionNumber = 0
  else:
    sparePartitionNumber =  0
  return sparePartitionNumber

def validate(sparePartitionNumber):
  return sparePartitionNumber == 2 or sparePartitionNumber == 3

def mount(sparePartitionNumber, mountPoint):
  import subprocess
  sparePartition = partitionPrefix + str(sparePartitionNumber)
  if not os.path.exists(mountPoint):
    os.makedirs(mountPoint)
  if os.path.ismount(mountPoint):
    print 'umount ' + mountPoint
    subprocess.check_call( [ 'umount', '-f', mountPoint ])

  subprocess.check_call( [ 'mount', sparePartition, mountPoint ])
  return

def writeFirmware(firmware, filePath):
  #import contextlib
  #import lzma
  #import tarfile
  f = open(filePath, "wb")
  f.write(firmware)
  # tar sometimes returns "short read" error
  # flush buffer to fix
  f.flush()
  # sync might not be needed
  subprocess.check_call( [ 'sync' ] )
  f.close()
  return

def decompress(srcFile, filePath):
  #import tarfile
  import os

  #with tarfile.open(srcFile, mode="r") as t:
    #t.extractall(filePath)
  # tar.tar has to be installed
  #if not os.path.isfile("tar.tar"): return False
  try:
    # system command from emmc.sh
    subprocess.check_call( [ 'tar', 'mxf', srcFile, '-C', filePath, '--numeric-owner' ] )
  except subprocess.CalledProcessError as e:
    print "tar returned error: " + str(e)

  return

def migrateConfiguration(dstDir):
  files = [
      "/var/lib/connman/wifi.config",
      "/etc/passwd",
      "/etc/shadow",
      ]
  copyFiles(files, dstDir)

  dirs = [
      "/etc/ssh/",
      ]
  copyDirs(dirs, dstDir)

  return

def copyFiles(files, dstDir):
  for file in files:
    dstfile = dstDir + file
    dstDir2 = os.path.dirname(dstfile)
    if not os.path.exists(dstDir2):
      os.makedirs(dstDir2)
    if (os.path.isfile(file)):
      shutil.copy2(file, dstDir2)
  return

def copyDirs(dirs, dstDir):
  for dir in iter(dirs):
    dstDir2 = dstDir + dir
    print dstDir2
    if os.path.exists(dstDir2): 
      shutil.rmtree(dstDir2)
    shutil.copytree(dir, dstDir2)
  return

def markRootFsPartition(sparePartitionNumber):
  string_for_switching_partition='mmcpartition=2\n\
uenvcmd=echo Starting uenvcmd; setenv mmcroot /dev/mmcblk0p${mmcpartition} ro; setenv bootpart 1:${mmcpartition}; echo mmcdev=${mmcdev} mmcroot=${mmcroot}; mmc dev ${mmcdev}; echo Finished uenvcmd'

  mount(1, bootMountPoint)
  replacement = "mmcpartition=" + str(sparePartitionNumber)
  with open(bootMountPoint + "uEnv.txt", "r") as fp:
    string_before = fp.read()
    print "before: " + string_before
    string_after = re.sub(r"mmcpartition=\d", replacement, string_before)
    print "after: " + string_after
    if string_before == string_after: # we should add the uenvcmd manually
      string_for_switching_partition = re.sub(r"mmcpartition=\d", replacement, string_for_switching_partition)
      string_after += string_for_switching_partition
  with open(bootMountPoint + "uEnv.txt", "w") as fp:
    fp.write(string_after)
    fp.flush()
  return

def test_markRootFsPartition():
  markRootFsPartition(3)
  pdb.set_trace()
  return

def main():
  try:
    currMd5Sum = getCurrMd5Sum()
    md5Sum = getNewMd5Sum()
    if _DEBUG_: pdb.set_trace()
    # if checksum is different
    #   then grab actual firmware
    # validate firmware
    if compare(md5Sum, currMd5Sum): 
      print "No Upgrade: Firmware Checksum identical."
      return
    print "compare md5Sum " + md5Sum + " done ..."
    if _DEBUG_: pdb.set_trace()

    # Look for spare partition
    # mount spare partition to mountPoint
    # empty the partition 
    sparePartitionNumber = getSparePartitionNumber()
    if not validate(sparePartitionNumber):
      print "No Spare Partition for upgrade."
      return
    print "sparePartitionNumber=" + str(sparePartitionNumber)
    if _DEBUG_: pdb.set_trace()

    mount(sparePartitionNumber, mountPoint)
    if _DEBUG_: pdb.set_trace()

    shutil.rmtree(mountPoint, ignore_errors=True)
    if _DEBUG_: pdb.set_trace()

    #firmware = getNewFirmware()
    firmwareFile = mountPoint + "fw"
    getNewFirmware2(firmwareFile)

    if _DEBUG_: pdb.set_trace()
    #if not validateFirmware(firmware, md5Sum): 
    if not validateFirmwareFile(firmwareFile, md5Sum): 
      print "New Firmware is not valid"
      return
    print "validateFirmware done ..."
    if _DEBUG_: pdb.set_trace()

    #writeFirmware(firmware, firmwareFile)
    #pdb.set_trace()

    decompress(firmwareFile, mountPoint)
    if _DEBUG_: pdb.set_trace()

    os.remove(firmwareFile)
    if _DEBUG_: pdb.set_trace()

    # write md5Sum to spare partition
    fName = mountPoint + md5Path
    f = open(fName, "w")
    f.write(md5Sum)
    f.close()
    if _DEBUG_: pdb.set_trace()

    # migrate configuration
    migrateConfiguration(mountPoint)
    #subprocess.check_call( ['./migrate_configuration.sh', mountPoint])

    # mount uboot
    # mark rootfs partition
    # todo: reboot only if gdaq is idle
    markRootFsPartition(sparePartitionNumber)

    # flush buffer before reboots
    subprocess.check_call( [ 'sync' ] )

    if _DEBUG_: pdb.set_trace()

    subprocess.check_call( [ '/sbin/shutdown', '-r', 'now' ] )
    print "Upgrade Succeeded..."
  except:
    print "Upgrade Failed..."
    raise
  return

def test_validateFirmwareFile():
  md5Sum = "71814215632c10882e240fbaa3e5c2b3"
  firmwareFile = mountPoint + "fw"
  if not validateFirmwareFile(firmwareFile, md5Sum): 
    print "New Firmware is not valid"
    return
  print "validateFirmware done ..."
  if _DEBUG_: pdb.set_trace()
  return

def test_decompress():
  print "test_decompress ... "
  srcFile = mountPoint + "fw"
  filePath = mountPoint
  decompress(srcFile, filePath)
  print "test_decompress done ... "
  if _DEBUG_: pdb.set_trace()
  return

if __name__ == '__main__':
  #test_validateFirmwareFile()
  #test_decompress()
  #test_markRootFsPartition()
  main()
  #subprocess.check_call( ['./migrate_configuration.sh', mountPoint])

#wget http://192.168.1.70:8000/console-image-beaglebone.tar.xz 
#GRc2375Q0sw8FFSgjhB3Sw==
#todo: migrate wifi config

#/LC5/FYvOgsXLixHsL/8UQ==

