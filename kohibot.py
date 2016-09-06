import random
from argparse import ArgumentParser
from collections import defaultdict

import tweepy

import settings


def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument('-c', '--count', help='How many messages to generate', type=int, default=1)
    arg_parser.add_argument('--tweet', help='Tweet the last message generated', action='store_true', default=False)
    args = arg_parser.parse_args()

    auth = tweepy.OAuthHandler(*settings.oauth)
    auth.set_access_token(*settings.access_token)
    api = tweepy.API(auth)

    chain = defaultdict(list)
    tweet_count = 0

    for user in settings.users:
        print 'Getting tweets for %s...' % user
        try:
            for tweet in api.user_timeline(id=user, count=100, exclude_replies=True, include_rts=False):
                words = tweet.text.split()
                if chain_words(chain, words):
                    tweet_count += 1
        except tweepy.error.TweepError as e:
            print 'Error getting tweets: %s' % e

    print 'Got %d tweets' % tweet_count
    print 'Chain length: %d' % len(chain)

    message = None
    for i in range(args.count):
        message = ramble(chain)
        print repr(message)

    if args.tweet and message is not None:
        print 'Tweeeting: ' + repr(message)
        api.update_status(message)


def chain_words(chain, words):
    # require 5+ word sentences
    if len(words) < 5:
        return False

    # filter links
    words = filter(lambda w: not (w.startswith('http://') or w.startswith('https://')), words)

    # filter mentions
    words = map(lambda w: w.strip('.,"\'@()[]!?'), words)

    # map start word
    chain[None].append(words[0])

    # map every word to the one before
    for i in range(1, len(words)):
        chain[words[i - 1].lower()].append(words[i])

    # map end word
    chain[words[-1].lower()].append(None)

    return True


def ramble(chain, max_len=140):
    # starting word
    word = random.choice(chain[None])
    msg = word

    while True:
        # get random word that can follow the previous one
        word = random.choice(chain[word.lower()])

        # reached sentence end, break out
        if not word:
            break

        newmsg = msg + ' ' + word
        if len(newmsg) > max_len:
            break
        msg = newmsg

    return msg


if __name__ == '__main__':
    main()
