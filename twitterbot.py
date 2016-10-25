import random
import re
from time import time

import gevent
import tweepy
from peewee import IntegrityError

from brain import Brain
from db import Tweet
from util import sanitize_words


class TwitterBot:
    def __init__(self, settings, args):
        self.settings = settings
        self.args = args

        self.auth = tweepy.OAuthHandler(*self.settings.oauth)
        self.auth.set_access_token(*self.settings.access_token)
        self.api = tweepy.API(self.auth)
        self.me = self.api.me()

        self.brain = None
        self.reload_brain()

    def reload_brain(self):
        self.brain = Brain.from_db(self.settings.brain_select_limit)

    def run(self):
        gevent.spawn(self.check_tweets)

        if self.settings.tweet_schedule:
            gevent.spawn(self.tweet_scheduler)

        if self.settings.replies:
            listener = tweepy.StreamListener()
            listener.on_status = self.on_reply
            stream = tweepy.Stream(auth=self.auth, listener=listener)
            gevent.spawn(stream.userstream)

        # Keep main alive
        while True:
            gevent.sleep(1)

    def check_tweets(self):
        while True:
            for user in self.settings.users:
                try:
                    tweets = self.api.user_timeline(
                        id=user,
                        count=200,
                        exclude_replies=True,
                        include_rts=False,
                        tweet_mode='extended')
                    tweets_saved = 0
                    for tweet in tweets:
                        try:
                            tweets_saved += Tweet.from_tweepy(tweet).save(force_insert=True)
                        except IntegrityError:
                            pass
                    if tweets_saved > 0:
                        print '[check_tweets] Got %d new tweets from %s' % (tweets_saved, user)
                        self.reload_brain()
                except Exception as exc:
                    print '[check_tweets] Error while getting tweets of %s: %s' % (user, exc)
                gevent.sleep(10)

    def tweet_scheduler(self):
        t = int(time())
        seconds = self.settings.tweet_schedule_minutes * 60
        while True:
            if int(time()) / seconds != t / seconds:
                self.update_status(status=self.brain.ramble())
            t = int(time())
            gevent.sleep(1)

    def on_reply(self, status):
        if status.in_reply_to_user_id == self.me.id:
            print '[on_reply] %s' % status.text
            msg = re.sub(r'@\w+ ?', '', status.text)
            words = sanitize_words(msg.split())
            at = '@' + status.user.screen_name + ' '
            seed_word = random.choice(words) if words else None
            reply = at + self.brain.ramble(max_len=140 - len(at), seed_word=seed_word)
            self.update_status(status=reply, in_reply_to_status_id=status.id)

    def update_status(self, **kwargs):
        if self.args.test:
            print '[update_status] %s (Not tweeted due to --test)' % kwargs['status']
        else:
            print '[update_status] %s' % kwargs['status']
            self.api.update_status(**kwargs)