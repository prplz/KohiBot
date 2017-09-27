import random
from HTMLParser import HTMLParser
from collections import defaultdict

import settings
import util
from db import Tweet
from logger import logger

html_parser = HTMLParser()


class Brain:
    def __init__(self):
        self.chain = defaultdict(list)

    @staticmethod
    def from_db(limit):
        brain = Brain()
        tweets = Tweet.select().order_by(Tweet.tweet_id.desc()).limit(limit)
        tweets_used = 0
        for tweet in tweets:
            if brain.add_tweet(tweet.text):
                tweets_used += 1
        logger.debug('[load_from_db] limit=%d loaded=%d used=%d chain=%d',
                     limit, len(tweets), tweets_used, len(brain.chain))
        return brain

    def add_tweet(self, text):
        text = html_parser.unescape(text)
        words = util.sanitize_words(text.split())

        # require 5+ word sentences
        if len(words) < 5:
            return False

        for word in words:
            word = word.lower()
            for bad_word in settings.blacklist_words:
                if bad_word in word:
                    return False

        # map start word
        self.chain[None].append(words[0])

        # map every word to the one before
        for i in range(1, len(words)):
            self.chain[words[i - 1].lower()].append(words[i])

        # map end word
        self.chain[words[-1].lower()].append(None)

        return True

    def ramble(self, max_len, seed_word=None):
        # starting word
        if seed_word and seed_word.lower() in self.chain:
            word = seed_word
        else:
            word = random.choice(self.chain[None])
        msg = word

        while True:
            # get random word that can follow the previous one
            word = random.choice(self.chain[word.lower()])

            # reached sentence end, break out
            if not word:
                break

            newmsg = msg + ' ' + word
            if len(newmsg) > max_len:
                break
            msg = newmsg

        return msg
