

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


reverse_leet_dict = {"4": "a",
                     "@": "a",
                     "3": "e",
                     "$": "s",
                     "5": "s",
                     "1": "l",
                     "0": "o"}


def has_leet_substitutions(char):
    return char in leet_dict.keys()


def get_leet_substitutions(char):
    return leet_dict[char]


def is_possible_leet_substitution(char):
    return char in reverse_leet_dict.keys()


def deleet(char):
    return reverse_leet_dict[char]


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
        self.has_next = False
        self.omni_mask = self.__getmask__(password)
        self.counter_list = []
        self.counter_head = None
        self.counter_tail = None
        for i in range(len(self.omni_mask)):
            mask_chars = self.omni_mask[i]
            max_value = len(mask_chars) - 1
            self.__appendcounter__(max_value)
            if max_value > 0:
                self.has_next = True
        self.__increment__()

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
            if has_leet_substitutions(char):
                omni_mask.append((char,) + get_leet_substitutions(char))
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
        return "".join(permutation_builder)

