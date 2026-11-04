"""Builds AndroidManifest.xml (binary AXML) and resources.arsc by hand, then packs the APK."""
import struct, zipfile, sys

ANDROID_NS = 'http://schemas.android.com/apk/res/android'
ATTR_IDS = {
    'theme': 0x01010000, 'label': 0x01010001, 'icon': 0x01010002, 'name': 0x01010003,
    'exported': 0x01010010, 'screenOrientation': 0x0101001e, 'configChanges': 0x0101001f,
    'minSdkVersion': 0x0101020c, 'versionCode': 0x0101021b, 'versionName': 0x0101021c,
    'targetSdkVersion': 0x01010270, 'hardwareAccelerated': 0x010102d3,
}
T_REF, T_STR, T_DEC, T_HEX, T_BOOL = 0x01, 0x03, 0x10, 0x11, 0x12


def pad4(b):
    return b + b'\0' * ((4 - len(b) % 4) % 4)


def string_pool(strings, utf8=False):
    offs, data = [], b''
    for s in strings:
        offs.append(len(data))
        if utf8:
            e = s.encode('utf-8')
            assert len(s) < 128 and len(e) < 128
            data += bytes([len(s), len(e)]) + e + b'\0'
        else:
            e = s.encode('utf-16-le')
            data += struct.pack('<H', len(e) // 2) + e + b'\0\0'
    data = pad4(data)
    hdr = 28
    strings_start = hdr + 4 * len(strings)
    flags = 0x100 if utf8 else 0
    body = b''.join(struct.pack('<I', o) for o in offs) + data
    return struct.pack('<HHIIIIII', 0x0001, hdr, hdr + len(body), len(strings), 0, flags, strings_start, 0) + body


def build_axml(tree):
    # collect strings: attribute names with resource ids first (resource map order)
    attr_names = []
    others = []

    def walk(node):
        tag, attrs, kids = node
        for (ns, name, typ, val) in attrs:
            if ns and name not in attr_names:
                attr_names.append(name)
        for (ns, name, typ, val) in attrs:
            if not ns and name not in others:
                others.append(name)
            if typ == T_STR and val not in others:
                others.append(val)
        if tag not in others:
            others.append(tag)
        for k in kids:
            walk(k)
    walk(tree)
    attr_names.sort(key=lambda n: ATTR_IDS[n])
    strings = attr_names + [s for s in others if s not in attr_names] + ['android', ANDROID_NS]
    idx = {s: i for i, s in enumerate(strings)}
    NONE = 0xFFFFFFFF
    chunks = [string_pool(strings)]
    rmap = b''.join(struct.pack('<I', ATTR_IDS[n]) for n in attr_names)
    chunks.append(struct.pack('<HHI', 0x0180, 8, 8 + len(rmap)) + rmap)
    chunks.append(struct.pack('<HHIIIII', 0x0100, 16, 24, 1, NONE, idx['android'], idx[ANDROID_NS]))

    def emit(node):
        tag, attrs, kids = node
        # android attrs sorted by resource id, plain attrs first
        attrs = sorted(attrs, key=lambda a: (1, ATTR_IDS[a[1]]) if a[0] else (0, 0))
        ab = b''
        for (ns, name, typ, val) in attrs:
            nsi = idx[ANDROID_NS] if ns else NONE
            if typ == T_STR:
                raw, data = idx[val], idx[val]
            else:
                raw, data = NONE, val & 0xFFFFFFFF
            ab += struct.pack('<IIIHBBI', nsi, idx[name], raw, 8, 0, typ, data)
        body = struct.pack('<IIHHHHHH', NONE, idx[tag], 20, 20, len(attrs), 0, 0, 0) + ab
        chunks.append(struct.pack('<HHIII', 0x0102, 16, 16 + len(body), 1, NONE) + body)
        for k in kids:
            emit(k)
        chunks.append(struct.pack('<HHIIIII', 0x0103, 16, 24, 1, NONE, NONE, idx[tag]))
    emit(tree)
    chunks.append(struct.pack('<HHIIIII', 0x0101, 16, 24, 1, NONE, idx['android'], idx[ANDROID_NS]))
    body = b''.join(chunks)
    return struct.pack('<HHI', 0x0003, 8, 8 + len(body)) + body


def build_arsc(pkg_name, icon_path):
    gpool = string_pool([icon_path], utf8=True)
    type_pool = string_pool(['mipmap'], utf8=True)
    key_pool = string_pool(['ic_launcher'], utf8=True)
    spec = struct.pack('<HHIBBHI', 0x0202, 16, 16 + 4, 1, 0, 0, 1) + struct.pack('<I', 0)
    config = struct.pack('<I', 64) + b'\0' * 60
    hdr_size = 20 + len(config)
    entries_start = hdr_size + 4
    entry = struct.pack('<HHI', 8, 0, 0) + struct.pack('<HBBI', 8, 0, T_STR, 0)
    type_chunk_size = entries_start + len(entry)
    typ = struct.pack('<HHIBBHII', 0x0201, hdr_size, type_chunk_size, 1, 0, 0, 1, entries_start) + config + struct.pack('<I', 0) + entry
    name16 = pkg_name.encode('utf-16-le').ljust(256, b'\0')
    pkg_hdr = 288
    type_off = pkg_hdr
    key_off = pkg_hdr + len(type_pool)
    pkg_body = type_pool + key_pool + spec + typ
    pkg = struct.pack('<HHII', 0x0200, pkg_hdr, pkg_hdr + len(pkg_body), 0x7f) + name16 + struct.pack('<IIIII', type_off, 1, key_off, 1, 0) + pkg_body
    assert len(pkg) == pkg_hdr + len(pkg_body)
    body = gpool + pkg
    return struct.pack('<HHII', 0x0002, 12, 12 + len(body), 1) + body


ASSETS = []

def main(icon_png, out_apk):
    A = True
    manifest = ('manifest', [
        (None, 'package', T_STR, 'com.kontra.game'),
        (A, 'versionCode', T_DEC, 4),
        (A, 'versionName', T_STR, '1.3'),
    ], [
        ('uses-sdk', [(A, 'minSdkVersion', T_DEC, 21), (A, 'targetSdkVersion', T_DEC, 29)], []),
        ('uses-permission', [(A, 'name', T_STR, 'android.permission.INTERNET')], []),
        ('uses-permission', [(A, 'name', T_STR, 'android.permission.ACCESS_NETWORK_STATE')], []),
        ('application', [
            (A, 'label', T_STR, 'Контра'),
            (A, 'icon', T_REF, 0x7f010000),
            (A, 'hardwareAccelerated', T_BOOL, 0xFFFFFFFF),
        ], [
            ('activity', [
                (A, 'name', T_STR, 'com.kontra.game.MainActivity'),
                (A, 'theme', T_REF, 0x01030007),
                (A, 'exported', T_BOOL, 0xFFFFFFFF),
                (A, 'screenOrientation', T_DEC, 6),
                (A, 'configChanges', T_HEX, 0x5b0),
                (A, 'label', T_STR, 'Контра'),
            ], [
                ('intent-filter', [], [
                    ('action', [(A, 'name', T_STR, 'android.intent.action.MAIN')], []),
                    ('category', [(A, 'name', T_STR, 'android.intent.category.LAUNCHER')], []),
                ]),
            ]),
        ]),
    ])
    icon_res = 'res/mipmap/ic_launcher.png'
    with zipfile.ZipFile(out_apk, 'w') as z:
        z.writestr(zipfile.ZipInfo('AndroidManifest.xml', (2024, 1, 1, 0, 0, 0)), build_axml(manifest), zipfile.ZIP_DEFLATED)
        zi = zipfile.ZipInfo('resources.arsc', (2024, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_STORED
        z.writestr(zi, build_arsc('com.kontra.game', icon_res))
        z.write('classes.dex', 'classes.dex', zipfile.ZIP_DEFLATED)
        for src, dst in ASSETS:
            z.write(src, 'assets/' + dst, zipfile.ZIP_DEFLATED)
        zi = zipfile.ZipInfo(icon_res, (2024, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_STORED
        z.writestr(zi, open(icon_png, 'rb').read())


if __name__ == '__main__':
    for a in sys.argv[3:]:
        src, dst = a.split('=')
        ASSETS.append((src, dst))
    main(sys.argv[1], sys.argv[2])
