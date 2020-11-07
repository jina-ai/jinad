# jinad

Jina Flow Management API


## Set up jinad on AWS

1. Create a new instance on AWS and log into the instance

```bash
ssh -i your.pem ubuntu@ec2-3-17-167-247.us-east-2.compute.amazonaws.com
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

5. Keep jina running with `screen`

```bash
screen
cd ../jinad/jinad
export JINAD_CONTEXT=pod
nohup python3 main.py &
```

Detach the screen session by `CTRL+a` `d`. Afterwards, you can safely close your terminal. Now we are ready to set up pods on this instance from either your local machine or another remote instance.

To verify whether jinad is properly running, one can use the following lines

```bash
export JINAD_IP=3.17.167.247
export JINAD_PORT=8000
curl -s -o /dev/null -w "%{http_code}"  http://$JINAD_IP:$JINAD_PORT/v1/alive
```

Alternatives, open `http://3.17.167.247:8000/docs` on your browser and you will see the API documentations of jinad.

**Note** that `JINAD_CONTEXT` is used to set up the jinad context. The possible values are `flow`, `pod`, and `pea`. When we use `JINAD_CONTEXT=pod`, it will set jinad to create Pods. 

## Use Case 1: Use Pods on cloud from a local flow

```python
from jina.flow import Flow
from jina.enums import PeaRoleType
f = Flow().add(uses='_pass', host='3.17.167.247', port_expose=8000, role=PeaRoleType.SINGLETON)
with f:
    f.dry_run()
```

`3.17.167.247` is the public ip of your instance. By default, jinad is listening to the port `8000` 
