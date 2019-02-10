#!/bin/bash

# get python3.6.7 up and running from source

pushd
mkdir -p $HOME/build
cd $HOME/build
echo "installing python3.6.7 to $HOME/.local"
wget https://www.python.org/ftp/python/3.6.7/Python-3.6.7.tgz
tar fx Python-3.6.7.tgz
cd Python-3.6.7
./configure --enable-optimizations --prefix=$HOME/.local
make -j8
make install

# go back and install a venv
popd
$HOME/.local/bin/python3.6 -m venv venv --copies

