import os
import sys
import re


def sanitize(filepath):
    data = ""
    base_dir = os.path.dirname(filepath)

    with open(filepath) as f:
        data = f.read()

    # ignore old docs
    if data.find('```cue') >= 0:
        return ""

    # strip header
    n = data.find("\n# ")
    if n >= 0:
        data = data[n+1:]
    else:
        print(f"warning: can't find title in {filepath}")

    # strip tags
    data = re.sub(r"\<Tab.+\n", "", data)
    data = re.sub(r"\</Tab.+\n", "", data)

    match = True
    while match is True:
        # Force re-run the finditer from the beginning given we're modifying data in place
        match = False

        for match in re.finditer(r"file=(\./.*)\n", data):
            fpath = os.path.join(base_dir, match.group(1))
            with open(fpath) as f:
                data = "{}\n{}\n{}".format(data[:match.start(0)], f.read(), data[match.end(0):])
            match = True
            break


    # strip double lines
    data = re.sub(r"\n\n+", "\n\n", data)

    return data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} filepath")
        sys.exit(1)

    filepath = sys.argv[1]

    doc = sanitize(filepath)
    if len(doc) == 0:
        print(f"ignored file: {filepath}")
    else:
        print(f"sanitized file: {filepath}")

    # replace the original file with the sanitized one
    with open(filepath, "w") as f:
        f.write(doc)
