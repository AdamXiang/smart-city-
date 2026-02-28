# 1. 以 Bitnami 原廠的 3.5.1 作為基底
FROM bitnamilegacy/spark:3.5.1

# 2. 切換成最高權限的大老闆 (root) 來安裝軟體
USER root

# 3. 解決時區警告：告訴高鐵忽略時區差異
ENV PYARROW_IGNORE_TIMEZONE=1

# 4. 把所有你需要的 Python 員工一次請齊！
# ⚠️ 關鍵：強制限制 numpy 版本必須小於 2.0，避免跟 Spark 打架！
RUN pip install --no-cache-dir "pandas<2.2.0" pyarrow boto3 kafka-python "numpy<2.0.0"

# 5. 裝完後，乖乖把權限還給原本的 Spark 員工
USER 1001