import sys
import shutil
import time
from datetime import timedelta
import math
import DataHandler
import ParameterTools
import PasswordTools
import MaskTools


parameters = None
data_handler = None


def print_usage():
    print("usage: " + sys.argv[0] + " /your/potfile/path [-d, --depth DEPTH] [-o, --output OUTPUT_NAME] [-a, --analyze-only] [-w, --mask-weight-cutoff CUTOFF] [-p, --previous-passwords PASSWORD_LIST] [-h, --help]")


def print_progress(prefix_comment, completed, total, time_left=None):
    percent = (float(completed) / float(total)) * 100
    if time_left is None or len(time_left) == 0:
        sys.stdout.write("%s %d/%d (%.2f%%)" % (prefix_comment, completed, total, percent))
    else:
        sys.stdout.write("%s %d/%d (%.2f%%) Estimated time remaining: %s" % (prefix_comment, completed, total, percent, time_left))
    sys.stdout.flush()


def get_estimated_time_remaining(percentage_complete, progress_start_time):
    time_elapsed = time.time() - progress_start_time
    if time_elapsed > 0:
        completion_rate = percentage_complete / time_elapsed
        remaining_percentage = 1.00 - percentage_complete
        seconds_left = round(remaining_percentage / completion_rate)
        return str(timedelta(seconds=seconds_left))
    return "Unknown"


def iterate_set_as_tuples(my_set):
    for set_item in my_set:
        yield (set_item,)


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


def main():
    global parameters
    global data_handler

    if len(sys.argv) < 2:
        print_usage()
        exit()

    parameters = ParameterTools.Parameters(sys.argv)

    if parameters.display_help:
        print_usage()
        exit()

    unique_derivatives_computed = 0
    password_total = 0
    masks = {}

    start_time = time.time()
    with DataHandler.SqliteDataHandler() as data_handler:
        word_extractor = PasswordTools.WordExtractor()

        if parameters.previous_passwords is not None and not parameters.analyze_only:
            try:
                with open(parameters.previous_passwords, "r") as previous_passwords:
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
            except IOError:
                print("The provided previous password file was invalid or could not be found.")

        try:
            with open(parameters.potfile_name, "r") as potfile:
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
                    mask = MaskTools.get_mask(password)
                    mask_key = "".join(mask)
                    if mask_key in masks.keys():
                        masks[mask_key] = masks[mask_key] + 1
                    else:
                        masks[mask_key] = 1
                    password_total += 1
                data_handler.commit()
                data_handler.flush_staged_passwords()
        except IOError:
            print("The provided pot file was invalid or could not be found.")

        print("Analyzing masks...")
        masks_ordered = [(v, k) for k, v in masks.items()]
        masks_ordered.sort(reverse=True)
        mask_list = []
        mask_count_cutoff = math.ceil(float(password_total) * parameters.mask_weight_cutoff)
        print("Mask cutoff: " + str(parameters.mask_weight_cutoff))
        print("Most common masks for " + str(mask_count_cutoff) + " passwords will be processed.")
        mask_process_password_count = 0
        for count_mask_pair in masks_ordered:
            if mask_process_password_count > mask_count_cutoff:
                break
            mask_process_password_count += count_mask_pair[0]
            mask_list.append(count_mask_pair[1])
        mask_attack_suggestions = MaskTools.get_mask_attack_suggestions(mask_list)

        if not parameters.analyze_only:
            for i in range(parameters.depth):
                record_count = data_handler.working_password_count()
                progress_prefix = "\rProcessing password set for depth " + str(i+1) + "... "
                counter = 1
                cursor = data_handler.get_working_password_iterator()
                depth_start_time = time.time()
                time_remaining_text = None
                for row in cursor:
                    if counter % 128 == 0:
                        time_remaining_text = get_estimated_time_remaining(float(counter) / float(record_count), depth_start_time)
                    print_progress(progress_prefix, counter, record_count, time_remaining_text)
                    counter += 1
                    fresh_derivative_set = PasswordTools.get_all_derivatives(row[0])
                    data_handler.stage_many_passwords(fresh_derivative_set, auto_commit=False)
                data_handler.commit()
                print("")
                print("Aggregating results from depth " + str(i+1) + "...")
                data_handler.flush_staged_passwords()
            unique_derivatives_computed = data_handler.derivative_count()

        print("Outputting results to disk...")

        if not parameters.analyze_only:
            try:
                with open(parameters.derivative_output_name, "w") as outfile:
                    cursor = data_handler.get_derivative_iterator()
                    for row in cursor:
                        outfile.write(row[0] + "\n")
            except IOError:
                print("There was an issue writing the derivatives output.")

            try:
                shutil.copyfile(parameters.potfile_name, parameters.potfile_backup_name)
            except IOError:
                print("There was a problem producing the previous used password file")

        try:
            with open(parameters.maskfile_output_name, "w") as outfile:
                for mask in mask_attack_suggestions:
                    outfile.write(mask + "\n")
        except IOError:
            print("There was an issue writing the mask attack file")

        try:
            with open(parameters.analysis_output_name, "w") as outfile:
                outfile.write("Common words in passwords:\n")
                for word_tuple in word_extractor.get_ordered_common_words():
                    occurrences = word_tuple[0]
                    if occurrences < 2:
                        break
                    pct = (float(occurrences) / float(password_total)) * 100.00
                    if pct < 0.01:
                        break
                    word = word_tuple[1]
                    variants = word_extractor.get_variants(word)
                    outfile.write("%s (%.2f%%) - %s\n" % (occurrences, pct, collection_to_pretty_string(variants)))
                outfile.write("\nCommon password masks:\n")
                for mask_tuple in masks_ordered:
                    occurrences = mask_tuple[0]
                    if occurrences < 2:
                        break
                    pct = (float(occurrences) / float(password_total)) * 100.00
                    if pct < 0.01:
                        break
                    mask = mask_tuple[1]
                    outfile.write("%s (%.2f%%) - %s\n" % (occurrences, pct, mask))
        except IOError:
            print("There was an issue writing the analysis file")

    end_time = time.time()

    print("* * *")

    print("Results saved to '" + parameters.derivative_output_name + "' '" + parameters.maskfile_output_name + "' '" + parameters.analysis_output_name + "'")
    print("Potfile backup saved to '" + parameters.potfile_backup_name + "'")

    print("* * *")

    process_time = end_time - start_time
    print("Processing took %s" % str(timedelta(seconds=process_time)))

    print("* * *")

    print("Passwords processed from potfile: " + str(password_total))
    print("Unique derivatives computed: " + str(unique_derivatives_computed))
    print("Unique Masks discovered: " + str(len(masks)))
    print(str(len(mask_attack_suggestions)) + " focused attack masks created for .hcmask file")


if __name__ == "__main__":
    main()

