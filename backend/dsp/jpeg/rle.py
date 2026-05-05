def rle_encode(arr):
    encoded = []
    count = 1

    for i in range(1, len(arr)):
        if arr[i] == arr[i - 1]:
            count += 1
        else:
            encoded.append((float(arr[i - 1]), count))
            count = 1

    encoded.append((float(arr[-1]), count))
    return encoded


def rle_decode(encoded):
    decoded = []

    for value, count in encoded:
        decoded.extend([value] * count)

    return decoded