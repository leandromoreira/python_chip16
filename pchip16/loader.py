def load(file_path):
    raw_array = []
    with open(file_path, "rb") as f:
        chars = f.read()
        for i, char in enumerate(chars):
            raw_array.append(ord(char))
    return raw_array
