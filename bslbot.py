#!/usr/bin/env python

import tweepy
import time
import sys
import os
import random
from configobj import ConfigObj

config = ConfigObj(os.path.expanduser('~/.bslbot'), unrepr=True)

auth = tweepy.OAuthHandler(config['authentication']['consumer_key'], config['authentication']['consumer_secret'])
auth.set_access_token(config['authentication']['access_key'], config['authentication']['access_secret'])
api = tweepy.API(auth)

def printOrTweet(x):
    """Simple function that currently prints, but will tweet."""
    global config

    print "You have entered the printOrTweet zone."
    if config['misc']['printortweet'] == 'print':
        print x
    elif config['misc']['printortweet'] == 'tweet':
        api.update_status(x)
    else:
        print "I don't know whether to tweet or print."

def tweetRandomWord():
    # TODO sort it so that 'Random' actually means 'random selection from tweets that haven't been tweeted yet'
    import random
    """This function tweets a pseudo random word in BSL."""
    # Dictionary of all words we can possibly tweet about
    all_words = config['Tweets']['Words'] 

    # Choose one of the words
    word = all_words[random.choice(all_words.keys())]
    tweet = word['tweet']
    link = word['link']
    printOrTweet(tweet + "\n" + link)


def tweetAboutFromSpreadsheet(category):
    """Function to tweet a random tweet from the spreadsheet."""

    # Use the global config variable
    global config
    
    import gspread
    gc = gspread.login(config['gspread']['username'], config['gspread']['password'])

    sheet = gc.open('bslbot\'s brain')

    wks = sheet.worksheet(category)

    # Get all the values as a list
    wks_list = wks.get_all_values()

    # Remove the title
    #
    # TODO replace this with finding which column corresponds to which thing
    # (tweet, link, etc.)

    # Fetch the important column indicies
    tweet_cell_col = wks.find("Tweet").col
    no_of_times_tweeted_cell_col = wks.find("No of times tweeted").col

    # Try to find a link column, but if you don't, don't sweat it.
    try:
        link_cell_col = wks.find("Link").col
    except gspread.exceptions.CellNotFound:
        pass


    # Remove the titles from the list of cells
    wks_list.pop(0)

    # Set an arbitrary high number of times tweeted
    lowest_no_of_times_tweeted = 9001
    candidates_for_tweeting = []
    for i in wks_list:
        # -1 in the next line because python counts from 0, spreadsheets count
        # from 1
        no_of_times_tweeted = int(i[no_of_times_tweeted_cell_col-1])
        if no_of_times_tweeted < lowest_no_of_times_tweeted:
            # if this tweet has the lowest no_of_times_tweeted so far dump the
            # rest of them and start the list with this one
            print 'dumping candidates'
            lowest_no_of_times_tweeted = no_of_times_tweeted
            candidates_for_tweeting = [ i ]
        elif no_of_times_tweeted == lowest_no_of_times_tweeted:
            # otherwise if it's equally untweeted, carry on and add this one to
            # the list
            candidates_for_tweeting.append(i)
        # else: do nothing

    chosen_tweet = random.choice(candidates_for_tweeting)

    # The original function has some complex logic here to make sure that it
    # tweets things int he correct order. The new logic does not require this
    # (yet) as it is only for BSLDictionary entries

    # Find the cell that holds the chosen tweet
    cell_for_chosen_tweet = wks.find(chosen_tweet[tweet_cell_col-1])
    print cell_for_chosen_tweet
    print cell_for_chosen_tweet.value

    # If there is a link defined, use it. 
    if 'link_cell_col' in locals():
        tweet_to_return = wks.cell(cell_for_chosen_tweet.row, tweet_cell_col).value\
                          + " "\
                          + config['misc']['signature']\
                          + "\n"\
                          + wks.cell(cell_for_chosen_tweet.row, link_cell_col).value
    else:
        tweet_to_return = wks.cell(cell_for_chosen_tweet.row, tweet_cell_col).value\
                          + " "\
                          + config['misc']['signature']\
                

    # Mark the chosen tweet as tweeted one more time
    print wks.cell(cell_for_chosen_tweet.row, 5)
    print wks.cell(cell_for_chosen_tweet.row, 5).value
    current_no_of_times_tweeeted = int( wks.cell( cell_for_chosen_tweet.row,
                                                  no_of_times_tweeted_cell_col ).value )

    # Update the number of times tweeted
    wks.update_cell( cell_for_chosen_tweet.row,
                     no_of_times_tweeted_cell_col,
                     current_no_of_times_tweeeted + 1)
    

    return tweet_to_return
            

    

    
    
def tweetAbout(category):
    """Function to choose a semi-random tweet from a predefined list.

    This function looks at all the tweets in a category and then chooses one
    that has not been used in a while. Specifically, it chooses tweets which
    have been tweeted the least.

    E.g. If all but 10 tweets in a category have been tweeted once, and 10 have
    never been tweeted, this function will only choose from those 10."""

    global config

    if category == 'words':
        # TODO make tweetAboutFromSpreadsheet the main tweetAbout function
        return tweetAboutFromSpreadsheet()
    
    # This little code block is bslbot's method for not tweeting the same thing
    # all the time. In fact, bslbot never tweets the same thing twice (once a
    # category is chosen) until he doesn't have a choice.
    lowest_no_of_times_tweeted = 9001
    candidates_for_tweeting = []
    for i in config['tweets'][category].keys():
        # if this tweet has the lowest no_of_times_tweeted so far dump the
        # rest of them and start the list with this one
        if config['tweets'][category][i]['no_of_times_tweeted'] < lowest_no_of_times_tweeted:
            print 'dumping candidates'
            lowest_no_of_times_tweeted = config['tweets'][category][i]['no_of_times_tweeted']
            print 'lowest times is ', lowest_no_of_times_tweeted
            candidates_for_tweeting = [ i ]
        # otherwise if it's equally untweeted, carry on and add this one to
        # the list
        elif config['tweets'][category][i]['no_of_times_tweeted'] == lowest_no_of_times_tweeted:
            candidates_for_tweeting.append(i)
        # else: rejected (do nothing)


    chosen_tweet = random.choice(candidates_for_tweeting)
    tmptweet = config['tweets'][category][chosen_tweet]['tweet']
    # If there is a link, try and add it to the tweet along with the
    # signature. If not, just add the signature
    try:
        tmptweet = tmptweet + "\n" + config['tweets'][category][chosen_tweet]['link'] + " " + config['misc']['signature']
    except KeyError:
        tmptweet = tmptweet + " " + config['misc']['signature']
    
    config['tweets'][category][chosen_tweet]['no_of_times_tweeted'] +=1
    config.write()
    
    return tmptweet
    

def _whatShouldITweetAbout():

    """Internal function allowing bslbot to decide what to tweet about.

    Returns string."""

    free_will =  random.random()
    
    if free_will <0.01:
        return tweetAboutFromSpreadsheet('SelfPromotion')
    elif free_will <0.1:
        return tweetAboutFromSpreadsheet('Advice')
    else:
        return tweetAboutFromSpreadsheet('BSLDictionary')
    

def tweet(text=None, delay=0):
    """Function instructing bslbot to tweet.

    If no arguments are given, bslbot decides what to tweet on his own."""

    # bslbot should use the global config in this function.
    global config 

    import time
    time.sleep(delay)

    # After sleeping for that long, bslbot needs to reload the config file just
    # in case it's changed
    config = ConfigObj(os.path.expanduser('~/.bslbot'), unrepr=True)

    
    if text==None:
        printOrTweet(_whatShouldITweetAbout())
    else:
        printOrTweet(text)


def follow_back():
    """Simple function to follow back people on twitter.

    Taken shamelessly from http://www.dototot.com/write-twitter-bot-python-tweepy-follow-new-followers/
    """
    for follower in tweepy.Cursor(api.followers).items():
        follower.follow()
        print follower.screen_name


if __name__ == "__main__":
    print "Starting bslbot..."
    tweet(delay=random.randint(1,config['misc']['max_delay']))
    time.sleep(10)
    #follow_back()
