#!/bin/sh
cp /etc/fstab /etc/fstab.orig
cp fstab /etc/fstab
cp /etc/resolv.conf /tmp/resolv.conf
rm /etc/resolv.conf
ln -s /tmp/resolv.conf /etc/resolv.conf
	 
sync

echo "FSTAB overwritten, reboot to reload"
