import os
import re

def get_relative_path(from_path, to_path):
    rel = os.path.relpath(to_path, os.path.dirname(from_path))
    if not rel.startswith('.'):
        rel = './' + rel
    return rel

root_dir = 'amaima/frontend/src/app/core'
alias_base = 'amaima/frontend/src/app'

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(('.ts', '.tsx')):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()

            # Find all @/core/ imports
            new_content = content
            matches = re.findall(r"'@/core/(.*?)'", content)
            for m in set(matches):
                full_target_path = os.path.join(alias_base, 'core', m)
                rel_path = get_relative_path(filepath, full_target_path)
                new_content = new_content.replace(f"'@/core/{m}'", f"'{rel_path}'")

            if new_content != content:
                with open(filepath, 'w') as f:
                    f.write(new_content)
