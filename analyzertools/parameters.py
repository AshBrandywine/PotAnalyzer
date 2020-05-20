import getopt


class Parameters:
    unix_options = "hd:o:aw:p:l:b:"
    gnu_options = ["help", "depth=", "output=", "analyze-only", "mask-weight-cutoff=", "previous-passwords=",
                   "deriver-length-limit=", "batch-size="]

    def __init__(self, argument_input):
        self.display_help = False
        self.depth = 1
        self.derivative_output_name = "derivatives.txt"
        self.maskfile_output_name = "masks.hcmask"
        self.analysis_output_name = "analysis.txt"
        self.potfile_backup_name = "processed.potfile"
        self.previous_passwords = None
        self.mask_weight_cutoff = 0.30
        self.analyze_only = False
        self.derivative_base_length_limit = 16
        self.writer_batch_size = 1000000
        if argument_input[1].startswith("-"):
            self.display_help = True
        else:
            self.potfile_name = argument_input[1]
            if len(argument_input) > 2:
                self._parse_optional_arguments(argument_input[2:])

    def _parse_optional_arguments(self, optional_arguments):
        arguments, values = getopt.getopt(optional_arguments, self.unix_options, self.gnu_options)
        for current_argument, current_value in arguments:
            if current_argument in ("-h", "--help"):
                self.display_help = True
            elif current_argument in ("-d", "--depth"):
                self.depth = max(int(current_value), 1)
            elif current_argument in ("-o", "--output"):
                self.derivative_output_name = current_value + "_derivatives.txt"
                self.maskfile_output_name = current_value + "_masks.hcmask"
                self.analysis_output_name = current_value + "_analysis.txt"
                self.potfile_backup_name = current_value + "_processed.potfile"
            elif current_argument in ("-a", "--analyze-only"):
                self.analyze_only = True
            elif current_argument in ("-w", "--mask-weight-cutoff"):
                self.mask_weight_cutoff = float(current_value)
            elif current_argument in ("-p", "--previous-passwords"):
                self.previous_passwords = current_value
            elif current_argument in ("-l", "--deriver-length-limit"):
                self.derivative_base_length_limit = current_value
            elif current_argument in ("-b", "--batch-size"):
                self.writer_batch_size = int(current_value)
