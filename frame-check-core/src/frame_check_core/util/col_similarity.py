from collections.abc import Iterable
from functools import cache


@cache
def jaro_winkler(s1: str, s2: str) -> float:
    s1, s2 = s1.lower(), s2.lower()
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    max_dist = int(max(len1, len2) / 2) - 1

    match = 0
    hash_s1 = [0] * len1
    hash_s2 = [0] * len2

    for i in range(len1):
        for j in range(max(0, i - max_dist), min(len2, i + max_dist + 1)):
            if s1[i] == s2[j] and hash_s2[j] == 0:
                hash_s1[i] = 1
                hash_s2[j] = 1
                match += 1
                break

    if match == 0:
        return 0.0

    t = 0
    point = 0
    for i in range(len1):
        if hash_s1[i]:
            while hash_s2[point] == 0:
                point += 1
            if s1[i] != s2[point]:
                t += 1
            point += 1
    t = t // 2

    jaro = (match / len1 + match / len2 + (match - t) / match) / 3.0

    # Jaro-Winkler adjustment
    prefix = 0
    for i in range(min(len1, len2)):
        if s1[i] == s2[i]:
            prefix += 1
        else:
            break
    prefix = min(4, prefix)

    return jaro + 0.1 * prefix * (1 - jaro)


def zero_deps_jaro_winkler(target_col: str, existing_cols: Iterable[str]) -> str | None:
    if not existing_cols:
        return None

    jw_distances_dict = {
        col: abs(jaro_winkler(target_col, col)) for col in existing_cols
    }

    if jw_distances_dict.values():
        target_value = max(jw_distances_dict.values())
        if target_value > 0.9:
            index = list(jw_distances_dict.values()).index(target_value)
            result = list(jw_distances_dict.keys())[index]
            return result

    return None
