with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('id="searchId"')
print('searchId line:', text[:pos].count('\n') + 1)
