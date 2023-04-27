import sys

__equivalent = {
   "  ো  "  : "   ু   ", 
   "  ূ   " :  "  ু   ",
   "  ছ   " : "   চ ",
   " ণ  " :  "  ন  ",
   "  ট  "  : "   ত   ",
   "  ঠ  "  :  "  থ   ",
   "  ড  "  : "  দ   ",
   "  ী  "  : "  ি   ",
   "  স    " : "    হ   ",
   "  ৎ  ":   "  ত ", 
    "  ।  ":   "    ",
    "  ঁ  ":  "   "
}
equivalent = {key.strip(): value.strip() for key, value in __equivalent.items()}

# suffixes
_suffixes = ["ক ", "ৰ ", "য়ে   ", " লৈ  ", "ই" , " ৱে  " ]
suffixes = [x.strip() for x in _suffixes]


def equivalent_text(string, ignore_suffix=False):
    for key, value in equivalent.items():
        string = string.replace(key, value)

    if ignore_suffix:
       for suffix in suffixes:
          if string.endswith(suffix):
              return string[:-len(suffix)] 

    return string

def are_similar(string1, string2, ignore_suffix=False):
    
    if string1.lower()==string2.lower():
       return True

    if ignore_suffix:
        if len(string1) > len(string2):
           return string1[len(string2):] in suffixes
        elif len(string1) < len(string2):
           return string2[len(string1):] in suffixes

    return False


def substring_around(s, word, around=50):
    index = s.find(word)
    if index != -1:
        start = max(0, index - around)
        end = min(len(s), index + len(word) + around)
        result = s[start:end]
        return result
    return ""


def text_with_query_words(text, query_words_equiv, delta=20):
    # mark the words whether query word or not
    words_marked = []
    for word in text.strip().split(" "):
        word_to_record = (word, False)

        for query_word_equiv in query_words_equiv:
            word_equiv = equivalent_text(word)
            if query_word_equiv.lower() == word_equiv.lower():
                word_to_record = (f"<strong>{word}</strong>", True)
                break

            is_assamese = all(0x0980 <= ord(c) <= 0x09FF for c in query_word_equiv)
            if is_assamese:
                if word_equiv.startswith(query_word_equiv) and word_equiv[len(query_word_equiv) :] in suffixes:
                    word_to_record = (f"<strong>{word}</strong>", True)
                    break
        words_marked.append(word_to_record)

    text_segments = []
    lower = 0
    while lower < len(words_marked):
        i = lower
        while i < len(words_marked) and words_marked[i][1] == False:
            i = i + 1

        # reached the final word
        if i == len(words_marked):
            break

        left, right = max(lower, i - delta), min(len(words_marked), i + delta)
        text_segments.append(" ".join([x[0] for x in words_marked[left:right]]))
        lower = right

    #print(sum([True for x,y in words_marked if x]) , text_segments)

    return text_segments


def page_match_score_v2(word_loc_arrays):
    score = sys.maxsize
    num_words = len(word_loc_arrays)
    
    all_word_locs = []
    for word_loc_array in word_loc_arrays:
       all_word_locs += word_loc_array
    all_word_locs.sort(key=lambda x: x[1])

    words_pos = {}
    for word_loc in all_word_locs:
        words_pos[word_loc[0]] = word_loc[1]
        if len(words_pos) == num_words:
           idxs = sorted(list(words_pos.values()), reverse=False)
           if score > idxs[-1] - idxs[0]:
              score = idxs[-1] - idxs[0]

    return score

def page_match_score(text, query_words_equiv):
    score = sys.maxsize
    num_words = len(query_words_equiv)

    # mark the words whether query word or not
    words_pos = {}
    for idx, word in enumerate(text.strip().split(" ")):
        for query_word_equiv in query_words_equiv:
            word_equiv = equivalent_text(word)

            # exact match
            if query_word_equiv.lower() == word_equiv.lower():
                words_pos[word_equiv.lower()] = idx
                if len(words_pos) == num_words:
                    idxs = sorted(list(words_pos.values()), key=lambda x: x)
                    if score > idxs[-1] - idxs[0]:
                       score = idxs[-1] - idxs[0]
                break

            is_assamese = all(0x0980 <= ord(c) <= 0x09FF for c in query_word_equiv)
            if is_assamese:
                if word_equiv.startswith(query_word_equiv) and word_equiv[len(query_word_equiv) :] in suffixes:
                    words_pos[word_equiv.lower()] = idx
                    if len(words_pos) == num_words:
                        idxs = sorted(list(words_pos.values()), key=lambda x: x)
                        if score > idxs[-1] - idxs[0]:
                           score = idxs[-1] - idxs[0]
                    break

    return score


def merge_word_indices(word_index, extended_word_index): 
   """
      merge extended_word_indec to word_index

   """ 
   # merge the two word indices
   for book, page_array in extended_word_index.items():
     # if book id already seen add the new page numbers, otherwise add a new entry for the book
     if book in word_index:
        word_index[book] = sorted(
              list(set(word_index[book]).union(set(page_array))),
              reverse=False)
     else:
        word_index[book] = page_array
