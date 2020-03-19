import sys, json

def get_words(path):
    words = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            for w in line.strip().split(" "):
                words.append(w.upper())
    # file is closed automatically
    return words


def count_word(words, search):
    count = 0
    for w in words:
        if w == search:
            count += 1
    return count


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 wc.py <file.txt> (ALL|<word>)")
        sys.exit(1)

    path = sys.argv[1]
    search = sys.argv[2].upper()
    words = get_words(path)

    if search.upper() == "ALL":
        counts = {}
        for word in words:
            if word in counts:
                counts[word] += 1
            else:
                counts[word] = 1
        print(json.dumps(counts, sort_keys=True, indent=2))
    else:
        print(count_word(words, search))


if __name__ == '__main__':
     main()
