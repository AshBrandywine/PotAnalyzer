import passwordtools

masks = {}
derivative_set = set()

with open("pot.txt", "r") as potfile:
    for line in potfile.readlines():
        line_split = line.strip().split(":")
        if len(line_split) < 2:
            continue
        password = line_split[1]
        mask = passwordtools.get_mask(password)
        mask_key = "".join(mask)
        if masks.__contains__(mask_key):
            masks[mask_key] = masks[mask_key] + 1
        else:
            masks[mask_key] = 1
        derivative_set.update(passwordtools.get_all_derivatives(password, mask))

print(masks)

print(derivative_set)
print(len(derivative_set))

