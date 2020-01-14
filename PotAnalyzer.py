#!/usr/bin/env python3

import sys
import shutil
import time
from datetime import timedelta
import math
from analyzertools import passwordtools, parameters, database, masktools

data_handler = None
word_extractor = passwordtools.WordExtractor()
masks = {}
ordered_mask_list = []
password_count = 0
omission_count = 0


def print_usage():
    print("""usage: %s /your/potfile/path 
    [-o, --output OUTPUT_NAME]                  Give the output files a unique prefix
    [-a, --analyze-only]                        Skip generating derivatives, only analyze the potfile (very fast)
    [-w, --mask-weight-cutoff CUTOFF]           Between 0 and 1, basically how large to make the mask attack file (default 0.3)
    [-p, --previous-passwords PASSWORD_LIST]    Include a potfile or word list to omit from derivative generation
    [-d, --depth DEPTH]                         How many times to recursively re-process derivative results (default 1, exponentially intensive)
    [-h, --help]                                Show this help output""" % sys.argv[0])


def print_progress(prefix_comment, completed, total, time_left=None):
    percent = (float(completed) / float(total)) * 100
    if time_left is None or len(time_left) == 0:
        sys.stdout.write("%s %d/%d (%.2f%%)" % (prefix_comment, completed, total, percent))
    else:
        sys.stdout.write("%s %d/%d (%.2f%%) Estimated time remaining: %s" % (prefix_comment, completed, total,
                                                                             percent, time_left))
    sys.stdout.flush()


def get_estimated_time_remaining(percentage_complete, progress_start_time):
    time_elapsed = time.time() - progress_start_time
    if time_elapsed > 0:
        completion_rate = percentage_complete / time_elapsed
        remaining_percentage = 1.00 - percentage_complete
        seconds_left = round(remaining_percentage / completion_rate)
        return str(timedelta(seconds=seconds_left))
    return "Unknown"


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


def import_password_omissions(filename):
    global omission_count
    try:
        with open(filename, "r") as previous_passwords:
            print("Importing previous password file...")
            for line in previous_passwords.readlines():
                line_split = line.strip().split(":")
                if len(line_split) == 1:
                    password = line_split[0]
                else:
                    password = line_split[len(line_split)-1]
                if len(password) == 0:
                    continue
                data_handler.add_omitted_password(password)
                omission_count += 1
    except IOError:
        print("The provided previous password file was invalid or could not be found.")


def import_potfile(filename):
    global password_count
    try:
        with open(filename, "r") as potfile:
            print("Importing passwords from potfile...")
            for line in potfile.readlines():
                line_split = line.strip().split(":")
                if len(line_split) < 2:
                    continue
                password = line_split[len(line_split)-1]
                if len(password) == 0:
                    continue
                if data_handler.password_is_omitted(password):
                    continue
                data_handler.stage_password(password, auto_commit=False)
                word_extractor.extract(password)
                mask = masktools.get_mask(password)
                mask_key = "".join(mask)
                if mask_key in masks.keys():
                    masks[mask_key] = masks[mask_key] + 1
                else:
                    masks[mask_key] = 1
                password_count += 1
            data_handler.commit()
    except IOError:
        print("The provided pot file was invalid or could not be found.")


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


def generate_derivatives(depth):
    for i in range(depth):
        record_count = data_handler.working_password_count()
        progress_prefix = "\rProcessing password set for depth " + str(i+1) + "... "
        counter = 1
        cursor = data_handler.get_working_password_iterator()
        depth_start_time = time.time()
        time_remaining_text = None
        for row in cursor:
            if counter % 128 == 0:
                time_remaining_text = get_estimated_time_remaining(float(counter) / float(record_count),
                                                                   depth_start_time)
            print_progress(progress_prefix, counter, record_count, time_remaining_text)
            counter += 1
            fresh_derivative_set = passwordtools.get_all_derivatives(row[0])
            data_handler.stage_many_passwords(fresh_derivative_set, auto_commit=False)
        data_handler.commit()
        print("")
        print("Aggregating results from depth " + str(i+1) + "...")
        data_handler.flush_staged_passwords()


def write_derivative_output(filename):
    try:
        with open(filename, "w") as outfile:
            cursor = data_handler.get_derivative_iterator()
            for row in cursor:
                outfile.write(row[0] + "\n")
    except IOError:
        print("There was an issue writing the derivatives output.")


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

    if len(sys.argv) < 2:
        print_usage()
        exit()

    params = parameters.Parameters(sys.argv)

    if params.display_help:
        print_usage()
        exit()

    unique_derivatives_computed = 0
    start_time = time.time()
    with database.SqliteDataHandler() as data_handler:
        if params.previous_passwords is not None and not params.analyze_only:
            import_password_omissions(params.previous_passwords)
        import_potfile(params.potfile_name)
        mask_attack_suggestions = analyze_masks(params.mask_weight_cutoff)
        if not params.analyze_only:
            data_handler.flush_staged_passwords()
            generate_derivatives(params.depth)
            unique_derivatives_computed = data_handler.derivative_count()
        print("Outputting results to disk...")
        if not params.analyze_only:
            write_derivative_output(params.derivative_output_name)
            backup_potfile(params.potfile_name, params.potfile_backup_name)
        write_maskfile_output(params.maskfile_output_name, mask_attack_suggestions)
        write_analysis_output(params.analysis_output_name)
    end_time = time.time()

    print("* * *")
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
    print("Unique derivatives computed: %s" % str(unique_derivatives_computed))
    print("Unique Masks discovered: %s" % str(len(masks)))
    print("%s focused attack masks created for .hcmask file" % str(len(mask_attack_suggestions)))


if __name__ == "__main__":
    main()

