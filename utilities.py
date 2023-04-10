
def substring_around(s, word, around= 50):

    index = s.find(word)
    
    if index != -1:
        start = max(0, index - around)
        end = min(len(s), index + len(word) + around)
        result = s[start:end]
        return result

    return ""
