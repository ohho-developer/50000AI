#!/usr/bin/env python
"""
Simple .mo file compiler using Python's msgfmt.py
"""
import os
import sys
from django.core.management.commands.compilemessages import Command

def main():
    """Run Django's compilemessages command programmatically"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main_project.settings.development')
    
    import django
    django.setup()
    
    command = Command()
    command.handle(verbosity=2, locale=['en'])

if __name__ == '__main__':
    # Try to compile using Python's built-in msgfmt module
    try:
        main()
    except Exception as e:
        print(f"Django compilemessages failed: {e}")
        print("\nTrying alternative method...")
        
        # Alternative: use Python's msgfmt.py directly
        import subprocess
        python_dir = os.path.dirname(sys.executable)
        msgfmt_path = os.path.join(python_dir, 'Tools', 'i18n', 'msgfmt.py')
        
        if os.path.exists(msgfmt_path):
            po_file = 'locale/en/LC_MESSAGES/django.po'
            mo_file = 'locale/en/LC_MESSAGES/django.mo'
            
            result = subprocess.run(
                [sys.executable, msgfmt_path, '-o', mo_file, po_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"Success! Created {mo_file}")
            else:
                print(f"Error: {result.stderr}")
        else:
            print(f"msgfmt.py not found at {msgfmt_path}")
            print("\nPlease install gettext and add it to PATH")
            print("Download from: https://mlocati.github.io/articles/gettext-iconv-windows.html")

