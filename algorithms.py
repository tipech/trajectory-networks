"""Execute node importance algorithms on trajectory networks.

Provides algorithm classes for calculation of node importance in trajectory
networks, either naively or iwth the SLOT algorithm. Moreover, this can be
executed as a script to actually generate the data.

Notes:
 - the terms "point", "node" and "object" are used interchangeably here
 - a network "snapshot" is the form of the dynamic, evolving network,
    in a single moment in time (a freeze-frame snapshot)
 

"""

import argparse, os, math, json
import networkx as nx
from datetime import datetime
from pprint import pprint


def main():
    """Run the algorithm with command-line parameters."""


    # parser for command line arguments
    parser = argparse.ArgumentParser(
        description="Generate the trajectory network of moving objects.")

    # algorithm type argument: naive or SLOT
    parser.add_argument("type", choices=["naive", "slot"],
        help="type of algorithm")

    # input data file argument
    parser.add_argument("file", help="trajectory data file")

    # optional arguments: print/store results
    parser.add_argument("-p", "--print", action="store_true",
        help="print results to console")
    parser.add_argument("-s", "--store", action="store_true",
        help="store data to file")

    # metric selection arguments
    parser.add_argument("-d", "--degree", action="store_true",
        help="calculate node degree")
    parser.add_argument("-t", "--triangles", action="store_true",
        help="calculate duration of triangles")
    parser.add_argument("-tm", "--membership", action="store_true",
        help="calculate node triangle membership")
    parser.add_argument("-c", "--components", action="store_true",
        help="calculate duration of components")
    parser.add_argument("-cd", "--connectedness", action="store_true",
        help="calculate node connectedness")
    
    args = parser.parse_args() # parse the arguments

    metrics = { "degree":args.degree, 
                "triangles":args.triangles, 
                "membership":args.membership, 
                "components":args.components, 
                "connectedness":args.connectedness}

    # read file
    try:
        with open(args.file, "r") as input_file:
            
            # parse the json data
            data = json.load(input_file)

            # depending on type, run the appropriate algorithm
            if args.type == "naive":
                algorithm = NaiveNodeImportance(data, metrics)

            elif args.type == "slot":
                algorithm = SLOTNodeImportance(data, metrics)


    except IOError as e:
        parser.error("Problem occured during file reading: \n\t%s" % e)


    if args.print:  # print results
        print(algorithm)
        
    # if args.store:
    #     algorithm.export_data(args.naive)



class NodeImportance():
    """Handle common functions for node importance algorithm"""

    def __init__(self, data, metrics):
        """Perform algorithm initialization actions"""

        self.data = data
        self.metrics = metrics


        self.history = {
            'degree':{},
            'triangles':{},
            'membership': {},
            'components': {},
            'connectedness':{}}


    def set_node_metric_value(self, metric, node_id, value):
        """Store the value of a single metric on a node"""
        pass


    def store_node_metric_duration(self, metric, node_id, value):
        """Store the duration a value lasted for a single metric on a node"""

        # this is a new node
        if node_id not in self.history[metric]:
            
            # create the new node, add metric value with duration 1
            self.history[metric][node_id] = {value: 1}

        # this node existed, but never had this value before
        elif value not in self.history[metric][node_id]:   

            # add the metric value to the node with duration 1
            self.history[metric][node_id][value] = 1

        # both node and metric value existed
        else:

            # simply increment the duration of the value
            self.history[metric][node_id][value] += 1


    def store_item_metric_duration(self, item_type, item_id):
        """Store the duration of a single item (triangle or component)"""

        # this is a new item
        if item_id not in self.history[item_type]:
            
            # create the new item entry with duration 1
            self.history[item_type][item_id] = 1

        # item existed
        else:

            # increment the duration of the item
            self.history[item_type][item_id] += 1




class NaiveNodeImportance(NodeImportance):
    """Calculate node importance metrics with the naive algorithm"""

    def __init__(self, data, metrics):
        super().__init__(data, metrics)

        # iterate through the network snapshots in time 
        # pprint(data)
        for snapshot in data.values():

            # build the network
            G = nx.Graph()
            G.add_nodes_from([node['id'] for node in snapshot['nodes']])
            G.add_edges_from([(edge['from'], edge['to'])
                for edge in snapshot['edges']])

            # degree metric
            if metrics['degree']:

                # calculate degree of the current snapshot
                snapshot_degree = nx.degree(G)

                # store metric for every node
                for node in snapshot_degree:                    
                    self.store_node_metric_duration("degree", node[0],node[1])

            # triangles metric
            if metrics['triangles']:

                # calculate triangles of the current frame in time
                snapshot_triangles = self.get_all_triangles(G)

                # get id for every triangle and store its duration
                for triangle in snapshot_triangles:

                    # concat nodes for id
                    triangle_id = '_'.join(sorted(triangle))
                    self.store_item_metric_duration("triangles", triangle_id)

            # triangle membership metric
            if metrics['membership']:

                # calculate triangle counts of the current snapshot
                snapshot_triangle_counts = nx.triangles(G)

                # store metric for every node
                for node_id, triangles in snapshot_triangle_counts.items():
                    self.store_node_metric_duration("membership", node_id,
                        triangles)

            # component-related metrics
            if metrics['components'] or metrics['connectedness']:

                # calculate components of the current frame in time
                snapshot_components = nx.connected_components(G)

                if metrics['components']:                    
                    for component in snapshot_components:

                        # concat nodes for id
                        component_id = '_'.join(sorted(component))
                        self.store_item_metric_duration("components",
                            component_id)


                if metrics['connectedness']:
                    for component in snapshot_components:

                        # get the size of the component
                        size = len(component) - 1

                        # store value for every node in component
                        for node_id in component:
                            self.store_node_metric_duration("connectedness",
                                node_id, size)

        pprint(self.history)


    def get_all_triangles(self, G):
        """Returns all triangles in a network"""

        result=[]   # will hold final result
        done=set()  # will hold already examined nodes

        for node in G: 

            done.add(node)          # node examined
            neighbors_done=set()    # will hold examined neighbors of node
            neighbors=set(G[node])  # not-yet-examined neighbors of node

            # examine neigbors of node
            for neighbor in neighbors: 
                if neighbor in done:         # node already examined
                    continue
                neighbors_done.add(neighbor) # neighbor node already examined
                
                # check potential triangle of node and neighbor
                for common in neighbors.intersection(G[neighbor]):
                    if common in done or common in neighbors_done:
                        continue

                    # new triangle
                    result.append( (node,neighbor,common) ) 
        return result




class StreamingNodeImportance(NodeImportance):
    """Calculate node importance metrics using a streaming algorithm"""

    def __init__(self, data, metrics):
        super().__init__(data, metrics)

        active_nodes = []
        active_edges = []
        
        # iterate through the network snapshots in time 
        for snapshot in data.values():

            # add any nodes that just appeared to active
            for new_node in snapshot["nodes"]:
                active_nodes





class SLOTNodeImportance(NodeImportance):
    """Calculate node importance metrics using the SLOT algorithm"""

    def __init__(self, data, metrics):
        super().__init__(data, metrics)



        



if __name__ == "__main__":
    # Run the module with command-line parameters.
    main()