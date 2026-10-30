import json

import main

print(json.dumps(main.ejecutar({}), ensure_ascii=False)[:2000])
