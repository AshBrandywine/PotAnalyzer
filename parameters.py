import getopt


class Parameters:
    unix_options = "hd:o:"
    gnu_options = ["help", "depth=", "output="]

    def __init__(self, argument_input):
        self.display_help = False
        self.depth = 1
        self.derivative_output_name = "derivatives.txt"
        self.mask_analysis_output_name = "masks.txt"
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
                self.mask_analysis_output_name = current_value + "_masks.txt"
