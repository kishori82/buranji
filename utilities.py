import sys

def substring_around(s, word, around= 50):

    index = s.find(word)
    
    if index != -1:
        start = max(0, index - around)
        end = min(len(s), index + len(word) + around)
        result = s[start:end]
        return result

    return ""


def text_with_query_words(text, query_words, delta=20):

    # mark the words whether query word or not 
    words_marked = []
    for word  in text.strip().split(' '):
       word_to_record = (word, False)
       for query_word in query_words:
          if query_word.lower()==word.lower():
             word_to_record = (f"<strong>{word}</strong>", True) 
             continue

       words_marked.append(word_to_record) 


    text_segments = []
    lower = 0
    while lower < len(words_marked):
       i = lower
       while  i < len(words_marked) and words_marked[i][1]==False:
          i = i + 1

       # reached the final word
       if i==len(words_marked):
          break

       left, right = max(lower, i - delta), min(len(words_marked), i + delta)
       text_segments.append(' '.join([x[0] for x in words_marked[left:right]]))
       lower = right

    return text_segments


def page_match_score(text, query_words):
    score = sys.maxsize
    num_words = len(query_words)

    # mark the words whether query word or not 
    words_pos = {}
    for idx, word  in enumerate(text.strip().split(' ')):
       for query_word in query_words:
          if query_word.lower()==word.lower():
             words_pos[word.lower()] = idx         
             if len(words_pos) == num_words:
               idxs = sorted(list(words_pos.values()), key = lambda x: x)
               score = idxs[-1] - idxs[0] 
               continue

    return score
