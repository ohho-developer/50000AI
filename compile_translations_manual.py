#!/usr/bin/env python
"""
수동으로 .po 파일을 .mo 파일로 컴파일하는 스크립트
gettext 도구가 없는 환경에서 사용

Usage:
    python compile_translations_manual.py
"""

import os
import struct
import array


def parse_po_file(po_file):
    """
    .po 파일을 파싱하여 msgid와 msgstr 쌍을 추출합니다.
    """
    translations = {}
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False
    
    with open(po_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 주석이나 빈 줄은 건너뛰기
            if not line or line.startswith('#'):
                # msgid/msgstr 블록이 끝났을 때 저장
                if current_msgid is not None and current_msgstr is not None:
                    if current_msgid and current_msgstr:  # 빈 문자열 제외
                        translations[current_msgid] = current_msgstr
                    current_msgid = None
                    current_msgstr = None
                    in_msgid = False
                    in_msgstr = False
                continue
            
            # msgid 시작
            if line.startswith('msgid "'):
                if current_msgid is not None and current_msgstr is not None:
                    if current_msgid and current_msgstr:
                        translations[current_msgid] = current_msgstr
                current_msgid = line[7:-1]  # 'msgid "' 와 마지막 '"' 제거
                current_msgstr = None
                in_msgid = True
                in_msgstr = False
            
            # msgstr 시작
            elif line.startswith('msgstr "'):
                current_msgstr = line[8:-1]  # 'msgstr "' 와 마지막 '"' 제거
                in_msgid = False
                in_msgstr = True
            
            # 연속된 문자열 (다음 줄에 이어지는 경우)
            elif line.startswith('"') and line.endswith('"'):
                content = line[1:-1]  # 앞뒤 '"' 제거
                if in_msgid and current_msgid is not None:
                    current_msgid += content
                elif in_msgstr and current_msgstr is not None:
                    current_msgstr += content
        
        # 마지막 항목 처리
        if current_msgid is not None and current_msgstr is not None:
            if current_msgid and current_msgstr:
                translations[current_msgid] = current_msgstr
    
    return translations


def generate_mo_file(translations, mo_file):
    """
    번역 딕셔너리를 .mo 파일 형식으로 생성합니다.
    GNU gettext .mo 파일 형식을 따릅니다.
    """
    # 번역 쌍을 정렬
    keys = sorted(translations.keys())
    offsets = []
    ids = []
    strs = []
    
    for key in keys:
        ids.append(key.encode('utf-8'))
        strs.append(translations[key].encode('utf-8'))
    
    # .mo 파일 헤더 생성
    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + sum(len(k) + 1 for k in ids)
    
    # 키와 값의 오프셋 계산
    koffsets = []
    voffsets = []
    
    offset = keystart
    for key in ids:
        koffsets.append((len(key), offset))
        offset += len(key) + 1
    
    offset = valuestart
    for value in strs:
        voffsets.append((len(value), offset))
        offset += len(value) + 1
    
    # .mo 파일 작성
    with open(mo_file, 'wb') as f:
        # Magic number (little-endian)
        f.write(struct.pack('I', 0x950412de))
        
        # Version
        f.write(struct.pack('I', 0))
        
        # Number of entries
        f.write(struct.pack('I', len(keys)))
        
        # Offset of table with original strings
        f.write(struct.pack('I', 7 * 4))
        
        # Offset of table with translation strings
        f.write(struct.pack('I', 7 * 4 + len(keys) * 8))
        
        # Size of hashing table (0 = no hash table)
        f.write(struct.pack('I', 0))
        
        # Offset of hashing table (unused)
        f.write(struct.pack('I', 0))
        
        # Write the offset tables
        for length, offset in koffsets:
            f.write(struct.pack('I', length))
            f.write(struct.pack('I', offset))
        
        for length, offset in voffsets:
            f.write(struct.pack('I', length))
            f.write(struct.pack('I', offset))
        
        # Write the keys
        for key in ids:
            f.write(key)
            f.write(b'\x00')
        
        # Write the values
        for value in strs:
            f.write(value)
            f.write(b'\x00')


def compile_po_to_mo(po_file, mo_file):
    """
    .po 파일을 .mo 파일로 컴파일합니다.
    """
    print(f"Reading {po_file}...")
    translations = parse_po_file(po_file)
    
    print(f"Found {len(translations)} translations")
    
    print(f"Generating {mo_file}...")
    generate_mo_file(translations, mo_file)
    
    print(f"Successfully compiled to {mo_file}")
    
    # 파일 크기 확인
    size = os.path.getsize(mo_file)
    print(f"File size: {size:,} bytes")


def main():
    """
    메인 함수: locale 디렉토리의 모든 .po 파일을 컴파일합니다.
    """
    print("Django Translation Compiler")
    print("=" * 50)
    
    # locale 디렉토리 찾기
    locale_dirs = []
    
    # 프로젝트 루트의 locale 디렉토리
    if os.path.exists('locale'):
        locale_dirs.append('locale')
    
    # 각 앱의 locale 디렉토리
    for item in os.listdir('.'):
        locale_path = os.path.join(item, 'locale')
        if os.path.isdir(locale_path):
            locale_dirs.append(locale_path)
    
    if not locale_dirs:
        print("No locale directories found!")
        return
    
    total_compiled = 0
    
    # 각 locale 디렉토리 처리
    for locale_dir in locale_dirs:
        print(f"\nProcessing {locale_dir}/")
        
        # 각 언어 디렉토리 처리
        for lang in os.listdir(locale_dir):
            lang_path = os.path.join(locale_dir, lang)
            lc_messages = os.path.join(lang_path, 'LC_MESSAGES')
            
            if not os.path.isdir(lc_messages):
                continue
            
            # .po 파일 찾기
            po_file = os.path.join(lc_messages, 'django.po')
            
            if not os.path.exists(po_file):
                continue
            
            mo_file = os.path.join(lc_messages, 'django.mo')
            
            print(f"\nLanguage: {lang}")
            try:
                compile_po_to_mo(po_file, mo_file)
                total_compiled += 1
            except Exception as e:
                print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print(f"Compilation complete! Total: {total_compiled} file(s)")


if __name__ == '__main__':
    main()

