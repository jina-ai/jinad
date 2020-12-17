# jinad - The Daemon to manage Jina remotely

<p align="center">
<a href="#license"><img src="https://github.com/jina-ai/jinad/blob/main/.github/badges/license-badge.svg?raw=true" alt="Jina" title="Jinas is licensed under Apache-2.0"></a>
<a href="https://pypi.org/project/jina/"><img src="https://github.com/jina-ai/jinad/blob/main/.github/badges/python-badge.svg?raw=true" alt="Python 3.7 3.8" title="Jinas supports Python 3.7 and above"></a>
<a href="https://pypi.org/project/jina/"><img src="https://img.shields.io/pypi/v/jinad?color=%23099cec&amp;label=PyPI&amp;logo=pypi&amp;logoColor=white" alt="PyPI"></a>
<a href="https://hub.docker.com/r/jinaai/jina/tags"><img src="https://img.shields.io/docker/v/jinaai/jinad?color=%23099cec&amp;label=Docker&amp;logo=docker&amp;logoColor=white&amp;sort=semver" alt="Docker Image Version (latest semver)"></a>
<a href="https://github.com/jina-ai/jinad/actions?query=workflow%3ACI"><img src="https://github.com/jina-ai/jinad/workflows/CI/badge.svg" alt="CI"></a>
<a href="https://github.com/jina-ai/jinad/actions?query=workflow%3ACD"><img src="https://github.com/jina-ai/jinad/workflows/CD/badge.svg?branch=main" alt="CD"></a>
<a href="https://codecov.io/gh/jina-ai/jinad"><img src="https://codecov.io/gh/jina-ai/jinad/branch/main/graph/badge.svg" alt="codecov"></a>
</p>

## Set up jinad on remote machines

The easist way of running `jinad` is to use the docker image,

```bash
sudo docker run --rm -d --network host jinaai/jinad
```

You can verify whether it running properly by

```bash
export JINAD_IP=1.2.3.4
export JINAD_PORT=8000
curl -s -o /dev/null -w "%{http_code}"  http://$JINAD_IP:$JINAD_PORT/v1/alive
```

> `1.2.3.4` is the public ip of your instance. By default, jinad is listening to the port `8000`


## Use Case 1: Create Pods on remote machines
After having `jinad` running on the remote machine, you can directly create and use the remote pods from your local machine

```python
f = (Flow()
     .add(name='p1', uses='_logforward')
     .add(name='p2', host='1.2.3.4', port_expose='8000', uses='_logforward')
with f:
     f.search_lines(lines=['jina', 'is', 'cute'], output_fn=print)
```


## Use Case 2: Create Pods on remote using Jina CLI


```
jina pod --host 1.2.3.4 --port-expose 8000 --uses _logforward
```

> Make sure `jinad` is running in `pod` context

> we need to pass a valid `role` for this (pydantic issue to be fixed)


<!--## Use Case 3: Create Peas on remote using Jina CLI

```
jina pea --host 1.2.3.4 --port-expose 8000 --role SINGLETON
```

> Make sure `jinad` is running in `pea` context

> we need to pass a valid `role` for this (pydantic issue to be fixed)-->

## Use Case 3: Create a Flow on remote

```
curl -s --request PUT "http://1.2.3.4:8000/v1/flow/yaml" -H  "accept: application/json" -H  "Content-Type: multipart/form-data" -F "uses_files=@helloworld.encoder.yml" -F "uses_files=@helloworld.indexer.yml" -F "pymodules_files=@components.py" -F "yamlspec=@helloworld.flow.index.yml"
```

> Make sure `jinad` is running in `flow` context





<!--1. Create a new instance on AWS and log into the instance

```bash
ssh -i your.pem ubuntu@ec2-1-2-3-4.us-east-2.compute.amazonaws.com
```


2. Install the required packages

```bash
sudo apt-get update
sudo apt-get -y install python3.8 python3.8-dev python3.8-distutils python3.8-venv python3-pip
```

3. Install jina

```bash
git clone https://github.com/jina-ai/jina.git
cd jina
pip3 install -e .
```

4. Install jinad

```bash
git clone https://github.com/jina-ai/jinad.git
cd jinad/
pip3 install -r jinad/requirements.txt
```

5. Install & Configure `Fluentd`

```
sudo mkdir -p /var/run/td-agent/
sudo touch /var/run/td-agent/td-agent.pid
curl -L https://toolbelt.treasuredata.com/sh/install-ubuntu-focal-td-agent4.sh | sh
echo 'FLUENT_CONF=/home/ubuntu/jina/jina/resources/fluent.conf' | sudo tee -a /etc/default/td-agent
sudo systemctl restart td-agent
```

5. Create a systemd service

```
sudo bash -c 'cat  << EOF > /etc/systemd/system/jinad.service
[Unit]
Description=jina remote manager
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/jinad/jinad
Environment=JINAD_PORT=8000
Environment=JINAD_CONTEXT=all
ExecStart=/usr/bin/python3.8 main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF'
```

6. Start the service to be constantly running in the background

```
sudo systemctl daemon-reload
sudo systemctl start jinad.service

```

7. To follow the logs via journald


```
journalctl -u jinad -f
```

8. Verify whether jinad is properly running, one can use the following lines

```bash
export JINAD_IP=1.2.3.4
export JINAD_PORT=8000
curl -s -o /dev/null -w "%{http_code}"  http://$JINAD_IP:$JINAD_PORT/v1/alive
```

Alternatives, open `http://1.2.3.4:8000/docs` on your browser and you will see the API documentations of jinad.


> env `JINAD_CONTEXT` is used to set up the jinad context. The possible values are  `all` (default), `flow`, `pod`, and `pea`. When we use `JINAD_CONTEXT=pod`, it will set jinad to create Pods.

> env `JINAD_PORT` is used to set a port on which Uvicorn runs (default: 8000)

-->




