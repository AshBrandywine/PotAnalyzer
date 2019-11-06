import sys
import time
import sqlite3
import parameters
import passwordtools


def print_usage():
    print("usage: " + sys.argv[0] + " /your/potfile/path [-d, --depth DEPTH] [-o, --output OUTPUT_NAME] [-h, --help]")


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
with sqlite3.connect(":memory:") as db:
    db.execute("create table password_set (password text, unique(password))")
    db.execute("create table derivative_set (password text, unique(password))")
    db.execute("create table new_password_set (password text, unique(password))")
    db.commit()
    masks = {}
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
                db.execute("insert or ignore into password_set values (?)", (password,))
                db.commit()
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
        record_count = str(db.execute("select count(password) from password_set").fetchone()[0])
        progress_prefix = "\rProcessing password set for depth " + str(i+1) + "... "
        db.execute("delete from new_password_set")
        db.commit()
        counter = 1
        cursor = db.execute("select password from password_set")
        for row in cursor:
            sys.stdout.write(progress_prefix + str(counter) + "/" + record_count)
            sys.stdout.flush()
            counter += 1
            new_derivative_set = passwordtools.get_all_derivatives(row[0])
            db.executemany("insert or ignore into new_password_set values (?)", iterate_set_as_tuples(new_derivative_set))
        db.commit()
        print()
        print("Aggregating results from depth " + str(i+1) + "...")
        db.execute("insert or ignore into derivative_set(password) select password from new_password_set")
        db.execute("delete from password_set")
        db.execute("insert or ignore into password_set(password) select password from new_password_set")
        db.commit()

    unique_derivatives_computed = db.execute("select count(password) from derivative_set").fetchone()[0]

    print("Outputting results to disk...")

    try:
        with open(params.derivative_output_name, "w") as outfile:
            cursor = db.execute("select password from derivative_set")
            for row in cursor:
                outfile.write(row[0] + "\n")
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

end_time = time.time()
process_time = end_time - start_time
print("Processing took %.4f seconds" % process_time)

print("Unique derivatives computed: " + str(unique_derivatives_computed))
print("Unique Masks discovered: " + str(len(masks)))
print("Results saved to '" + params.derivative_output_name + "' and '" + params.mask_analysis_output_name + "'")


