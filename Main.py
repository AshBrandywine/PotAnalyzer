import sys
import passwordtools


if len(sys.argv) < 2:
    print("Please provide a Hashcat pot file.")
    exit(0)

masks = {}
derivative_set = set()

try:
    with open(sys.argv[1], "r") as potfile:
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
except IOError:
    print("The provided pot file was invalid or could not be found.")

try:
    with open("derivatives.txt", "w") as outfile:
        for derivative in derivative_set:
            outfile.write(derivative + "\n")
except IOError:
    print("There was an issue writing the derivatives output.")

try:
    with open("masks.txt", "w") as outfile:
        for mask in masks.keys():
            outfile.write(mask + " - " + str(masks[mask]) + "\n")
except IOError:
    print("There was an issue writing the mask analysis output")

print("Unique derivatives computed: " + str(len(derivative_set)))
print("Masks analyzed: " + str(len(masks)))


