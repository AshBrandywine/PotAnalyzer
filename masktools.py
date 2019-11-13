

alpha_lower_mask = "?l"
alpha_lower_pool = "abcdefghijklmnopqrstuvwxyz"

alpha_upper_mask = "?u"
alpha_upper_pool = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

digit_mask = "?d"
digit_pool = "0123456789"

special_mask = "?s"
special_pool = "!\"#$%&'()*+,-./:;<=>?@[]^_`{|}~"

year_length = 4
recent_centuries = ("19", "20")
famous_pre_1900_years = ("1054", "1088", "1206", "1215", "1453", "1455", "1492", "1509", "1517", "1519", "1564", "1651", "1687", "1776", "1789", "1815", "1825", "1859", "1885", "1893")


def _generate_mask_builder(mask):
    mask_builder = []
    for i in range(0, len(mask), 2):
        mask_builder.append(mask[i] + mask[i+1])
    return mask_builder


def _generate_year_derivatives(mask_builder, year_start_index):
    derivatives = []
    derivative_builder = mask_builder.copy()
    for year in famous_pre_1900_years:
        for i in range(len(year)):
            derivative_builder[year_start_index+i] = year[i]
        derivatives.append("".join(derivative_builder))
    for century in recent_centuries:
        derivative_builder[year_start_index] = century[0]
        derivative_builder[year_start_index+1] = century[1]
        derivative_builder[year_start_index+2] = digit_mask
        derivative_builder[year_start_index+3] = digit_mask
        derivatives.append("".join(derivative_builder))
    return derivatives


def _get_year_derivatives(mask_builder):
    derivatives = []
    year_start_index = -1
    digit_counter = 0
    for i in range(len(mask_builder)):
        char = mask_builder[i]
        if char == digit_mask:
            if digit_counter == 0:
                year_start_index = i
            digit_counter += 1
        else:
            if digit_counter == year_length:
                new_derivatives = _generate_year_derivatives(mask_builder, year_start_index)
                derivatives.extend(new_derivatives)
            digit_counter = 0
    if digit_counter == year_length:
        new_derivatives = _generate_year_derivatives(mask_builder, year_start_index)
        derivatives.extend(new_derivatives)
    return derivatives


def get_mask_derivatives(mask_list):
    derivatives = []
    for mask in mask_list:
        mask_builder = _generate_mask_builder(mask)
        year_derivatives = _get_year_derivatives(mask_builder)
        if len(year_derivatives) == 0:
            derivatives.append(mask)
        else:
            derivatives.extend(year_derivatives)
    return derivatives

