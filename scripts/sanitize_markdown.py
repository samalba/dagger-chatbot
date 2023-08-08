import sys
import re


def sanitize(filepath):
    data = ""

    with open(filepath) as f:
        data = f.read()

    # strip header
    n = data.find("\n# ")
    if n == -1:
        print("Can't find title")
        return
    data = data[n+1:]

    # strip tags
    data = re.sub(r"\<Tab.+\n", "", data)
    data = re.sub(r"\</Tab.+\n", "", data)

    match = True
    while match is True:
        # Force re-run the finditer from the beginning given we're modifying data in place
        match = False

        for match in re.finditer(r"file=(\./.*)\n", data):
            fpath = match.group(1)
            with open(fpath) as f:
                data = "{}\n{}\n{}".format(data[:match.start(0)], f.read(), data[match.end(0):])
            match = True
            break


    # strip double lines
    data = re.sub(r"\n\n+", "\n\n", data)

    return data


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} input-path output-path")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    doc = sanitize(input_file)
    with open(output_file, "+w") as f:
        f.write(doc)
