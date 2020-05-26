#!/usr/bin/env python3

import sys
import shutil
import time
from datetime import timedelta
import math
from analyzertools import passwordtools, parameters, masktools, batchwriter, progress

data_handler = None
writer = None
word_extractor = passwordtools.WordExtractor()
used_hashes = set()
omitted_hashes = set()
masks = {}
ordered_mask_list = []
password_count = 0
omission_count = 0
unique_derivative_count = 0


def print_usage():
    print("""usage: %s /your/potfile/path 
    [-o, --output OUTPUT_NAME]                  Give the output files a unique prefix
    [-a, --analyze-only]                        Skip generating derivatives, only analyze the potfile (very fast)
    [-w, --mask-weight-cutoff CUTOFF]           Between 0 and 1, basically how large to make the mask attack file (default 0.3)
    [-p, --previous-passwords PASSWORD_LIST]    Include a potfile or word list to omit from derivative generation
    [-d, --depth DEPTH]                         [DEPRECATED] How many times to recursively re-process derivative results [DEPRECATED]
    [-l, --deriver-length-limit LIMIT]          Character length limit of passwords used to generate derivatives (default 16)
    [-b, --batch-size SIZE]                     Smaller size reduces peak memory usage at the cost of performance (default 1000000)
    [-h, --help]                                Show this help output""" % sys.argv[0])


def collection_to_pretty_string(collection):
    string_builder = []
    first_item = True
    for item in collection:
        if first_item:
            first_item = False
        else:
            string_builder.append(", ")
        string_builder.append(str(item))
    return "".join(string_builder)


def add_used_password(password):
    used_hashes.add(hash(password))


def is_password_used(password):
    return hash(password) in used_hashes


def add_omitted_password(password):
    omitted_hashes.add(hash(password))


def is_password_omitted(password):
    return hash(password) in omitted_hashes


def parse_potfile_line(line_input, try_parse_malformed=False):
    line = line_input.strip()
    start_index = line.find(':') + 1
    if 0 < start_index < len(line):
        return line[start_index:]
    if try_parse_malformed:
        return line
    return ''


def import_password_omissions(filename):
    global omission_count
    try:
        with open(filename, "r") as previous_passwords:
            print("Importing previous password file...")
            for line in previous_passwords.readlines():
                password = parse_potfile_line(line, try_parse_malformed=True)
                if len(password) == 0:
                    continue
                add_omitted_password(password)
                omission_count += 1
    except IOError:
        print("The provided previous password file was invalid or could not be found.")


def analyze_masks(weight_cutoff):
    global ordered_mask_list
    print("Analyzing masks...")
    ordered_mask_list = [(v, k) for k, v in masks.items()]
    ordered_mask_list.sort(reverse=True)
    mask_list = []
    mask_count_cutoff = math.ceil(float(password_count) * weight_cutoff)
    print("Mask cutoff: " + str(weight_cutoff))
    print("Most common masks for " + str(mask_count_cutoff) + " passwords will be processed.")
    mask_process_password_count = 0
    for count_mask_pair in ordered_mask_list:
        if mask_process_password_count > mask_count_cutoff:
            break
        mask_process_password_count += count_mask_pair[0]
        mask_list.append(count_mask_pair[1])
    return masktools.get_mask_attack_suggestions(mask_list)


def pre_analyze_potfile(potfile_name):
    global password_count
    try:
        with open(potfile_name, 'r') as potfile:
            print('Loading potfile for analysis...')
            for line in potfile.readlines():
                password = parse_potfile_line(line)
                if len(password) == 0 or is_password_omitted(password):
                    continue
                word_extractor.extract(password)
                mask = masktools.get_mask(password)
                mask_key = "".join(mask)
                if mask_key in masks.keys():
                    masks[mask_key] = masks[mask_key] + 1
                else:
                    masks[mask_key] = 1
                password_count += 1
    except IOError:
        print('The provided potfile was invalid or could not be found.')


def output_derivatives(potfile_name, output_name, password_length_limit, batch_size):
    global unique_derivative_count
    progress_prefix = '\rGenerating and outputting unique derivatives... '
    counter = 1
    try:
        with open(potfile_name, 'r') as potfile:
            with batchwriter.BatchWriter(output_name) as batch_writer:
                batch_writer.batch_size = batch_size
                tracker = progress.ProgressTracker(password_count)
                for line in potfile.readlines():
                    password = parse_potfile_line(line)
                    if len(password) == 0 or is_password_omitted(password):
                        continue
                    tracker.update(counter)
                    sys.stdout.write(progress_prefix + str(tracker))
                    sys.stdout.flush()
                    counter += 1
                    if not is_password_used(password) and len(password) <= password_length_limit:
                        add_used_password(password)
                        fresh_derivative_set = passwordtools.get_all_derivatives(password)
                        batch_writer.add_many_lines(fresh_derivative_set)
                unique_derivative_count = batch_writer.unique_line_count()
    except IOError:
        print('Could not access potfile for derivative generation.')


def backup_potfile(potfile_name, backup_name):
    try:
        shutil.copyfile(potfile_name, backup_name)
    except IOError:
        print("There was a problem producing the previous used password file")


def write_maskfile_output(filename, mask_attack_list):
    try:
        with open(filename, "w") as outfile:
            for mask in mask_attack_list:
                outfile.write(mask + "\n")
    except IOError:
        print("There was an issue writing the mask attack file")


def write_analysis_output(filename):
    try:
        with open(filename, "w") as outfile:
            outfile.write("Common words in passwords:\n")
            for word_tuple in word_extractor.get_ordered_common_words():
                occurrences = word_tuple[0]
                if occurrences < 2:
                    break
                pct = (float(occurrences) / float(password_count)) * 100.00
                if pct < 0.01:
                    break
                word = word_tuple[1]
                variants = word_extractor.get_variants(word)
                outfile.write("%s (%.2f%%) - %s\n" % (occurrences, pct, collection_to_pretty_string(variants)))
            outfile.write("\nCommon password masks:\n")
            for mask_tuple in ordered_mask_list:
                occurrences = mask_tuple[0]
                if occurrences < 2:
                    break
                pct = (float(occurrences) / float(password_count)) * 100.00
                if pct < 0.01:
                    break
                mask = mask_tuple[1]
                outfile.write("%s (%.2f%%) - %s\n" % (occurrences, pct, mask))
    except IOError:
        print("There was an issue writing the analysis file")


def elapsed_time_str(start_time, end_time):
    process_time = round(end_time - start_time, 2)
    process_time_string = str(timedelta(seconds=process_time))
    if process_time % 1 > 0:
        process_time_string = process_time_string.rstrip("0")
    return process_time_string


def main():
    global data_handler
    global writer

    if len(sys.argv) < 2:
        print_usage()
        exit()

    params = parameters.Parameters(sys.argv)

    if params.display_help:
        print_usage()
        exit()

    start_time = time.time()
    if params.previous_passwords is not None and not params.analyze_only:
        import_password_omissions(params.previous_passwords)
    pre_analyze_potfile(params.potfile_name)
    mask_attack_suggestions = analyze_masks(params.mask_weight_cutoff)
    write_maskfile_output(params.maskfile_output_name, mask_attack_suggestions)
    write_analysis_output(params.analysis_output_name)
    if not params.analyze_only:
        output_derivatives(params.potfile_name, params.derivative_output_name,
                           params.derivative_base_length_limit, params.writer_batch_size)
        backup_potfile(params.potfile_name, params.potfile_backup_name)
    end_time = time.time()

    print("\n* * *")
    if params.analyze_only:
        print("Results saved to '%s' '%s'" % (params.maskfile_output_name,
                                              params.analysis_output_name))
    else:
        print("Results saved to '%s' '%s' '%s'" % (params.derivative_output_name,
                                                   params.maskfile_output_name,
                                                   params.analysis_output_name))
        print("Potfile backup saved to '%s'" % params.potfile_backup_name)
    print("* * *")
    print("Processing took %s" % elapsed_time_str(start_time, end_time))
    print("* * *")
    print("Passwords processed from potfile: %s" % str(password_count))
    print("Unique derivatives computed: %s" % str(unique_derivative_count))
    print("Unique Masks discovered: %s" % str(len(masks)))
    print("%s focused attack masks created for .hcmask file" % str(len(mask_attack_suggestions)))


if __name__ == "__main__":
    main()
