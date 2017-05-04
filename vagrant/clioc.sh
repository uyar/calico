#!/bin/sh

dn="$(dirname $1)"
bn="$(basename $1)"
vagrant ssh -c "cd /vagrant/$dn && clioc $bn"
