'''
All nodes currently in Chameleon will be fetched. 
Different types of processors, network interfaces, storage devices, and chassis will be listed,
along with the number of times appear in the system. 

@author: zhuo zhen
'''

import requests
import sys
from collections import defaultdict

# Processor class
class Processor:

    def __init__(self, processor):
        self.vendor = processor["vendor"]
        self.model = processor["model"]
        self.version = ""
        if "version" in processor:
            self.version = processor["version"]
        self.key = (self.vendor, self.model, self.version)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

# Network class
class Network:

    def __init__(self, network):
        self.vendor = network["vendor"]
        self.model = network["model"]
        self.key = (self.vendor, self.model)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

# Storage class
class Storage:

    def __init__(self, storage):
        self.vendor = storage["vendor"]
        self.model = storage["model"]
        self.key = (self.vendor, self.model)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

# Chassis class
class Chassis:

    def __init__(self, chassis):
        self.name = chassis["name"]

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

# Global variables
ROOT_URL = "https://api.chameleoncloud.org"
HIERARCHY = ["root", "sites", "clusters", "nodes"]

processor_dict = defaultdict(int)
network_dict = defaultdict(int)
storage_dict = defaultdict(int)
chassis_dict = defaultdict(int)

# Functions
def has_children(rel):
    ind = HIERARCHY.index(rel)
    return ind < len(HIERARCHY) - 1  

def get_children_rel(rel):
    # not checking index out of bound here, 
    # because has_children function will always be called before this function
    return HIERARCHY[HIERARCHY.index(rel) + 1]

def get_children_url(rel, item):
    # not checking index out of bound here,
    # because has_children function will always be called before this function
    children_rel = HIERARCHY[HIERARCHY.index(rel) + 1]
    children = next(i for i in item["links"] if i["rel"] == children_rel)
    childern_url = ROOT_URL + children["href"]
    return childern_url

def send_request(url):
    resp = requests.get(url)
    if resp.status_code == requests.codes.ok:
        return resp.json()
    else:
        sys.exit("Sending request to %s failed! STATUS CODE: %s" % (url, resp.status_code))

# Main method
if __name__ == '__main__':
    if len(HIERARCHY) <= 0:
        sys.exit()
    root = HIERARCHY[0]
    current_url = {"level": root, "url": ROOT_URL}
    url_queue = []
    # if level of current_url is not node, append children urls to queue
    # and pop first element in queue as current_url
    # iterate until all urls in queue are node urls
    while has_children(current_url["level"]):
        resp = send_request(current_url["url"])
        iterable_resp = []
        if "items" in resp:
            iterable_resp = resp["items"]
        else:
            iterable_resp = [resp]

        for item in iterable_resp:
            url_queue.append({"level": get_children_rel(current_url["level"]), "url": get_children_url(current_url["level"], item)})

        if len(url_queue) == 0:
            break
        current_url = url_queue.pop(0)

    # put back the first node url
    if not has_children(current_url["level"]):
        url_queue.append(current_url)

    # get all nodes
    for nodes_url in url_queue:
        resp = send_request(nodes_url["url"])
        nodes = resp["items"]
        for node in nodes:
            # parsing processor
            processor = Processor(node["processor"])
            processor_dict[processor] += 1

            # parsing network
            for node_network in node["network_adapters"]:
                network = Network(node_network)
                network_dict[network] += 1

            # parsing storage
            for node_storage in node["storage_devices"]:
                storage = Storage(node_storage)
                storage_dict[storage] += 1

            # parsing chassis
            chassis = Chassis(node["chassis"])
            chassis_dict[chassis] += 1

    # print processor
    print("****** PROCESSORS ******")
    for processor in sorted(processor_dict, key = processor_dict.get, reverse = True):
        print("vendor: %s   model: %s   version: %s   count: %s" % (processor.vendor, processor.model, processor.version, processor_dict[processor]))

    # print network adaptersr
    print("****** NETWORK ADAPTERS ******")
    for network in sorted(network_dict, key = network_dict.get, reverse = True):
        print("vendor: %s   model: %s   count: %s" % (network.vendor, network.model, network_dict[network]))

    # print storage devices
    print("****** STORAGE DEVICES ******")
    for storage in sorted(storage_dict, key = storage_dict.get, reverse = True):
        print("vendor: %s   model: %s   count: %s" % (storage.vendor, storage.model, storage_dict[storage]))

    # print chassis
    print("****** CHASSIS ******")
    for chassis in sorted(chassis_dict, key = chassis_dict.get, reverse = True):
        print("name: %s   count: %s" % (chassis.name, chassis_dict[chassis]))  


