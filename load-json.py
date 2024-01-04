# This is the file that will load the database from a json file!
# To be worked on!

import pymongo
import json

if __name__ == "__main__":
    jsonFile = input("What is the name of the json file? ")+".json" # because it needs to have .json at the end?
    print("The json file is called: ", jsonFile)
    portNum = input("What is the port number of the server? ")
    batchSize = 10000
    
    port = "mongodb://localhost:" + portNum
    
    # Connect to the server
    client = pymongo.MongoClient(port)
    print("Connected to the database at port: ", portNum)
    
    # Connect to the 291db database
    db = client["291db"]
    
    # Check to see if the tweets collection exists
    collist = db.list_collection_names()
    if "tweets" in collist:
        # drop tweets
        tweetsCollection = db["tweets"]
        tweetsCollection.drop()
        print("Collection Dropped")
    
    # Creates object to allow access to the tweets collection
    tweetsCollection = db["tweets"]
    
    tweetsCollection.delete_many({}) # Similar to dropping table, still need to drop table though
    
    # OPEN THE JSON FILE
    with open(jsonFile, 'r') as f:
        data = f.read()
    
    # Remove trailing newline
    data = data.rstrip('\n')
    
    data = f'[{data}]' # add square brackets
    
    data = data.replace('\n', ',') # add commas
    
    
    print("Starting the json.loads part")
    data = json.loads(data) # now turn it back into a json file
    
    print("Starting adding the tweets")
    
    # Using list slicing, adds the objects in the json file in batches of size batchSize
    for i in range(0, len(data), batchSize):
        currentBatch = data[i: i + batchSize]
        tweetsCollection.insert_many(currentBatch)
    
    print("Successfully added the json file contents to the database")
    
    print("Processed this many tweets: ", len(data))
    
    print("Commencing indexing")
    
    tweetsCollection.create_index("retweetCount")
    tweetsCollection.create_index("likeCount")
    tweetsCollection.create_index("quoteCount")
    
    print("Indexes for retweetCount, likeCount, and quoteCount created")
    
    tweetsCollection.create_index("user.displayname")
    tweetsCollection.create_index("user.location")
    
    print("Indexes for displayname and location created")
    
    tweetsCollection.create_index("content")
    tweetsCollection.create_index("user.followersCount")

    print("Indeces for content and followersCount created")
    
    client.close()
