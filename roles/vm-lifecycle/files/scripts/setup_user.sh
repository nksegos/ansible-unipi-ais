#!/bin/bash

usage(){
	echo "This script is used to setup a user with passwordless sudo privileges and allow ssh connections corresponding to a specific key."
	echo "Please note that such a user constitutes a security risk and should be NEVER used in production enviroments."
	echo ""
	echo "Usage:"
	echo " 		./setup_user.sh USER PAYLOAD"
	echo ""
	echo "USER 		-> 	the name of the user to be created. By default, the value is set to 'ansible'."
	echo "PAYLOAD 	-> 	the path for the public key to be injected. By default, the value is set to '/root/.ssh/authorized_keys' ."
	echo ""
	echo ""
	echo "Examples:"
	echo " 		./setup_user.sh myuser:file:/path/to/the/key"
	echo "		./setup_user.sh "
	echo "		./setup_user.sh myuser"
	echo " 		./setup_user.sh help"
	echo ""
	echo ""
}

USR=
KEY=
KEY_BKP=


unclean_exit(){
	if grep -qw $USR /etc/passwd ; then
		userdel -r $USR > /dev/null 2>&1
		if grep -qw "$USR   ALL=(ALL:ALL) NOPASSWD:ALL" /etc/sudoers ; then
			sed -i "/$USR   ALL=(ALL:ALL) NOPASSWD:ALL/d" /etc/sudoers
			if [ -f $KEY_BKP ]; then
				cat $KEY_BKP > $KEY
			fi
		fi
	fi
	exit 1
}
	
trap unclean_exit ERR

if [ -z $1 ]; then
	USR="ansible"
	KEY=/root/.ssh/authorized_keys
elif [[ "${1,,}" == "help" ]]; then
	usage
	exit 0
else
	if [ -z $2 ]; then
		USR=$1
		KEY=/root/.ssh/authorized_keys
	elif ! [ -f $2 ]; then
		echo "Error: Invalid public key file path."
		exit 1
	else
		USR=$1
		KEY=$2
	fi
fi


#  Create user
useradd -m -s /bin/bash $USR
echo "${USR}:$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32; echo '')" | chpasswd

# Install and grant sudo and upgrade ssh
if ! grep -q 'Debian\|Ubuntu' /etc/*-release; then
#	yum check-update > /dev/null 2>&1
	yum update openssh openssh-server openssh-clients -y #> /dev/null 2>&1
	yum install sudo -y #> /dev/null 2>&1
	usermod -aG wheel $USR	
else
	export DEBIAN_FRONTEND=noninteractive
	apt update -q #> /dev/null 2>&1
	apt install -yq sudo policycoreutils #> /dev/null 2>&1
	apt install -yq --only-upgrade openssh-server openssh-client openssh-sftp-server #> /dev/null 2>&1
	ssh-keygen -A #> /dev/null 2>&1
	systemctl restart sshd #> /dev/null 2>&1
	usermod -aG sudo $USR
fi

echo "$USR   ALL=(ALL:ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create user's .ssh dir and set perms
mkdir -p /home/${USR}/.ssh
chmod 700 /home/${USR}/.ssh

# Move key to the correct position and set perms
KEY_BKP=$(mktemp)
cat $KEY > $KEY_BKP
mv $KEY /home/${USR}/.ssh/authorized_keys
chmod 600 /home/${USR}/.ssh/authorized_keys

# Chown recursively .ssh dir
chown -R $USR:$USR /home/${USR}/
su $USR << EOF
	restorecon -Rv ~/.ssh
EOF

exit 0
