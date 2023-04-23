import sys

__equivalent = {
  "  ো  "  : "   ু   ", 
  "  ূ   " :  "  ু   ",
  "  ছ   " : "   চ ",
  " ণ  ":  "  ন  ",
   "  ট  "  : "   ত   ",
   "  ঠ  "  :  "  থ   ",
   "  ড  "  : "  দ   ",
   "  ী  "  : "  ি   ",
   "  স    " : "    হ   ",
   "  ৎ  ":   "  ত "
}
equivalent = {key.strip(): value.strip() for key, value in __equivalent.items()}


def equivalent_text(string):
    for key, value in equivalent.items():
        string = string.replace(key, value)
    return string


# suffixes
_suffixes = ["ক ", "ৰ ", "য়ে   ", " লৈ  ", "ই" , " ৱে  " ]
suffixes = [x.strip() for x in _suffixes]


def substring_around(s, word, around=50):
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
    for word in text.strip().split(" "):
        word_to_record = (word, False)
        for query_word in query_words:
            if query_word.lower() == word.lower():
                word_to_record = (f"<strong>{word}</strong>", True)
                continue
            is_assamese = all(0x0980 <= ord(c) <= 0x09FF for c in query_word)
            if is_assamese:
                if word.startswith(query_word) and word[len(query_word) :] in suffixes:
                    word_to_record = (f"<strong>{word}</strong>", True)
                    continue

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

    return text_segments


def page_match_score(text, query_words):
    score = sys.maxsize
    num_words = len(query_words)

    # mark the words whether query word or not
    words_pos = {}
    for idx, word in enumerate(text.strip().split(" ")):
        for query_word in query_words:
            is_assamese = all(0x0980 <= ord(c) <= 0x09FF for c in query_word)
            if query_word.lower() == word.lower():
                words_pos[word.lower()] = idx
                if len(words_pos) == num_words:
                    idxs = sorted(list(words_pos.values()), key=lambda x: x)
                    score = idxs[-1] - idxs[0]
                    continue

    return score
