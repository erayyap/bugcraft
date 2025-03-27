import argparse
import sys

def sort_file(input_file, output_file, sort_type, sort_order="asc"):
    """Sorts a text file line by line based on the specified criteria.

    Args:
        input_file: Path to the input text file.
        output_file: Path to the output text file.
        sort_type: The type of sorting to perform:
                   - "length": Sort by line length.
                   - "second_word": Sort by the second word of each line.
                   - "first_number": Sort numerically by the first number in each line.
                   - "alphanumeric": Default alphanumeric sort
        sort_order: "asc" for ascending order (default), "desc" for descending.
    """
    try:
        with open(input_file, "r") as f_in, open(output_file, "w") as f_out:
            lines = f_in.readlines()

            if sort_type == "length":
                lines.sort(key=len, reverse=(sort_order == "desc"))
            elif sort_type == "second_word":
                lines.sort(
                    key=lambda line: line.split()[1] if len(line.split()) > 1 else "",
                    reverse=(sort_order == "desc"),
                )
            elif sort_type == "first_number":
                lines.sort(
                    key=lambda line: int(line.split()[0])
                    if line.split() and line.split()[0].isdigit()
                    else float('-inf') if sort_order == "asc" else float('inf'),  # Handle lines without numbers at the beginning or end depending on sort order
                    reverse=(sort_order == "desc"),
                )
            elif sort_type == "alphanumeric":
                lines.sort(reverse=(sort_order == "desc"))
            else:
                print(f"Error: Invalid sort type '{sort_type}'.")
                return
            f_out.writelines(lines)
        print(f"File sorted successfully. Output written to '{output_file}'.")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description="Sort a text file line by line.")
    parser.add_argument("input_file", help="Path to the input text file.")
    parser.add_argument("output_file", help="Path to the output text file.")
    parser.add_argument(
        "-t",
        "--sort_type",
        choices=["length", "second_word", "first_number", "alphanumeric"],
        default="alphanumeric",
        help="Type of sorting to perform (default: alphanumeric).",
    )
    parser.add_argument(
        "-o",
        "--sort_order",
        choices=["asc", "desc"],
        default="asc",
        help="Sorting order: 'asc' for ascending, 'desc' for descending (default: asc).",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    sort_file(args.input_file, args.output_file, args.sort_type, args.sort_order)

if __name__ == "__main__":
    main()