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

            def replace_alias(match):
                alias_path = match.group(1)
                full_target_path = os.path.join(alias_base, alias_path)

                # Check if target exists as a file or directory
                if os.path.exists(full_target_path + '.ts') or                    os.path.exists(full_target_path + '.tsx') or                    os.path.exists(os.path.join(full_target_path, 'index.ts')) or                    os.path.exists(os.path.join(full_target_path, 'index.tsx')) or                    os.path.isdir(full_target_path):
                    rel_path = get_relative_path(filepath, full_target_path)
                    return f"import {{ match.group(2) }} from '{rel_path}'"
                return match.group(0)

            # Simple regex for import { ... } from '@/...'
            # This is tricky because of multiple import styles.
            # I'll just do a simpler string replacement for @/ to relative paths where appropriate.

            lines = content.split('\n')
            new_lines = []
            for line in lines:
                match = re.search(r"from '@/(.*?)'", line)
                if match:
                    alias_path = match.group(1)
                    full_target_path = os.path.join(alias_base, alias_path)

                    # We only want to relativize if the target is also in src/app/core
                    if alias_path.startswith('core/'):
                        rel_path = get_relative_path(filepath, full_target_path)
                        line = line.replace(f"@/{alias_path}", rel_path)
                    elif alias_path == 'types' or alias_path.startswith('types/'):
                         # Map @/types to src/types (not under app)
                         # Wait, I have src/types AND src/app/core/types.
                         # Most things in core should use src/app/core/types.
                         # My tsconfig maps @/* to src/app/*
                         # So @/core/types is src/app/core/types
                         rel_path = get_relative_path(filepath, os.path.join(alias_base, 'core/types'))
                         line = line.replace("@/types", rel_path)

                new_lines.append(line)

            new_content = '\n'.join(new_lines)
            if new_content != content:
                with open(filepath, 'w') as f:
                    f.write(new_content)
