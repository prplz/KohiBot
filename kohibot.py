from gevent import monkey

monkey.patch_all()


def main():
    from argparse import ArgumentParser
    arg_parser = ArgumentParser()
    arg_parser.add_argument('--test', help='Test mode, don''t tweet', action='store_true', default=False)
    args = arg_parser.parse_args()

    import settings
    from twitterbot import TwitterBot
    bot = TwitterBot(settings, args)
    bot.run()


if __name__ == '__main__':
    main()
