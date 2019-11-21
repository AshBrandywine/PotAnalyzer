import sys
import shutil
import time
from datetime import timedelta
import math
import sqlite3
import parameters
import passwordtools
import masktools


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


if len(sys.argv) < 2:
    print_usage()
    exit()

params = parameters.Parameters(sys.argv)

if params.display_help:
    print_usage()
    exit()

if len(sys.argv) > 2:
    argument_list = sys.argv[1:]

unique_derivatives_computed = 0
start_time = time.time()
with sqlite3.connect("") as db:
    db.execute("create table password_set (password text, unique(password))")
    db.execute("create table omission_set (password text, unique(password))")
    db.execute("create table derivative_set (password text, unique(password))")
    db.execute("create table new_password_set (password text, unique(password))")
    db.commit()
    masks = {}
    password_total = 0

    if params.previous_passwords is not None and not params.analyze_only:
        try:
            with open(params.previous_passwords, "r") as previous_passwords:
                print("Importing previous password file...")
                for line in previous_passwords.readlines():
                    line_split = line.strip().split(":")
                    password = None
                    if len(line_split) == 1:
                        password = line_split[0]
                    else:
                        password = line_split[len(line_split)-1]
                    if len(password) == 0:
                        continue
                    db.execute("insert or ignore into omission_set values (?)", (password,))
                    db.commit()
        except IOError:
            print("The provided previous password file was invalid or could not be found.")

    try:
        with open(params.potfile_name, "r") as potfile:
            print("Importing passwords from potfile...")
            for line in potfile.readlines():
                line_split = line.strip().split(":")
                if len(line_split) < 2:
                    continue
                password = line_split[len(line_split)-1]
                if len(password) == 0:
                    continue
                cursor = db.execute("select * from omission_set where password = ?", (password,))
                if cursor.rowcount > 0:
                    continue
                db.execute("insert or ignore into password_set values (?)", (password,))
                db.commit()
                mask = passwordtools.get_mask(password)
                mask_key = "".join(mask)
                if mask_key in masks.keys():
                    masks[mask_key] = masks[mask_key] + 1
                else:
                    masks[mask_key] = 1
                password_total += 1
    except IOError:
        print("The provided pot file was invalid or could not be found.")

    print("Analyzing masks...")
    masks_ordered = [(v, k) for k, v in masks.items()]
    masks_ordered.sort(reverse=True)
    mask_list = []
    mask_count_cutoff = math.ceil(float(password_total) * params.mask_weight_cutoff)
    print("Mask cutoff: " + str(params.mask_weight_cutoff))
    print("Most common masks for " + str(mask_count_cutoff) + " passwords will be processed.")
    mask_process_password_count = 0
    for count_mask_pair in masks_ordered:
        if mask_process_password_count > mask_count_cutoff:
            break
        mask_process_password_count += count_mask_pair[0]
        mask_list.append(count_mask_pair[1])
    mask_derivatives = masktools.get_mask_derivatives(mask_list)

    unique_derivatives_computed = 0
    if not params.analyze_only:
        for i in range(params.depth):
            record_count = db.execute("select count(password) from password_set").fetchone()[0]
            progress_prefix = "\rProcessing password set for depth " + str(i+1) + "... "
            db.execute("delete from new_password_set")
            db.commit()
            counter = 1
            cursor = db.execute("select password from password_set")
            depth_start_time = time.time()
            time_remaining_text = None
            for row in cursor:
                if counter % 128 == 0:
                    time_remaining_text = get_estimated_time_remaining(float(counter) / float(record_count), depth_start_time)
                print_progress(progress_prefix, counter, record_count, time_remaining_text)
                counter += 1
                new_derivative_set = passwordtools.get_all_derivatives(row[0])
                db.executemany("insert or ignore into new_password_set values (?)", iterate_set_as_tuples(new_derivative_set))
            db.commit()
            print("")
            print("Aggregating results from depth " + str(i+1) + "...")
            db.execute("insert or ignore into derivative_set(password) select password from new_password_set")
            db.execute("delete from password_set")
            db.execute("insert or ignore into password_set(password) select password from new_password_set")
            db.commit()
        unique_derivatives_computed = db.execute("select count(password) from derivative_set").fetchone()[0]

    print("Outputting results to disk...")

    if not params.analyze_only:
        try:
            with open(params.derivative_output_name, "w") as outfile:
                cursor = db.execute("select password from derivative_set")
                for row in cursor:
                    outfile.write(row[0] + "\n")
        except IOError:
            print("There was an issue writing the derivatives output.")

        try:
            shutil.copyfile(params.potfile_name, params.potfile_backup_name)
        except IOError:
            print("There was a problem producing the previous used password file")

    try:
        with open(params.maskfile_output_name, "w") as outfile:
            for mask in mask_derivatives:
                outfile.write(mask + "\n")
    except IOError:
        print("There was an issue writing the mask file")

    try:
        with open(params.analysis_output_name, "w") as outfile:
            for mask_tuple in masks_ordered:
                outfile.write(str(mask_tuple[0]) + " - " + str(mask_tuple[1]) + "\n")
    except IOError:
        print("There was an issue writing the analysis file")

end_time = time.time()
process_time = end_time - start_time
print("Processing took %s" % str(timedelta(seconds=process_time)))

print("Unique derivatives computed: " + str(unique_derivatives_computed))
print("Unique Masks discovered: " + str(len(masks)))
print(str(len(mask_derivatives)) + " mask derivatives created for .hcmask file")
print("Results saved to '" + params.derivative_output_name + "' '" + params.maskfile_output_name + "' '" + params.analysis_output_name + "'")


