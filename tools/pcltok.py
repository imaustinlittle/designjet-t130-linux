"""Minimal PCL tokenizer for HP PCL3GUI captures.

Yields (offset, cmd, value, data) for each escape sequence.
cmd is like '*b' + 'W' (e.g. '*bW'), value is the numeric string,
data is the binary payload for commands that carry one.
"""
import re, sys

DATA_CMDS = {'W', 'V'}  # uppercase terminators that carry #bytes of data


def tokenize(d, start=0):
    i = start
    n = len(d)
    while i < n:
        if d[i] != 0x1b:
            # raw byte outside an escape; report run
            j = d.find(b'\x1b', i)
            if j < 0:
                j = n
            yield (i, 'RAW', None, d[i:j])
            i = j
            continue
        if i + 1 >= n:
            break
        c1 = d[i + 1]
        # two-character escape (ESC E, ESC %... handled below)
        if c1 == ord('%') and d[i:i + 9] == b'\x1b%-12345X':
            yield (i, 'UEL', None, b'')
            i += 9
            continue
        if not (0x21 <= c1 <= 0x2f):
            yield (i, chr(c1), None, b'')
            i += 2
            continue
        # parameterized: ESC c1 group (value param)*  last param uppercase
        if i + 2 >= n:
            break
        group = chr(d[i + 2])
        k = i + 3
        prefix = chr(c1) + group
        while True:
            m = re.match(rb'[+-]?[0-9]*\.?[0-9]*', d[k:k + 20])
            val = m.group(0).decode()
            k += len(val)
            if k >= n:
                return
            p = chr(d[k])
            k += 1
            data = b''
            if p.upper() in DATA_CMDS:
                ln = int(float(val)) if val not in ('', '+', '-') else 0
                data = d[k:k + ln]
                k += ln
            yield (i, prefix + p.upper(), val, data)
            if p.isupper() or not p.isalpha():
                break
            # combined form: next parameter continues with same prefix
            i = k  # report offset of continuation
        i = k


def pcl_body(d):
    j = d.find(b'ENTER LANGUAGE')
    j = d.find(b'\n', j) + 1
    return j


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    start = pcl_body(d)
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    for c, (off, cmd, val, data) in enumerate(tokenize(d, start)):
        if c >= limit:
            break
        extra = ''
        if data:
            extra = f' len={len(data)} ' + data[:24].hex(' ')
        print(f'{off:7d} {cmd:5s} {val if val is not None else "":>8s}{extra}')
