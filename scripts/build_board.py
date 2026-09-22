#!/usr/bin/env python3
"""Fill the bundled board template with scene summaries; never edits manuscripts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote


def build(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError('输出不能覆盖输入状态文件')
    state = json.loads(source.read_text(encoding='utf-8'))
    if not isinstance(state.get('project'), str) or not state['project'].strip():
        raise ValueError('需要 project 名称')
    if not isinstance(state.get('cards'), list):
        raise ValueError('需要 cards 数组')
    ids = set()
    for index, card in enumerate(state['cards']):
        if not isinstance(card.get('id'), str) or not card['id'] or card['id'] in ids:
            raise ValueError('卡片需要唯一 id')
        ids.add(card['id'])
        card.setdefault('kind', 'scene')
        if card['kind'] not in ('scene', 'gap'):
            raise ValueError('未知卡片类型')
        card.setdefault('title', card['id'])
        card.setdefault('x', 24 + index % 2 * 336)
        card.setdefault('y', 24 + index // 2 * 460)
        for key in ('x', 'y'):
            if not isinstance(card[key], (int, float)) or not 0 <= card[key] <= 100000:
                raise ValueError('坐标必须是有效非负数')
        if card['kind'] == 'scene' and card.get('file'):
            path = (source.parent / card['file']).resolve()
            card['sourceUrl'] = quote(os.path.relpath(path, output.parent), safe='/')
    state.setdefault('version', 1)
    state.setdefault('timeline', [])
    state.setdefault('selected', None)
    state.setdefault('note', '')
    if state['version'] != 1 or not isinstance(state['note'], str):
        raise ValueError('无效状态版本或备注')
    order = state['timeline']
    if not isinstance(order, list) or any(not isinstance(i, str) for i in order) or len(set(order)) != len(order) or not set(order) <= ids:
        raise ValueError('时间线包含重复或不存在的卡片')
    if state['selected'] is not None and state['selected'] not in ids:
        raise ValueError('选中的卡片不存在')
    state.setdefault('projectId', hashlib.sha256((str(source.parent) + '\0' + state['project']).encode()).hexdigest()[:24])
    data = json.dumps(state, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = Path(__file__).resolve().parent.parent / 'assets/scene-board.html'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(template.read_text(encoding='utf-8').replace('__SCENE_DATA__', data), encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', required=True, help='JSON状态文件；card.file相对此文件所在目录')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(build(args.state, args.output))
