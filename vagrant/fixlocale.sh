#!/bin/sh

sudo chmod go+w /etc/bash.bashrc
sudo echo >> /etc/bash.bashrc
sudo echo export LANGUAGE=en_US.UTF-8 >> /etc/bash.bashrc
sudo echo export LANG=en_US.UTF-8 >> /etc/bash.bashrc
sudo echo export LC_ALL=en_US.UTF-8 >> /etc/bash.bashrc
sudo chmod go-w /etc/bash.bashrc

sudo locale-gen en_US.UTF-8
sudo dpkg-reconfigure locales
