# This is the file that will contain all of the code! 

# Here's a rough outline of the things I (Xavier) think will be needed.
# Please change anything in your assigned task(s) (variable names, function names, values passed in through call site, etc...) as you see fit

import pymongo
from pymongo import MongoClient
from datetime import datetime
import re

db = None # The database in mongodb
tweets = None # The tweets collection in mongodb

def help():
    # Prints the how to use each command in main menu
    print("Type '1' to search for a tweet")
    print("Type '2' to search for a user")
    print("Type '3' to see top users")
    print("Type '4' to see the top tweets")
    print("Type '5' to compose a tweet")
    print("Type '6' to exit the system")
    print("Type '0' to see this list of commands again :)")
    return
    

def mainMenu():
    # From here, all the tasks can be called
    global db, tweets
    
    help()
    while True:
        command = input("What is your command? (Type 0 to see list of commands) ").strip()
        if command == '1': # Search for a tweet!
            tweetSearch()
        elif command == '2': # Search for a user!
            term = input("Enter the single term you would like to search for in users: ")
            userSearch(term)
        elif command == '3': # Find the top tweets
            n = int(input("Enter the number of top users you would like to see (the top n users): "))
            topUsers(n)
        elif command == '4': # Find the top users
            print("The available ways to rank tweets are: retweet count, like count, quote count")
            category = int(input("Type '1' for retweet count, '2' for like count, or '3' for quote count: "))
            n = int(input("Enter the number of top tweets you would like to see (the top n tweets): "))
            topTweets(category, n)
        elif command == '5': # Write a tweet
            print("What is the text of the tweet you would like to tweet?")
            text = input()
            composeTweet(text)
        elif command == '6': # Exit the program
            print("Exiting system.")
            exit(1)
        elif command == '0': # Print the list of commands
            help()
        else:
            print("Invalid command. Type '0' to see the list of commands.")
    return

def tweetSearch():
    # Given a string of keywords, find tweets with matching words
    global db, tweets
    
    while True:
        # Searches for Matching Tweets
        terms = input("Enter the term(s) you would like to search for in tweets (or enter 'exit' to go back to main menu): ").strip()
        if terms.lower() == 'exit':
            break
        terms = terms.split()
        
        regex_patterns = [rf"\b{(term)}\b" for term in terms]# create a regular expression pattern for each keyword
        combined_pattern = {"$regex": ".*" + ".*".join(regex_patterns) + ".*", "$options": "i"} # combine patterns with AND semantics (also case insensitive)
        matching_tweets = db.tweets.find({"content": combined_pattern}) # search for tweets with matching terms
        matching_tweets_list = list(matching_tweets) # convert matching tweets into a list (needed for selecting a tweet)
        
        # Displays Matching Tweets
        found_tweets = False
        i = 1
        for tweet in matching_tweets_list:
            found_tweets = True
            print("Tweet #",i)
            print(f"ID: {tweet['_id']}")
            username = tweet.get("user", {}).get("username")
            print("Username:", username)
            print(f"Date: {tweet['date']}")
            print(f"Content: {tweet['content']}")
            print("-------------------------------")
            
            i = i+1

        if not found_tweets:
            print("No matching tweets found.")
            continue
        
        # Asks User to Select a Tweet and Displays All Fields   
        while True: 
            command = input("Type in a tweet number to see more info (or enter 'back' to search for tweets again): ").strip()
            
            n = len(matching_tweets_list)
            if command == 'back': 
                break
            try:
                command = int(command)
            except ValueError:
                print("Invalid input, try again")
                continue

            if command > n or command < 1:
                    print("Invalid number, try again")
                
            else:
                print("Tweet #",command," info:")
                selected = matching_tweets_list[command-1] 
                ID = selected["_id"] 
                allFields = tweets.find({"_id":ID})
                for tweet in allFields:
                    print(tweet)
                continue 
    return

def userSearch(term):
    # Given a term, search for users with displaynames or locations that match
    global db, tweets

    if not term.strip():
        print("No search term provided. Exiting to the main menu.")
    
    else:

        # Create a regex pattern with word boundaries for the search term
        regex_pattern = r"\b" + re.escape(term) + r"\b"

        # Users matching the keyword in displayname OR location
        distinct_users = db.tweets.aggregate([
            {
                "$match": {
                    "$or": [
                        {"user.displayname": {"$regex": regex_pattern, "$options": "i"}},
                        {"user.location": {"$regex": regex_pattern, "$options": "i"}}
                    ]
                }
            },
            {
                "$group": {
                    "_id": "$user.username",  # Group by username
                    "displayname": {"$first": "$user.displayname"},
                    "location": {"$first": "$user.location"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "username": "$_id",  # Rename _id field to username
                    "displayname": 1,
                    "location": 1
                }
            }
        ])

        # Convert the CommandCursor to a list
        distinct_users_list = list(distinct_users)

        # Check if there are any matches
        if len(distinct_users_list) == 0:
            print("No matches found. Exiting to the main menu.")
        
        else:

            # Print the unique users' information
            for user in distinct_users_list:
                print(f"Username: {user['username']},\n Displayname: {user['displayname']},\n Location: {user['location']}\n")
            
            user_input = input("Would you like to see more information about a user? (y/n) ")

            if user_input.lower() == 'y':
                
                user_info = input("Which user would you like to see more information about? Enter their username: ")

                # Search for the username in the collection
                user = tweets.find_one({"user.username": user_info})

                if user:
                    userInfo(user_info)

                else:
                    print(f"Username '{user_info}' does not exist in the database.")
                    print("Going back to the main menu.")

            elif user_input.lower() == 'n':
                print("Going back to the main menu.")

            else:
                print("Invalid input. Going back to the main menu.")
            
# Given a username, find all the information about the user
def userInfo(username_input):

    global db, tweets

    print("Full information for the selected user:")

    # Find the user with the specified username and maximum followersCount
    search = [
        {
            "$match": {
                "user.username": username_input
            }
        },
        {
            "$group": {
                "_id": "$user.username",
                "maxFollowersCount": { "$max": "$user.followersCount" },
                "userRecord": { "$push": "$$ROOT" }
            }
        },
        {
            "$project": {
                "_id": 0,
                "userRecord": {
                    "$filter": {
                        "input": "$userRecord",
                        "as": "record",
                        "cond": { "$eq": ["$$record.user.followersCount", "$maxFollowersCount"] }
                    }
                },
                "maxFollowersCount": 1
            }
        }
    ]

    result = db.tweets.aggregate(search)

    for document in result:
        print(document)


def topTweets(count, n):
    # Given n, and the basis for the ranking (retweets, likes or quotes), display the top n tweets
    global db, tweets
    if count == 1:
        count = "retweetCount"
    elif count == 2:
        count = "likeCount"
    elif count == 3:
        count = "quoteCount"
    else:
        print("Invalid input for count of tweet. \n Returning to main menu.")
        return
    
    
    top = tweets.find({}, {"date":1, "content":1, "id":1, "user.username": 1} ).sort(count, -1).limit(n)
    
    savedTop = list(top)
    
    i = 1
    for tweet in savedTop:
        print(i, ":", tweet)
        
        i = i+1
    
    # Allow the user to select a tweet to see all fields
    while True:
        command = input("Type the number next to a tweet to see more info. Type 'exit' to return to main menu. ").strip()
        #FIXME Need to find what the index of tweets is, so that I can do a query finding the tweet where id = someID
        if command == 'exit':
            print("returning to main menu")
            break
        
        try:
            command = int(command)
        except ValueError:
            print("Invalid input, try again")
            continue

        if command > n or command < 1:
            print("Invalid number, try again")
        
        else:
            selected = savedTop[command-1]
            ID = selected["id"]
            allFields = tweets.find({"id":ID})
            for tweet in allFields:
                print(tweet)
            
    return


def topUsers(n):
    # Define a MongoDB aggregation pipeline to find top users based on followers count
    global db, tweets
    pipeline = [
        {
            "$group": {
                "_id": "$user.username",
                "displayname": {"$first": "$user.displayname"},
                "followersCount": {"$first": "$user.followersCount"}
            }
        },
        {
            "$sort": {"followersCount": pymongo.DESCENDING}
        },
        {
            "$limit": n
        }
    ]
    # Execute the pipeline and store the distinct users in a list
    distinct_users = list(db.tweets.aggregate(pipeline))

    for user in distinct_users:
        print(user)
    while True:
        # Prompt user for input
        selected_username = input("Enter the username to see full information (or type 'exit' to go back to the main menu): ").strip()
        if selected_username.lower() == 'exit':
            print("returning to main menu")
            break
        usernames = [user['_id'] for user in distinct_users]

        if selected_username in usernames:
            # Find the user information from the distinct_users list
            selected_user = next((user for user in distinct_users if user['_id'] == selected_username), None)

            print(f"Full information for {selected_username}:")
            user_info = db.tweets.aggregate([{"$match": {"user.username": selected_username}}, {"$project": {"user": 1, "_id": 0}}])
            for user in user_info:
                print(user)
        else:
            print(f"No information found for {selected_username}")
    return


def composeTweet(content):
    global db, tweets # NOW DB IS THE GLOBAL VARIABLE
    
    #FIXME Might have to manually set all other fields to NULL (ie. "tweetURL": None, etc...)
    current_utc_time = datetime.utcnow()
    
    # Format the date and time as a string in the desired format
    formatted_date = current_utc_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    
    tweet = {
        
        
        
        "url": None,
        "date": formatted_date,
        "content": content,
        "renderedContent": None,
        "id": None,
        "user":{
            "username": "291user",
            "displayname": None,
            "id": None,
            "description": None,
            "rawDescription": None,
            "descriptionUrls": None,
            "verified": None,
            "created": None,
            "followersCount": None,
            "friendsCount": None,
            "statusesCount": None,
            "favouritesCount": None,
            "listedCount": None,
            "mediaCount": None,
            "location": None,
            "protected": None,
            "linkUrl": None,
            "linkTcourl": None,
            "profileImageUrl": None,
            "profileBannerUrl": None,
            "url": None,
        },
        "outlinks": None,
        "replyCount": None,
        "retweetCount": None,
        "likeCount": None,
        "consersationId": None,
        "lang": None,
        "source": None,
        "sourceUrl": None,
        "sourceLabel": None,
        "media": None,
        "retweetedTweet": None,
        "quotedTweet": None,
        "mentionedUsers": None
    }
    result = db.tweets.insert_one(tweet)
    print(f"Tweet with id {result.inserted_id} has been inserted.")
    return

def main():
    # Connects to the mongodb database, and then moves to main menu
    port = int(input("What is the port number of the server? "))
    client = MongoClient('mongodb://localhost:'+str(port))
    print("Successfully connected to mongodb")
    global db, tweets
    db = client['291db']
    tweets = db['tweets']
    print("Entering the Main Menu")
    mainMenu()
    client.close()
    return

if __name__ == "__main__":
    main()
    
