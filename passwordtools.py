

alpha_lower_mask = "?l"
alpha_lower_pool = "abcdefghijklmnopqrstuvwxyz"

alpha_upper_mask = "?u"
alpha_upper_pool = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

numeric_mask = "?d"
digit_pool = "0123456789"

special_mask = "?s"
special_pool = "!\"#$%&'()*+,-./:;<=>?@[]^_`{|}~"

# http://www.gamehouse.com/blog/leet-speak-cheat-sheet/
leet_dict = {"a": ("4", "@"),
             "b": ("8",),
             # "c": (),
             # "d": (),
             "e": ("3",),
             "f": ("ph",),
             "g": ("6",),
             # "h": (),
             "i": ("1", "l"),
             "j": ("1", "l"),
             # "k": (),
             "l": ("1", "7"),
             # "m": (),
             # "n": (),
             "o": ("0", "p", "u"),
             # "p": (),
             # "q": (),
             # "r": (),
             "s": ("5", "$"),
             "t": ("7",),
             # "u": (),
             # "v": (),
             # "w": (),
             # "x": (),
             "y": ("j", "i", "7"),
             "z": ("2", "7")}


def get_mask(password):
    mask = []
    for char in password:
        if char in alpha_lower_pool:
            mask.append(alpha_lower_mask)
        elif char in alpha_upper_pool:
            mask.append(alpha_upper_mask)
        elif char in digit_pool:
            mask.append(numeric_mask)
        else:
            mask.append(special_mask)
    return mask


def _generate_character_replace_derivatives(password, character_index, character_pool):
    derivative_set = set()
    for char in character_pool:
        if password[character_index] == char:
            continue
        derivative_builder = list(password)
        derivative_builder[character_index] = char
        derivative_set.add("".join(derivative_builder))
    return derivative_set


def _get_character_pool_from_mask_code(mask_code):
    if mask_code == alpha_lower_mask:
        return alpha_lower_pool
    if mask_code == alpha_upper_mask:
        return alpha_upper_pool
    if mask_code == numeric_mask:
        return digit_pool
    if mask_code == special_mask:
        return special_pool
    return ""


def get_mask_derivatives(password, mask=None):
    if mask is None:
        mask = get_mask(password)
    derivative_set = set()
    for i in range(len(password)):
        mask_code = mask[i]
        character_pool = _get_character_pool_from_mask_code(mask_code)
        derivative_set = derivative_set | _generate_character_replace_derivatives(password, i, character_pool)
    return derivative_set


def get_add_derivatives(password, mask=None):
    if mask is None:
        mask = get_mask(password)
    derivative_set = set()
    for i in range(len(password) + 1):
        character_pool = ""
        if i > 0:
            character_pool = character_pool.join(_get_character_pool_from_mask_code(mask[i-1]))
        if i < len(password):
            character_pool = character_pool.join(_get_character_pool_from_mask_code(mask[i]))
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
    leet_generator = LeetGenerator(password)
    while leet_generator.has_next:
        derivative_set.add(leet_generator.get_next_permutation())
    return derivative_set


def get_all_derivatives(password, mask=None):
    if mask is None:
        mask = get_mask(password)
    derivative_set = set()
    derivative_set.update(get_mask_derivatives(password, mask))
    derivative_set.update(get_add_derivatives(password, mask))
    derivative_set.update(get_remove_derivatives(password))
    derivative_set.update(get_leet_derivatives(password))
    return derivative_set


class CascadeCounter:
    def __init__(self, max_value):
        self.next_counter = None
        self.value = 0
        self.max_value = max_value

    def increment(self):
        self.value += 1
        if self.value > self.max_value:
            self.value = 0
            if self.next_counter is not None:
                self.next_counter.increment()

    def is_max(self):
        return self.value == self.max_value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str("(" + str(self.value) + "/" + str(self.max_value) + ")")


class LeetGenerator:
    def __init__(self, password):
        self.has_next = True
        self.omni_mask = self.__getmask__(password)
        self.counter_list = []
        self.counter_head = None
        self.counter_tail = None
        for i in range(len(self.omni_mask)):
            mask_chars = self.omni_mask[i]
            max_value = len(mask_chars) - 1
            self.__appendcounter__(max_value)

    def __appendcounter__(self, max_value):
        counter = CascadeCounter(max_value)
        self.counter_list.append(counter)
        if self.counter_head is None:
            self.counter_head = counter
            self.counter_tail = counter
        else:
            self.counter_tail.next_counter = counter
            self.counter_tail = counter

    def __getmask__(self, password):
        omni_mask = []
        for char in password:
            if char in leet_dict.keys():
                omni_mask.append((char,) + leet_dict[char])
            else:
                omni_mask.append((char,))
        return omni_mask

    def __increment__(self):
        self.counter_head.increment()
        for counter in self.counter_list:
            if counter.value != 0:
                return
        self.has_next = False

    def get_next_permutation(self):
        permutation_builder = []
        for i in range(len(self.omni_mask)):
            char_options = self.omni_mask[i]
            current_index = self.counter_list[i].value
            char = char_options[current_index]
            permutation_builder.append(char)
        self.__increment__()
        permutation = "".join(permutation_builder)
        print(permutation)
        return "".join(permutation_builder)

