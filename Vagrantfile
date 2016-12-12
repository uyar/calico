# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
    config.vm.box = "ubuntu/xenial64"
#    config.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-i386-vagrant-disk1.box"

    config.vm.provider "virtualbox" do |vb|
        # vb.customize ["modifyvm", :id, "--memory", "1024"]
        vb.customize ["modifyvm", :id, "--name", "itucs" ]
    end

    # Run apt-get update as a separate step in order to avoid
    # package install errors
    config.vm.provision :puppet do |puppet|
        puppet.manifests_path = "vagrant"
        puppet.manifest_file  = "aptgetupdate.pp"
    end

    # ensure we have the packages we need
    config.vm.provision :puppet do |puppet|
        puppet.manifests_path = "vagrant"
        puppet.manifest_file  = "pace.pp"
    end
end
