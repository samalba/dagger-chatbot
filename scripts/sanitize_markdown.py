import os
import sys
import re


def sanitize(filepath):
    data = ""
    base_dir = os.path.dirname(filepath)

    with open(filepath) as f:
        data = f.read()

    # ignore old docs
    for keyword in ["```cue", "dagger-cue"]:
        if data.find(keyword) >= 0:
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

    # replace ```language file=XXX/XXX```
    match = True
    while match is True:
        # Force re-run the finditer from the beginning given we're modifying data in place
        match = False

        for m in re.finditer(r"file=(.*)\n", data):
            match = True
            fname = m.group(1).strip()
            fpath = os.path.join(base_dir, fname)
            content = ""
            if os.path.exists(fpath):
                with open(fpath) as f:
                    content = f.read()
            data = "{}\n{}\n{}".format(data[:m.start(0)], content, data[m.end(0):])
            break

    # replace {@include: XXX/XXX}
    match = True
    while match is True:
        # Force re-run the finditer from the beginning given we're modifying data in place
        match = False

        for m in re.finditer(r"{@include: (.*)}", data):
            match = True
            fname = m.group(1).strip()
            fpath = os.path.join(base_dir, fname)
            content = ""
            if os.path.exists(fpath):
                with open(fpath) as f:
                    content = f.read()
            data = "{}{}{}".format(data[:m.start(0)], content, data[m.end(0):])
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
