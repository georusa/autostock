# 5个你绝对用得上的 Python 数据处理技巧

> 让你的数据分析工作效率提升10倍

## 1. 一行代码读取多个CSV

```python
import pandas as pd
# 读取一个文件夹里所有CSV
dfs = [pd.read_csv(f) for f in glob.glob("data/*.csv")]
# 合并成一个DataFrame
result = pd.concat(dfs, ignore_index=True)
```

我知道有人会用 `for` 循环一个个读，但 `glob + concat` 才是正解。

## 2. 分布式API请求（再也不怕429）

```python
import httpx
from concurrent.futures import ThreadPoolExecutor

urls = ["https://api.example.com/data/1", ...]
with ThreadPoolExecutor(max_workers=10) as ex:
    results = list(ex.map(lambda u: httpx.get(u).json(), urls))
```

## 3. 一键生成HTML报告

```python
# 用模板+变量自动生成
from jinja2 import Template
report = Template(HTML_TEMPLATE).render(data=df.to_dict())
with open("report.html", "w") as f:
    f.write(report)
```

## 4. 把Excel当数据库查

```python
import pandas as pd
df = pd.read_excel("sales.xlsx")
# 按条件筛选
q1_top = df[df["季度"] == "Q1"].nlargest(10, "销售额")
```

## 5. 自动发送邮件报告

```python
import smtplib
from email.mime.text import MIMEText
# 5行代码搞定自动日报
```

---

💡 **需要这些脚本的完整版？** 我打包成了一个工具集，付费即可获得完整代码 + 技术支持。

📦 Python自动化处理工具包：¥49.9（含10+实用脚本）

🔗 购买：https://paypal.me/netmstar

#Python #自动化 #效率工具 #数据分析
