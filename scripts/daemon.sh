echo "#####################################"
echo " jinad daemon installation script "
echo "#####################################"
echo "You will be prompted for your password by sudo."


# clear any previous sudo permission
sudo -k

# TODO: add as arg
export JINAD_PORT=8000
export JINAD_IP='0.0.0.0'
export CODENAME=$(lsb_release -sc)

echo "Initial setup"
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
sleep 5

echo "Installing td-agent for fluentd"
sudo bash <<FLUENT_SCRIPT
    mkdir -p /var/run/td-agent/
    touch /var/run/td-agent/td-agent.pid

    curl https://packages.treasuredata.com/GPG-KEY-td-agent | sudo apt-key add -

    # add treasure data repository to apt
    echo "deb http://packages.treasuredata.com/4/ubuntu/${CODENAME}/ ${CODENAME} contrib" > /etc/apt/sources.list.d/treasure-data.list

    # install the toolbelt
    apt-get update
    apt-get install -y td-agent

    # add FLUENT_CONF to agent file
    echo 'FLUENT_CONF=${FLUENT_CONF}' | sudo tee -a /etc/default/td-agent
    systemctl restart td-agent

FLUENT_SCRIPT


echo "Installing jinad as daemon"
sudo bash -c 'cat  << EOF > /etc/systemd/system/jinad.service
[Unit]
Description=JinaD (Jina Remote manager)
After=network.target td-agent.service

[Service]
User=ubuntu
Environment=JINAD_PORT='${JINAD_PORT}'
ExecStart=/usr/local/jinad
Restart=always

[Install]
WantedBy=multi-user.target
EOF'


echo "Starting jinad service"
sudo bash <<JINAD_START
    systemctl daemon-reload
    systemctl start jinad.service
JINAD_START


echo "Sleeping for 2 secs to allow jinad service to start"
sleep 2

curl -s -o /dev/null -w "%{http_code}" http://${JINAD_IP}:${JINAD_PORT}/v1/alive
