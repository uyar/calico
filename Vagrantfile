# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
    config.vm.box = "bento/ubuntu-16.10-i386"

    config.vm.provider "virtualbox" do |vb|
        # vb.customize ["modifyvm", :id, "--memory", "1024"]
        vb.customize ["modifyvm", :id, "--name", "calico"]
    end

    config.vm.provision "shell",
        inline: "apt update -y"

    config.vm.provision "shell",
        inline: "apt install -y g++ libyaml-dev mercurial fakechroot"

    config.vm.provision "shell",
        inline: "apt install -y python3 python3-dev python3-pip"

    config.vm.provision "shell",
        inline: "pip3 install -U pip"

    config.vm.provision "shell",
        inline: "pip3 install -U calico"

end
