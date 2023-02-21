"""
    This program listens for work messages contiously.
    It also alerts user if foodB temperature changes by less than 1 degree or more in 10 minutes.
    

    Author: Deanna Clayton
    Date: Februrary 20, 2023

"""

import pika
import sys
import csv
from collections import deque

# create deque
# limit to 5 items (the 5 most recent readings)
foodB_deque = deque(maxlen=20)

# open a file to write some data
# create a csv writer for our comma delimited data
output_file = open("FoodB.csv", "w+")
writer = csv.writer(output_file, delimiter = ",")

# define an alert function to tell us when the foodA temperature decreases less than 1 degree in 10 min
def smoker_alert(d, message):
    d.append(message)
    if len(d) == 20:
        number = d[0] - d[-1]
        if abs(number) < 1:
            print("Food Stall!")

def float_num (element):
    if element is None: 
        return element
    try:
        float(element)
        return float(element)
    except ValueError:
        return element

# define a callback function to be called when a message is received
def foodB_callback(ch, method, properties, body):
    """ Define behavior on getting a message."""

    # decode the binary message body to a string
    message = body.decode()
    message2 = str(message)[1:-1]
    message3 = message2.split(',')
    message4 = float_num(message3[1])

    # tell user message has been received
    print(f" [x] Received {message}")

    # call alert function
    if isinstance(message4, float):
        smoker_alert(foodB_deque, message4)
    
    # write the strings to the output file
    writer.writerow(message3)
    
    # when done with task, tell the user
    print(" [x] Done.")
    # acknowledge the message was received and processed 
    # (now it can be deleted from the queue)
    ch.basic_ack(delivery_tag=method.delivery_tag)


# define a main function to run the program
def main(hn: str = "localhost", qn: str = "temp3"):
    """ Continuously listen for task messages on a named queue."""

    # when a statement can go wrong, use a try-except block
    try:
        # try this code, if it works, keep going
        # create a blocking connection to the RabbitMQ server
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=hn))

    # except, if there's an error, do this
    except Exception as e:
        print()
        print("ERROR: connection to RabbitMQ server failed.")
        print(f"Verify the server is running on host={hn}.")
        print(f"The error says: {e}")
        print()
        sys.exit(1)

    try:
        # use the connection to create a communication channel
        channel = connection.channel()

        # use the channel to declare a durable queue
        # a durable queue will survive a RabbitMQ server restart
        # and help ensure messages are processed in order
        # messages will not be deleted until the consumer acknowledges
        channel.queue_declare(queue=qn, durable=True)

        # The QoS level controls the # of messages
        # that can be in-flight (unacknowledged by the consumer)
        # at any given time.
        # Set the prefetch count to one to limit the number of messages
        # being consumed and processed concurrently.
        # This helps prevent a worker from becoming overwhelmed
        # and improve the overall system performance. 
        # prefetch_count = Per consumer limit of unaknowledged messages      
        channel.basic_qos(prefetch_count=1) 

        # configure the channel to listen on a specific queue,  
        # use the callback function named callback,
        # and do not auto-acknowledge the message (let the callback handle it)
        channel.basic_consume( queue=qn, on_message_callback=foodB_callback)

        # print a message to the console for the user
        print(" [*] Ready for work. To exit press CTRL+C")

        # start consuming messages via the communication channel
        channel.start_consuming()

    # except, in the event of an error OR user stops the process, do this
    except Exception as e:
        print()
        print("ERROR: something went wrong.")
        print(f"The error says: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print(" User interrupted continuous listening process.")
        sys.exit(0)
    finally:
        print("\nClosing connection. Goodbye.\n")
        connection.close()


# Standard Python idiom to indicate main program entry point
# This allows us to import this module and use its functions
# without executing the code below.
# If this is the program being run, then execute the code below
if __name__ == "__main__":
    # call the main function with the information needed
    main("localhost", "temp3")
