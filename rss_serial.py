# RSS Serial:
#   Fetches random entries from multiple RSS feeds (i.e. Twitter) 
#   and outputs them to a serial port in multiple parts.
#
#   Sending a new message requires serial input of ASCII 'n'
#   Sending the next part of a message requires serial input of 'g'
#
#   Written in Python 2.7 by Walfas.

import serial, feedparser, random, sys

#############
# Functions #
#############

def refreshFeeds():
    """Refresh all RSS feeds"""
    feedNumber = 0
    for URL in RSS_FEED_URLS:
        rssFeed[feedNumber] = feedparser.parse(URL)
        feedNumber += 1

def group(string, n):
    """Splits a string into smaller substrings of character length n
        From: http://snippets.dzone.com/posts/show/5641 """
    return [string[i:i+n] for i in xrange(0, len(string), n)]

#############
# Constants #
#############

SERIAL_PORT = "/dev/tty.usbmodemfd131"
#RSS_FEED_URLS = ["http://twitter.com/statuses/user_timeline/783214.rss",
#                 "http://twitter.com/statuses/user_timeline/86775205.rss",
#                 "http://twitter.com/statuses/user_timeline/20731304.rss",
#                 "http://twitter.com/statuses/user_timeline/24923100.rss",
#                 "http://twitter.com/statuses/user_timeline/17877351.rss",
#                 "http://twitter.com/statuses/user_timeline/14607140.rss"
#                 ]

RSS_FEED_URLS = ["http://twitter.com/statuses/user_timeline/810777.rss",
				 "http://twitter.com/statuses/user_timeline/172008956.rss"
                 ]

# In messages, replace the text in REPLACE_ORIG with the
#   text in REPLACE_WITH having the same index
REPLACE_ORIG = ["&lt;", "&gt;", "&amp;", "http://"]
REPLACE_WITH = ["<", ">", "&", ""]

# Refresh feeds after this many entries are read
REFRESH_RATE = 100

# Number of characters to send before waiting for the Arduino 
#   to request more. This is necessary due to the fact that the
#   Arduino has a 128-byte serial buffer, so this prevents long 
#   messages from getting cut off.
BYTES_TO_SEND = 72

########
# Main #
########

# Create a serial object
arduino = serial.Serial(SERIAL_PORT, 9600, timeout=5)

numFeeds = len(RSS_FEED_URLS)
rssFeed = [None]*numFeeds
numEntries = [None]*numFeeds
refreshFeeds()

# Determine the number of entries in each feed
for i in range(numFeeds):
    numEntries[i] = len(rssFeed[i]['entries'])

messagesDisplayed = 0
sendingMessage = True

while True:
    # Check if the feeds need refreshing
    if messagesDisplayed > REFRESH_RATE:
        messagesDisplayed = 0
        refreshFeeds()

    # Check to see if the Arduino is waiting for a new message
    if arduino.inWaiting() > 0:
        if arduino.read() == 'n':   # 'n' for "next message"
            
            # Choose a random message from a random feed
            whichFeed = random.randint(0,numFeeds-1)
            message = '@' + rssFeed[whichFeed]['entries'][random.randint(0,numEntries[whichFeed]-1)].description + '\n'
            
            # Replace certain substrings with other strings
            for i in range(len(REPLACE_ORIG)):
                message = message.replace(REPLACE_ORIG[i], REPLACE_WITH[i])

            # Split the message into multiple parts if necessary
            messageParts = group(message, BYTES_TO_SEND)
            currentMessagePart = 0

            sendingMessage = True

    # Check if the Arduino is waiting for the next part of a message
    while sendingMessage:
        if arduino.inWaiting() > 0:
            if arduino.read() == 'g':   # 'g' for "get"

                # Attempt to send the message to the Arduino
                try:
                    arduino.write(messageParts[currentMessagePart]) # Write to serial port
                    sys.stdout.write(messageParts[currentMessagePart]) # Print to screen
                    currentMessagePart += 1     # Advance to the next message

                    # If this is the last part of the message,
                    #   there's nothing else to send.
                    if currentMessagePart >= len(messageParts):
                        messagesDisplayed += 1
                        sendingMessage = False

                # Write a null character if message-sending fails (usually due to encoding)
                except:
                    arduino.write('\0')
                    sendingMessage = False
