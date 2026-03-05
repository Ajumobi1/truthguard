def humanize(text, max_words=100):
    words = text.split()
    return " ".join(words[:max_words]), len(words[:max_words])