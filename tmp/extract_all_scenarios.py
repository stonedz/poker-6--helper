import json
import math
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

from PIL import Image


workspace = Path('/home/stonedz/work/poker_test')
json_path = workspace / 'src/shortdeck_cli/data/preflop_scenarios.json'
out_path = workspace / 'tmp/preflop_scenarios.generated.json'
img_dir = workspace / 'tmp/all_charts'
img_dir.mkdir(parents=True, exist_ok=True)
ref_img_path = workspace / 'tmp/utg_rfi.png'
ref_ocr_path = workspace / 'tmp/utg_ocr.json'

label_to_src = {
    '1 - UTG RFI': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/wn9wlskjv755pw5jxuz8fgf29hta',
    '2 - MP RFI': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/vgbdkhbxvvzj0y64xk5p44ff7rf1',
    '3 - HJ RFI': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/0509kvqs3yu3zr1z72916c1vdfyn',
    '4 - CO RFI': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/yof0zl5cfqhodzk99j6at1lwduht',
    '5 - MP vs UTG Limp': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/papqalk2vthvzxn64grv6qydugvk',
    '6 - HJ vs UTG Limp': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/v9jv6hjcvibfvb9jy1c9ey8m66qs',
    '7 - CO vs UTG Limp': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/2rqdplakmv0shbv9wzzgeln5418u',
    '8 - BTN vs UTG Limp': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/ni1zn8656hpqrxekk3a35vwhzi5w',
    '9 - HJ vs MP Limp': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/hsywgfikmcz5uf4j6gix6qmkz7s9',
    '10 - CO vs MP Limp': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/llfezqw3c9wx51fhvrdmx9azhq2o',
    '11 - BTN vs MP Limp': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/gvml2mzt9uxuxeqnk6rcowsquq41',
    '12 - CO vs HJ Limp': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/81bznwbonchz7z3cs2sj2qcutm8f',
    '13 - BTN vs HJ Limp': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/av2hgfk97q1ac6n9dm9n5urlxjwk',
    '14 - BTN vs CO Limp': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/un4woxuu4zbva311av1khl08klie',
    '15 - MP vs UTG All in': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/1o08am2pg8l4n6o56df4mv9xctxb',
    '16 - HJ vs UTG All in': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/sdqa31stqpr4wqp7y5knxm4n04kx',
    '17 - CO vs UTG All in': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/6dpknb35bvay3ehj2ckwtk80a8ti',
    '18 - BTN vs UTG All in': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/goztbho1p21chkeymq40aqu7u2yi',
    '19 - HJ vs MP All in': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/9wvpolydnwo702eigu29qsnggvrr',
    '20 - CO vs MP All in': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/l6eywh9dgyefpb6uy1cw2qrby1oj',
    '21 - BTN vs MP All in': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/03rnlmdgf8yp80cpk4jgjbm462ps',
    '22 - CO vs HJ All in': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/ilvm538cjzt0i37ohnxe43k93s7k',
    '23- BTN vs HJ All in': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/yna6s4y98lk3893xrv1u8igi7l8c',
    '24 - BTN vs CO All in': 'https://sdf23r3d.s3.us-east-1.amazonaws.com/yb8osi2h89wu71f65n3kd1v2bv76',
}


def norm_label(value: str) -> str:
    return re.sub(r'\s*-\s*', '-', value.strip())


def dist(c1, c2):
    return math.sqrt(sum((a - b) * (a - b) for a, b in zip(c1, c2)))


def is_noise(c):
    r, g, b = c
    if r < 30 and g < 55 and b < 80:
        return True
    if r > 220 and g > 220 and b > 220:
        return True
    if r < 20 and g < 20 and b < 20:
        return True
    return False


def kmeans_1d(values, k=9, iters=60):
    values = sorted(values)
    mins, maxs = values[0], values[-1]
    centers = [mins + (maxs - mins) * i / (k - 1) for i in range(k)]
    for _ in range(iters):
        buckets = [[] for _ in range(k)]
        for value in values:
            idx = min(range(k), key=lambda i: abs(value - centers[i]))
            buckets[idx].append(value)
        new = [(sum(bucket) / len(bucket) if bucket else centers[i]) for i, bucket in enumerate(buckets)]
        if all(abs(a - b) < 1e-4 for a, b in zip(centers, new)):
            return sorted(new)
        centers = new
    return sorted(centers)


def derive_reference_bounds():
    ranks = list('AKQJT9876')
    hand_pattern = re.compile(r'^[AKQJT9876]{2}[so]?$')

    if not ref_img_path.exists():
        urllib.request.urlretrieve(label_to_src['1 - UTG RFI'], ref_img_path)

    if not ref_ocr_path.exists():
        raise RuntimeError('Reference OCR file missing: tmp/utg_ocr.json. Re-run UTG extraction first.')

    ocr = json.loads(ref_ocr_path.read_text())
    lines = ocr['ParsedResults'][0].get('TextOverlay', {}).get('Lines', [])
    points = []
    for line in lines:
        words = line.get('Words', [])
        if not words:
            continue
        text = ''.join(word.get('WordText', '') for word in words).replace('0', 'o')
        text = text.replace('S', 's').replace('O', 'o')
        if len(text) >= 2:
            hand = text[:2].upper() + (text[2:3].lower() if len(text) >= 3 else '')
        else:
            hand = text
        if hand_pattern.match(hand):
            left = min(word['Left'] for word in words)
            top = min(word['Top'] for word in words)
            right = max(word['Left'] + word['Width'] for word in words)
            bottom = max(word['Top'] + word['Height'] for word in words)
            points.append((hand, (left + right) / 2, (top + bottom) / 2))

    if len(points) < 55:
        raise RuntimeError(f'Reference OCR has insufficient hand labels: {len(points)}')

    image = Image.open(ref_img_path)
    width, height = image.size
    x_centers = kmeans_1d([point[1] for point in points], 9)
    y_centers = kmeans_1d([point[2] for point in points], 9)
    x_bounds = [0] * 10
    y_bounds = [0] * 10
    for i in range(1, 9):
        x_bounds[i] = (x_centers[i - 1] + x_centers[i]) / 2
        y_bounds[i] = (y_centers[i - 1] + y_centers[i]) / 2
    x_bounds[0] = max(0, x_centers[0] - (x_centers[1] - x_centers[0]) / 2)
    x_bounds[9] = min(width - 1, x_centers[-1] + (x_centers[-1] - x_centers[-2]) / 2)
    y_bounds[0] = max(0, y_centers[0] - (y_centers[1] - y_centers[0]) / 2)
    y_bounds[9] = min(height - 1, y_centers[-1] + (y_centers[-1] - y_centers[-2]) / 2)
    return x_bounds, y_bounds


def build_hand_actions(img_path: Path, x_bounds, y_bounds):
    ranks = list('AKQJT9876')
    prototypes = {
        'all-in': (164, 22, 26),
        'call': (64, 145, 108),
        'fold': (39, 125, 161),
        'ante': (194, 134, 60),
    }

    image = Image.open(img_path).convert('RGB')
    pixels = image.load()
    width, height = image.size

    actions_by_hand = {}
    for row_idx, rank_row in enumerate(ranks):
        for col_idx, rank_col in enumerate(ranks):
            if row_idx == col_idx:
                hand = rank_row + rank_col
            elif col_idx > row_idx:
                hand = rank_row + rank_col + 's'
            else:
                hand = rank_col + rank_row + 'o'

            x0 = int(x_bounds[col_idx] + 8)
            x1 = int(x_bounds[col_idx + 1] - 8)
            y0 = int(y_bounds[row_idx] + 8)
            y1 = int(y_bounds[row_idx + 1] - 8)
            if x1 <= x0 or y1 <= y0:
                actions_by_hand[hand] = 'fold'
                continue

            counts = defaultdict(int)
            total = 0
            for y in range(y0, y1, 1):
                for x in range(x0, x1, 1):
                    color = pixels[x, y]
                    if is_noise(color):
                        continue
                    action = min(prototypes, key=lambda a: dist(color, prototypes[a]))
                    if dist(color, prototypes[action]) > 85:
                        continue
                    counts[action] += 1
                    total += 1

            if total == 0:
                actions_by_hand[hand] = 'fold'
                continue

            ratios = {action: (counts[action] * 100.0 / total) for action in ['all-in', 'call', 'fold', 'ante'] if counts[action] > 0}
            ratios = {action: value for action, value in ratios.items() if value >= 0.3}
            ratio_sum = sum(ratios.values())
            if ratio_sum <= 0:
                actions_by_hand[hand] = 'fold'
                continue
            ratios = {action: (value * 100.0 / ratio_sum) for action, value in ratios.items()}
            ratios = {action: round(value, 1) for action, value in ratios.items() if value >= 0.3}
            rounded_sum = sum(ratios.values())
            ratios = {action: round(value * 100.0 / rounded_sum, 1) for action, value in ratios.items()}

            if len(ratios) == 1:
                actions_by_hand[hand] = next(iter(ratios.keys()))
                continue

            mixed = {}
            for action, value in sorted(ratios.items(), key=lambda item: item[1], reverse=True):
                mixed[action] = int(round(value)) if abs(value - round(value)) < 0.05 else value
            actions_by_hand[hand] = mixed

    return actions_by_hand


def main():
    data = json.loads(json_path.read_text())
    normalized_sources = {norm_label(label): source for label, source in label_to_src.items()}
    x_bounds, y_bounds = derive_reference_bounds()

    processed = 0
    for scenario_key, scenario in data.get('scenarios', {}).items():
        label = scenario.get('label', '').strip()
        source_url = normalized_sources.get(norm_label(label))
        if not source_url:
            print('SKIP no image mapping:', scenario_key, label)
            continue

        slug = re.sub(r'[^a-z0-9]+', '_', scenario_key.lower()).strip('_')
        image_path = img_dir / f'{slug}.png'
        if not image_path.exists():
            urllib.request.urlretrieve(source_url, image_path)

        scenario['hand_actions'] = build_hand_actions(image_path, x_bounds, y_bounds)
        scenario['notes'] = 'Extracted from chart image via OCR + color bucketing; verify against source before production use.'
        processed += 1
        print('DONE', processed, scenario_key)

    out_path.write_text(json.dumps(data, indent=2))
    print('WROTE', out_path)


if __name__ == '__main__':
    main()
