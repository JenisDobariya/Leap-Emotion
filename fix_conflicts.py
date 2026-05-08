import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Resolve all merge conflicts by keeping HEAD (ours) version
pattern = r'<<<<<<<[^\n]*\n(.*?)=======\n.*?>>>>>>>[^\n]*\n'
resolved = re.sub(pattern, r'\1', content, flags=re.DOTALL)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(resolved)

# Verify no conflicts remain
remaining = re.findall(r'<<<<<<<', resolved)
print(f"Conflicts resolved. Remaining markers: {len(remaining)}")
