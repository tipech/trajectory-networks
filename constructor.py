"""Construct trajectory networks out of moving object data.

Provides a class for construction of the trajectory network. Moreover, this
can be executed as a script to actually generate the data.

Notes:
 - the terms "point", "node" and "object" are used interchangeably here
 - a network "snapshot" is the form of the dynamic, evolving network,
    in a single moment in time (a freeze-frame snapshot)

"""

import argparse, csv, os, math, json
from datetime import datetime
from pprint import pprint


def main():
    """Run the constructor with command-line parameters."""


    # parser for command line arguments
    parser = argparse.ArgumentParser(
        description="Generate the trajectory network of moving objects.")

    # input data file argument
    parser.add_argument("file", help="trajectory data file")

    # optional arguments: print/store results
    parser.add_argument("-p", "--print", action="store_true",
        help="print results to console")
    parser.add_argument("-s", "--store", action="store_true",
        help="store data to file")
    
    # extra arguments: distance threshold, export naive
    parser.add_argument("--threshold", type=float, default=50,
        help="distance threshold where objects are connected (default: 50)")
    parser.add_argument("-n", "--naive", action="store_true",
        help="also export netwrok at every timestamp for naive calculation")

    args = parser.parse_args() # parse the arguments


    # check for invalid numbers
    if args.threshold < 0:
        parser.error("Invalid threshold value.")

    # read file
    try:
        with open(args.file, "r") as input_file:
            reader = csv.reader(input_file)
            next(reader) # skip first (headers) line

            data = []

            # parse csv data into array
            for row in reader:

                # timestamp, x, y, id
                data.append((int(row[0]),float(row[1]),float(row[2]), row[3]))

            # sort if not already sorted
            data.sort(key=lambda x: x[0])

            # run the constructor
            constructor = Constructor(data, args.threshold)


    except IOError as e:
        parser.error("Problem occured during file reading: \n\t%s" % e)


    if args.print:  # print results
        print(constructor)
        
    if args.store:
        constructor.export_data(args.naive)



class Constructor():

    """Construct the trajectory network of moving object data.

    Class that handles the necessary calculations at every step to create the
    time-evolving proximity network of objects in motion.
    End results are two dictionaries:
     - node_dict: has every node, when it started and when it stopped existing
     - edge_dict: has every edge, when it started and when it stopped existing
    

    """

    def __init__(self, data, threshold, spherical = False):
        """Initialize network construction"""

        self.data = data
        self.threshold = threshold
        self.spherical = spherical

        self.node_dict = {}
        self.edge_dict = {}

        time = data[0][0]       # start iterating from first timestamp
        active_objects = []     # will hold the objects in a single timestamp
        self.time_networks = {} # will hold every snapshot of the network

        # iterate through data and construct the simple threshold proximity
        # network at every timestamp (naive)
        for row in data:

            # if we moved to next timestamp
            if row[0] != time:

                # get the proximity network of last timestamp's objects
                network = self.get_proximity_network(active_objects)
                self.update_nodes(time, active_objects)  # update nodes dict
                self.update_edges(time, network)         # update edges dict

                # store the network snapshot for naive calculation
                self.time_networks[time] = {"nodes": active_objects, 
                                            "edges": network}

                time = row[0] # remember new timestamp
                active_objects = [] # forget last timestamp's objects

            # append position, id of point in new data row
            active_objects.append({"x":row[1], "y":row[2], "id":row[3]})

        # one last time for the events of the final timestamp
        # get the proximity network of last timestamp's objects
        network = self.get_proximity_network(active_objects)
        self.update_nodes(time, active_objects)  # update nodes dict
        self.update_edges(time, network)         # update edges dict

        # store the network snapshot for naive calculation
        if len(network) > 0:    # only bother if there are edges
            self.time_networks[time] = {"nodes": active_objects,
                                        "edges": network}



    def get_proximity_network(self, nodes):
        """Get the edges of a proximity network for this instant"""
        
        edge_list = []

        # ecamine all possible node pairs
        for i in range(0, len(nodes)):
            for j in range(i+1, len(nodes)):
    
                # future support for lat/lon distance calculation            
                if not self.spherical:
                    points_distance = self.distance(nodes[i], nodes[j])

                # points within distance threshold, make edge
                if(points_distance <= self.threshold):

                    # put IDs in order (string sort)
                    id_1 = min(nodes[i]["id"], nodes[j]["id"])
                    id_2 = max(nodes[i]["id"], nodes[j]["id"])

                    edge_list.append({"from": id_1, "to": id_2,
                        "id": id_1 + "_" + id_2})

        return edge_list


    def distance(self, point_1, point_2):
        """Calculate Eucledean distance of two points"""
        
        rel_x = point_1["x"] - point_2["x"]
        rel_y = point_1["y"]- point_2["y"]
        
        return math.sqrt(math.pow(rel_x, 2) + math.pow(rel_y, 2))


    def update_nodes(self, time, nodes):
        """Add new or update duration of old node dictionary entries"""
        
        # iterate and compare this timestamp's objects with the stored ones
        for node in nodes:

            if node["id"] in self.node_dict.keys(): # already exists

                # update old end time (object didn't stop existing last time)
                self.node_dict[node["id"]]["last"] = time

            else:   # brand new object
                self.node_dict[node["id"]] = {"first":time, "last":time}


    def update_edges(self, time, edges):
        """Add new or update duration of old edge dictionary entries"""
        
        # iterate and compare this timestamp's edges with the stored ones
        for edge in edges:

            if edge["id"] in self.edge_dict.keys(): # already exists

                # update old end time (edge didn't stop existing last time)
                self.edge_dict[edge["id"]]["last"] = time

            else:   # brand new edge
                self.edge_dict[edge["id"]] = {"first":time, "last":time,
                    "from": edge["from"], "to": edge["to"]}


    def export_data(self, naive):
        """Store the saved network data as json file"""        

        # check if data storage exists and if not, create it
        if not os.path.isdir("data"):
            os.mkdir("data")

        # timestamp for filename
        file_time = datetime.now()

        # open file for storage, filename is timestamp
        filename = "data/network_events_%s.json" % (file_time)
        with open(filename,"w+") as file:

            data_dict = {"nodes": self.node_dict, "edges": self.edge_dict}

            # write pretty JSON to file
            file.write( json.dumps(data_dict, sort_keys=True,
                indent=4, separators=(',', ': ')))

        # if naive calculation requested, also export network snapshots
        if naive:

            # open file for storage, filename is timestamp
            filename2 = "data/network_naive_%s.json" % (file_time)
            with open(filename2,"w+") as file:

                # write pretty JSON to file
                file.write( json.dumps(self.time_networks, sort_keys=True,
                    indent=4, separators=(',', ': ')))

            # return both filenames
            return (filename, filename2)

        else:
            return filename


    def __repr__(self):
        """Convert to string."""

        data_dict = {"nodes": self.node_dict, "edges": self.edge_dict}

        s = json.dumps(data_dict, sort_keys=True, indent=4)
        return("Generator(objects={%s})" % s)


if __name__ == "__main__":
    # Run the module with command-line parameters.
    main()