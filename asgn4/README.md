**Assignment: Sharded, Fault-tolerant Key-value store**

**Team Contributions**: Rory Glenn, Seth Tonningsen, Timothy Chandler

We all worked on this project togther using a Visual Studio Live Share session.
The Visual Studio Live Share session is an extention that allows all students to work on a single file simultaniously.
Everyone below acknowlages that everyone put in a equal amount of work.

Rory Glenn: 
	reshard()          - Reshard to change the shardcount of a system,
        get_myshard_info() - Returns the shard name holding the node that we are currently in,
        fixed global variable errors,
	linted code.

Seth Tonningsen:

	Shard commands():
	key-value-store-shard/shard-ids
	  It gets the ids of of the shards that are available
	key-value-store-shard/node-shard-id
	  It gets the shardID of the replica that is called
	key-value-store-shard/shard-id-members(shard_id)
	  Gets all the replicas IPs from the given shardID
	key-value-store-shard/shard-id-key-count(shard_id)
	  Counts the number of keys in the given shardID
	shard-keys
	  Returns the number of keys in a replica
	key-value-store-shard/add-member(shard_id)
	  Lets the client add a running replica to a shard

	Reshard():
	key-value-store-shard/reshard
	  Lets the client to be able to reshard the replicas
	set-shard-info 
	  A helper function for reshard, resets all the replicas info when resharding

	System():
	add_node_to_global_view(ip) 
	  Adds a replica IP to the global view
	init_server()
	  Sets up some of the data when a replica is started
	new_node_init(shard_id) 
	  When a new replica is added to the subnet(not at the start) it sets up some of the data

Timothy Chandler:
	get_all_data_self()                               - GET function that returns entire servers key-value store
	remove_ip_from_shard_info(ip)                     - DELETE fucntion that removes an IP from a servers shard metadata.
	get_shard_members_data(shard_id)                  - returns a list of IPs in a specific shard
	add_ip_to_shard_info(shard_id, ip)                - PUT function to add an IP to a specific shard. Used to update shard metadata on each server.
	reshard()                                         - Reshard to change the shardcount of a system.
	set_shard_info_broadcaster(shard_info)            - Broadcast to all nodes to update shard metadata.
	set_shard_info_reciever()                         - PUT function to change nodes shard metadata
	in_correct_shard(key)                             - find if a given key is in the current correct node/shard.
	route_to_shard(key, message_method, message_json) - takes key and request data, and routes request to a node in the correct shard.
	retrieve_all_system_data()                        - GET function that returns ALL system data in a heirarchy order. Used for debugging purposes.
	retrieve_all_system_data_kv()                     - Obtain ALL system key-value data for resharding purposes.
	new_node_init(shard_id)                           - Initialize a new node to a specific shard.
	route_hashing(key)                                - Takes a key and returns the shard the key belongs to. Uses a custom hashing function to accomplish this task.


**Acknowledgments:**
	None

**Citations**:

Distributed System Notes
