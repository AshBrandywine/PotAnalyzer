

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
             "b": ("8", "l3", "13", "6"),
             "c": ("[", "{", "<", "("),
             "d": ("t", ")", "[)", "1)", "l)"),
             "e": ("3", "&"),
             "f": ("ph"),
             "g": ("&", "6", "gee"),
             "h": ("#"),
             "i": ("1", "l", "!", "eye"),
             "j": ("1", "l"),
             # "k": (),
             "l": ("1", "7"),
             "m": ("/v\\", "/V\\", "/\\/\\"),
             # "n": (),
             "o": ("0", "p", "u", "Q", "oh"),
             # "p": (),
             # "q": (),
             # "r": (),
             "s": ("5", "$", "z", "Z"),
             "t": ("7"),
             # "u": (),
             "v": ("\\/"),
             "w": ("\\/\\/", "VV", "vv"),
             # "x": (),
             "y": ("j", "i", "7"),
             "z": ("2", "7", "s", "S")}


def get_mask(password):
    mask = []
    for char in password:
        if alpha_lower_pool.__contains__(char):
            mask.append(alpha_lower_mask)
        elif alpha_upper_pool.__contains__(char):
            mask.append(alpha_upper_mask)
        elif digit_pool.__contains__(char):
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

# TODO - These need to be more than just 1 substitute at a time
def get_leet_derivatives(password):
    derivative_set = set()
    for i in range(len(password)):
        char = password[i].lower()
        if char in leet_dict.keys():
            substitutes = leet_dict[char]
            for sub in substitutes:
                derivative_builder = list(password)
                del derivative_builder[i]
                derivative_builder.insert(i, sub)
                derivative_set.add("".join(derivative_builder))
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

