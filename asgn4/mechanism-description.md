```
Description of causal dependency tracking mechanism:

	We implemented causal dependency through the use of vector clocks and using the primary backup model. 
	For Key-Value-Store(KVS) we use a global python dictionary and use global lists for vector clocks, views and URL's for broadcasting. 
	Each replica contains a list of positive integers that correspond to the position of IP addresses in the view. 
	For example, the IPs 10.10.0.2:8085, 10.10.0.3:8085, 10.10.0.4:8085 relates to [0,0,0] directly. 
	Each time a put or delete request is called (not a get request), we increment the position of that replica by one in its vector clock. 
	Then we broadcast the request and its vector clock to the other replicas in its view. Each broadcasted replica will check the incoming vector clock. 
	If the vector clock is valid then you proceed to update the replicas vector clock and data. 
	This algorithm to check if a vector clock is valid with your own was discussed in class( Algorithm link can be found in README). 
	Else, we know that this request should not be served immedately. Therefore, the replica being broadcast too was disconnected from the server at some point in time. 
	Now this broadcasted replica requests data from another replica. Once done it can then satisfy the request and makes sure the vector clock is up to date. 
	Therefore keeping causul consisticy when having a reason to broadcast to all replicas in the view.


Description of replica failure detection mechanism:

	Our replica failure detection is fairly robust.
	Upon starting any replica, we want to initialize it. 
	This means, we check other known replicas for their data. 
	For example, if R1 and R2 have the key-value x=1, with a vector clock of [1,0], a newly started replica R3 will first tell R1 and R2 to expand the vector clock to [1,0,0], and then it will ask a Replica (R1 for example) to share its current vector clock(now [1,0,0]), and all key-value data. 
	Once this process is complete, R3 will have the vector clock of [1,0,0] and key-value store of x=1.
	In a different case, if a Replica recieves a request with an higher vector clock than expected, then we know a replica failure may have occured. 
	The replica with the failure will request the data from a replica with the correct vector clock.
	Once all data is recieved and the replica is up to date, then the replica will process whatever request. 
	Since we don't know how badly the failure is, we we use the init_server() from the README to copy data from the known good replicas.
	Furthermore, we maintain a list of all disconnected/dead servers, and ping such servers to check if they have come back online. 
	If a server returns a response, we know the server is up. This will initiate the previously dead/disconnected server to re-initialize to get all current data.
	The list of dead/disconnected servers is then updated. This midigates false positives.
	However, if detect a server to be down when we believed it to be up, then we remove that server from a replicas "alive" view list, and then we update it in the "dead" list. 
	Of course this alive/dead list is then sent to other replicas so all replicas have the same alive/dead list. This midigates false negatives.



Description of sharding mechanism:

    Sharding requires us to maintain an overhead on each node. Each node maintains a dictionary of all shard metadata called shard_info.
    shard_info looks like: {"shard1" : ["10.0.0.1", "10.0.0.2"],"shard2" : ["10.0.0.3", "10.0.0.4"]}
    If any node is removed or added to a shard, the shard_info of ALL nodes are adjusted. 
    This shard metadata is used to redirect key-value pairs to the correct shard. It does this using the below hashing method.

    Hashing - Takes the binary representation of a string and converts it into a number. 
            That number is then moduloed by the length of shards + 1. (to get "shard1", "shard2", ect...)
            The final result tells us which shard to shore the key in.
            This hash function is adjusted based on the number of shards.
            If resharding occures, the hash function adjusts appropratly.

    There are 2 cases when a node recieves a request from the client. 
    Case 1: The given key belongs in the shard in which it was recieved.
    Case 2: The given key does NOT belong in the shard in which it was recieves, and must be routed to the correct shard.
    Case 1 is trivial - we just process the request normally and finish.
    Case 2 runs the key through our hash table, and redirects the request to any node from the shard it belongs.
    Once the message is redirected to the correct node, Case 1 will apply, and the request will finish.


    Resharding -
        1. This process is started by a PUT request being sent to endpoint /key-value-store-shard/reshard at a node in the store.
        2. If we can give every shard at least two nodes, then the request is considered valid and the function continues.
        3. We rehash the key-value pairs in order to evenly distribute them accross all shards.
            During this process, our old data sets holding our key-value pairs, node lists, and vector clock, is reset.
            A new data set is created containing all of our key-value pairs.

        When do we want to call reshard?
            1. If a shard is instantiated with two nodes and one of the nodes goes offline, the shard is no longer fault-tolerant.
                In this case a reshard should be called in order to make the shard fault tolerant again by adding another node to it.
            2. We could also add new nodes to the shard in order to increase its capacity or throughput.

```


