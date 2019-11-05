import sys
import time
import parameters
import passwordtools


def print_usage():
    print("usage: " + sys.argv[0] + " /your/potfile/path [-d, --depth DEPTH] [-o, --output OUTPUT_NAME] [-h, --help]")


if len(sys.argv) < 2:
    print_usage()
    exit()

params = parameters.Parameters(sys.argv)

if params.display_help:
    print_usage()
    exit()

if len(sys.argv) > 2:
    argument_list = sys.argv[1:]

masks = {}
password_set = set()
derivative_set = set()

start_time = time.time()

try:
    with open(params.potfile_name, "r") as potfile:
        print("Importing passwords from potfile...")
        for line in potfile.readlines():
            line_split = line.strip().split(":")
            if len(line_split) < 2:
                continue
            password = line_split[len(line_split)-1]
            password_set.add(password)
            mask = passwordtools.get_mask(password)
            mask_key = "".join(mask)
            if mask_key in masks.keys():
                masks[mask_key] = masks[mask_key] + 1
            else:
                masks[mask_key] = 1
except IOError:
    print("The provided pot file was invalid or could not be found.")

used_password_set = set()
for i in range(params.depth):
    progress_prefix = "\rProcessing password set for depth " + str(i+1) + "... "
    new_password_set = set()
    counter = 1
    for password in password_set:
        sys.stdout.write(progress_prefix + str(counter) + "/" + str(len(password_set)))
        sys.stdout.flush()
        counter += 1
        new_derivative_set = passwordtools.get_all_derivatives(password) - used_password_set
        new_password_set.update(new_derivative_set)
        derivative_set.update(new_derivative_set)
    used_password_set.update(new_password_set)
    password_set = new_password_set
    print()

end_time = time.time()
process_time = end_time - start_time
print("Processing took %.4f seconds" % process_time)

try:
    with open(params.derivative_output_name, "w") as outfile:
        for derivative in derivative_set:
            outfile.write(derivative + "\n")
except IOError:
    print("There was an issue writing the derivatives output.")

try:
    with open(params.mask_analysis_output_name, "w") as outfile:
        masks_ordered = [(v, k) for k, v in masks.items()]
        masks_ordered.sort(reverse=True)
        for mask_tuple in masks_ordered:
            outfile.write(str(mask_tuple[0]) + " - " + str(mask_tuple[1]) + "\n")
except IOError:
    print("There was an issue writing the mask analysis output")

print("Unique derivatives computed: " + str(len(derivative_set)))
print("Unique Masks discovered: " + str(len(masks)))
print("Results saved to '" + params.derivative_output_name + "' and '" + params.mask_analysis_output_name + "'")


