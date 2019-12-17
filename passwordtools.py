import MaskTools
import LeetTools


def _generate_character_replace_derivatives(password, character_index, character_pool):
    derivative_set = set()
    for char in character_pool:
        if password[character_index] == char:
            continue
        derivative_builder = list(password)
        derivative_builder[character_index] = char
        derivative_set.add("".join(derivative_builder))
    return derivative_set


def get_mask_derivatives(password, mask=None):
    if mask is None:
        mask = MaskTools.get_mask(password)
    derivative_set = set()
    for i in range(len(password)):
        mask_code = mask[i]
        character_pool = MaskTools.get_character_pool_from_mask_code(mask_code)
        derivative_set = derivative_set | _generate_character_replace_derivatives(password, i, character_pool)
    return derivative_set


def get_add_derivatives(password, mask=None):
    if mask is None:
        mask = MaskTools.get_mask(password)
    derivative_set = set()
    for i in range(len(password) + 1):
        character_pool = ""
        if i > 0:
            character_pool = character_pool.join(MaskTools.get_character_pool_from_mask_code(mask[i - 1]))
        if i < len(password):
            character_pool = character_pool.join(MaskTools.get_character_pool_from_mask_code(mask[i]))
        for char in character_pool:
            derivative_builder = list(password)
            derivative_builder.insert(i, char)
            derivative_set.add("".join(derivative_builder))
    return derivative_set


def get_remove_derivatives(password):
    derivative_set = set()
    for i in range(len(password)):
        derivative_builder = list(password)
        del derivative_builder[i]
        derivative_set.add("".join(derivative_builder))
    return derivative_set


def get_leet_derivatives(password):
    derivative_set = set()
    leet_generator = LeetTools.LeetGenerator(password)
    while leet_generator.has_next:
        derivative_set.add(leet_generator.get_next_permutation())
    return derivative_set


def get_all_derivatives(password, mask=None):
    if mask is None:
        mask = MaskTools.get_mask(password)
    derivative_set = set()
    derivative_set.update(get_mask_derivatives(password, mask))
    derivative_set.update(get_add_derivatives(password, mask))
    derivative_set.update(get_remove_derivatives(password))
    derivative_set.update(get_leet_derivatives(password))
    return derivative_set


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

