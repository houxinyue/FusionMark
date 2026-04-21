import re

for enc in ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'cp1252']:
    try:
        with open('index.html', 'r', encoding=enc) as f:
            html = f.read()
        print('Read with', enc)
        break
    except Exception as e:
        print('Failed', enc, e)
        continue

html = re.sub(r'\s*fragment\b', '', html)
html = re.sub(r'class="\s+', 'class="', html)
html = re.sub(r'\s+"', '"', html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('fragment count:', len(re.findall(r'fragment', html)))
print('Done')
