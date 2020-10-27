import requests
from fastapi import status
from jina.helper import colored
from jina.peapods.pea import BasePea

from helper import namespace_to_dict


class PodAPI:
    def __init__(self, 
                 host: str,
                 port: int,
                 logger):
        self.logger = logger
        self.base_url = f'http://{host}:{port}/v1'
        self.alive_url = f'{self.base_url}/alive'
        self.pod_url = f'{self.base_url}/pod'
        self.log_url = f'{self.base_url}/log'
    
    def is_alive(self):
        try:
            r = requests.get(url=self.alive_url)
            if r.status_code == status.HTTP_200_OK:
                return True
            return False
        except requests.exceptions.ConnectionError:
            return False
    
    def create(self, pea_args: dict):
        try:
            r = requests.put(url=self.pod_url, 
                             json=pea_args)
            if r.status_code == status.HTTP_200_OK:
                return r.json()['pod_id']
            return False
        except requests.exceptions.ConnectionError:
            return False
    
    def log(self, pod_id):
        try:
            r = requests.get(url=f'{self.log_url}/?pod_id={pod_id}', 
                             stream=True)
            for log_line in r.iter_content():
                if log_line:
                    self.logger.info(f'from remote: {log_line}')

        except requests.exceptions.ConnectionError:
            return False
    
    def delete(self, pod_id):
        try:
            r = requests.delete(url=f'{self.pod_url}/?pod_id={pod_id}')
            if r.status_code == status.HTTP_200_OK:
                return True
            return False
        except requests.exceptions.ConnectionError:
            return False


class RemoteMutablePod(BasePea):
    """REST based Mutable pod to be used while invoking remote Pod via Flow API

    """
    def configure_pod_api(self):
        try:
            self.pod_host, self.pod_port = self.args['peas'][0].host, self.args['peas'][0].port_expose
            self.logger.info(f'got host {self.pod_host} and port {self.pod_port} for remote jinad pod')
        except (KeyError, AttributeError):
            self.logger.error('unable to fetch host & port of remote pod\'s REST interface')
            self.is_shutdown.set()
        
        self.pod_api = PodAPI(logger=self.logger, 
                              host=self.pod_host, 
                              port=self.pod_port)

    def loop_body(self):
        self.configure_pod_api()
        if self.pod_api.is_alive():
            self.logger.success('connected to the remote pod via jinad')
            
            pea_args = namespace_to_dict(self.args)
            self.pod_id = self.pod_api.create(pea_args=pea_args)
            if self.pod_id:
                self.logger.success(f'created remote pod with id {colored(self.pod_id, "cyan")}')
                self.set_ready()
                
                self.pod_api.log(pod_id=self.pod_id)
            else:
                self.logger.error('remote pod creation failed')
        else:
            self.logger.error('couldn\'t connect to the remote jinad')
            self.is_shutdown.set()
    
    def close(self):
        if self.pod_api.is_alive():
            status = self.pod_api.delete(pod_id=self.pod_id)
            if status:
                self.logger.success(f'successfully closed pod with id {colored(self.pod_id, "cyan")}')
            else:
                self.logger.error('remote pod close failed')
        else:
            self.logger.error('remote jinad pod is not active')
