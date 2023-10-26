# -*- mode: ruby -*-
# vi: set ft=ruby :

$script = <<-SCRIPT
echo "#### Setting up MRI4ALL Development Environment"
cd /vagrant
./install.sh
SCRIPT

Vagrant.configure(2) do |config|
  config.vm.box = "bento/ubuntu-22.04" # 22.04 LTS
  config.vm.provision "shell", inline: $script
  
  config.vm.provider "virtualbox" do |vb|
    # Increase memory for Virtualbox
    vb.memory = "4096"
    vb.cpus = 2	
    # Display the VirtualBox GUI when booting the machine
    vb.gui = true
    vb.customize ["modifyvm", :id, "--vram", "128"]
    vb.customize ["modifyvm", :id, "--clipboard-mode", "bidirectional"]
  end  
end
