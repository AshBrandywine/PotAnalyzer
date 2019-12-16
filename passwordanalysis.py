

def extract_words(password):
    extracted_words = []
    current_word = []
    building_word = False
    for i in range(len(password)):
        char = password[i]
        if building_word:
            if char.islower():
                current_word.append(char)
            else:
                extracted_words.append("".join(current_word))
                current_word.clear()
                if char.isalpha():
                    current_word.append(char.lower())
                else:
                    building_word = False
        elif char.isalpha():
            building_word = True
            current_word.append(char)
    if building_word:
        extracted_words.append("".join(current_word))
    return extracted_words


class WordExtractor:
    def __init__(self):
        self.extracted_words = {}

    def extract(self, password, minimum_word_size=3):
        words = extract_words(password)
        for word in words:
            if len(word) < minimum_word_size:
                continue
            if word in self.extracted_words.keys():
                count = self.extracted_words.get(word)
                self.extracted_words[word] = count + 1
            else:
                self.extracted_words[word] = 1

    def get_ordered_common_words(self):
        words_ordered = [(v, k) for k, v in self.extracted_words.items()]
        words_ordered.sort(reverse=True)
        return words_ordered

