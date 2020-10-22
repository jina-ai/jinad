import copy
from typing import Union, Tuple, List
from jina.flow import Flow as _Flow
from jina import __default_host__
from jina.peapods.pod import FlowPod as _FlowPod
from jina.peapods.pea import BasePea
from jina.excepts import FlowTopologyError


class Flow(_Flow):
    def add(self,
            needs: Union[str, Tuple[str], List[str]] = None,
            copy_flow: bool = True,
            **kwargs) -> 'Flow':
        """
        Add a pod to the current flow object and return the new modified flow object.
        The attribute of the pod can be later changed with :py:meth:`set` or deleted with :py:meth:`remove`

        Note there are shortcut versions of this method.
        Recommend to use :py:meth:`add_encoder`, :py:meth:`add_preprocessor`,
        :py:meth:`add_router`, :py:meth:`add_indexer` whenever possible.

        :param needs: the name of the pod(s) that this pod receives data from.
                           One can also use 'pod.Gateway' to indicate the connection with the gateway.
        :param copy_flow: when set to true, then always copy the current flow and do the modification on top of it then return, otherwise, do in-line modification
        :param kwargs: other keyword-value arguments that the pod CLI supports
        :return: a (new) flow object with modification
        """

        op_flow = copy.deepcopy(self) if copy_flow else self

        pod_name = kwargs.get('name', None)

        if pod_name in op_flow._pod_nodes:
            raise FlowTopologyError(f'name: {pod_name} is used in this Flow already!')

        if not pod_name:
            pod_name = '%s%d' % ('pod', op_flow._pod_name_counter)
            op_flow._pod_name_counter += 1

        if not pod_name.isidentifier():
            # hyphen - can not be used in the name
            raise ValueError(f'name: {pod_name} is invalid, please follow the python variable name conventions')

        needs = op_flow._parse_endpoints(op_flow, pod_name, needs, connect_to_last_pod=True)

        kwargs.update(op_flow._common_kwargs)
        kwargs['name'] = pod_name
        op_flow._pod_nodes[pod_name] = FlowPod(kwargs=kwargs, needs=needs)
        op_flow.set_last_pod(pod_name, False)

        return op_flow


class FlowPod(_FlowPod):
    
    def start(self) -> 'FlowPod':
        if self._args.host == __default_host__:
            return super().start()
        else:
            from remote import RESTRemoteMutablePod
            _remote_pod = RESTRemoteMutablePod(self.peas_args)
            self.enter_context(_remote_pod)
            self.start_sentinels()
            return self
