def crop(string, pattern, left=True):
    index = string.find(pattern)
    if left:
        return string[index:]
    else:
        return string[:pattern]
