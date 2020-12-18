#!/bin/bash
echo "#########################################################"
echo " jinad daemon installation script for Ubuntu/Debian"
echo "#########################################################"
echo "You will be prompted for your password by sudo."


# clear any previous sudo permission
sudo -k

# TODO: add as arg
export JINAD_PORT=8000
export JINAD_IP='0.0.0.0'
export CODENAME=$(lsb_release -sc)

echo -e "\n\nInitial setup for jinad\n"
sudo bash <<INIT
    # install python for jina & jinad
    apt-get update && apt-get -y install python3.8 python3.8-dev python3.8-distutils python3.8-venv python3-pip

    # env variable `JINAVER` can be set to install jina from a custom git branch
    export JINAVER=jina

    # install jinad
    pip3 install --prefix /usr/local jinad
INIT


# get custom fluentd path from jina resources
export FLUENT_CONF=$(python3 -c "import pkg_resources; print(pkg_resources.resource_filename('jina', 'resources/fluent.conf'))")

echo -e "\n\nInstalling td-agent for fluentd\n"
sudo bash <<FLUENT_SCRIPT
    mkdir -p /var/run/td-agent/
    touch /var/run/td-agent/td-agent.pid

    curl https://packages.treasuredata.com/GPG-KEY-td-agent | sudo apt-key add -

    # add treasure data repository to apt
    echo "deb http://packages.treasuredata.com/4/ubuntu/${CODENAME}/ ${CODENAME} contrib" | sudo tee /etc/apt/sources.list.d/treasure-data.list

    # install the toolbelt
    apt-get update
    apt-get install -y td-agent

    # add FLUENT_CONF to agent file
    echo 'FLUENT_CONF=${FLUENT_CONF}' | sudo tee -a /etc/default/td-agent
    sleep 1
    systemctl restart td-agent

FLUENT_SCRIPT

if [ $? -eq 0 ]; then
    echo -e "Successfully installed fluentd. Moving to the next step!"
else
    echo -e "Fluentd installation failed! Exiting"
    exit 1
fi


echo -e "\n\nInstalling jinad as daemon\n"
sudo bash -c 'cat  << EOF > /etc/systemd/system/jinad.service
[Unit]
Description=JinaD (Jina Remote manager)
After=network.target td-agent.service

[Service]
User=ubuntu
Environment=JINAD_PORT='${JINAD_PORT}'
ExecStart=/usr/local/bin/jinad
Restart=always

[Install]
WantedBy=multi-user.target
EOF'


echo -e "\n\nStarting jinad service\n"
sudo bash <<JINAD_START
    systemctl daemon-reload
    systemctl start jinad.service
JINAD_START

echo -e "Sleeping for 2 secs to allow jinad service to start"
sleep 2


if [[ $(curl -s -o /dev/null -w "%{http_code}" http://${JINAD_IP}:${JINAD_PORT}/v1/alive) -eq 200 ]]; then
    echo -e "\njinad started successfully as a daemon. please go to ${JINAD_IP}:${JINAD_PORT}/docs for more info"
else
    echo -e "\njinad server is not up. something went wrong! Exiting.."
    exit 1
fi
