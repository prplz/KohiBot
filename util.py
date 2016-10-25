def sanitize_words(words):
    # filter links
    words = filter(lambda w: not (w.startswith('http://') or w.startswith('https://')), words)

    # avoid mentions
    words = map(lambda w: w.replace('@', ''), words)

    # strip symbols
    words = map(lambda w: w.strip('`~!#$%^&*()-_=+[{]};:\'",<.>/?\\|'), words)

    return words
