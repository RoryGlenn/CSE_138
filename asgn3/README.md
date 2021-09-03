**Team Contributions**: Rory Glenn, Seth Tonningsen, Timothy Chandler
  
We all worked on this project togther using a Visual Studio Live Share session. 
The Vidual Studio Live Share session is an extention that allows all students to work on a single file simultaniously.
Everyone below acknowlages that everyone put in a equal amount of work.

Rory Glenn:  

    list_to_string() - A function that converts a the vector clock list to a string

    reset_vector_clock() - Sets the vector clock to all Zeros, depending on the number of live replicas

    vector_clock_init() - initialize the vector clock

    get_current_socket_index() - gets the index of the current replica according to where it is in the view list

    partially helped with send_broadcast() - broadcast info to other replicas


Seth Tonningsen:
  
    set_vector_clock() - sets new vector clock

    check_valid_clock() - sees if two vector clocks are valid

    vector_clock_init() - creates a vector clock of all 0's based on the view

    get_current_socket_index() - gets the index of the current replica 

    init_server() - A way for a new/outdated server to become current by requesting data from other replicas.

    get_causal_data() - Get causal data from a specific server

    broadcast() - Updates the KVS and vector clock when being broadcasted too

    Parts of /key-value-store/ and /key-value-store-view/ 


Timothy Chandler: 

    init_server() - A way for a new/outdated server to become current by requesting data from other replicas.

    remove_from_view(ip) - When a server is detected to being offline/disconnected, the server detecting will tell other servers to remove the specific IP from the view.

    add_to_view(ip) - A way to tell other server to add a specific IP to the view. 

    get_causal_date() - Get causal data from a specific server

    get_all_data() - This allows R1 to demand R2 to update its database/vector clock.


**Acknowledgments:**
Going to TA sessions helped. 
These are the TAs that helped:
Abhay Pande: consulted Abhay about the docker port numbers and how they are used in accordance with our project

**Citations**:          
Learning how to Convert Json to Python.
We needed this whenever we wanted to pasrse JSON request from one replica 
to something python readable. Since JSON and dictionaries play a big part
in this assignment, this guide helped a lot.
https://www.w3schools.com/python/python_json.asp

Distributed System Notes
We learned the check vector clock algorithm in class through laport diagrams. These notes had the exact same algorithm we learned and was written down very nicely. Therefore, when writing the algorithm in code we checked this to make sure our logic was correct. Also provides a easy to read description of the logic that we implemented when checking two vector clocks.
https://github.com/ChrisWhealy/DistributedSystemNotes/blob/master/Lecture%207.md

