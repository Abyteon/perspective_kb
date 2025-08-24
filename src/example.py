import polars as pl

# 读原始数据
df = pl.read_csv("data/example.csv")

# 提取时间信号并生成 timestamp_ms
time_df = (
    df.filter(pl.col("signal_name").str.starts_with("Time"))
    .pivot(
        values="signal_value", index="vid", on="signal_name", aggregate_function="first"
    )
    .with_columns(
        [
            pl.datetime(
                year=pl.col("TimeYear"),
                month=pl.col("TimeMonth"),
                day=pl.col("TimeDay"),
                hour=pl.col("TimeHour"),
                minute=pl.col("TimeMinute"),
                second=pl.col("TimeSecond"),
            ).alias("real_time")
        ]
    )
    .with_columns((pl.col("real_time").cast(pl.Int64) // 1000).alias("timestamp_ms"))
    .select(["vid", "timestamp_ms"])
)

# 为每个 vid 生成 1 分钟的连续时间序列（按秒）
offsets = pl.Series(range(0, 60 * 1000, 1000))
minute_df = (
    time_df.join(offsets.to_frame("offset_ms"), how="cross")
    .with_columns((pl.col("timestamp_ms") + pl.col("offset_ms")).alias("timestamp_ms"))
    .select(["vid", "timestamp_ms"])
    .sort(["vid", "timestamp_ms"])
)


# 提取业务信号并排序
biz_df = df.filter(~pl.col("signal_name").str.starts_with("Time")).sort(
    ["vid", "timestamp_ms"]
)

# 给两个表都加上 row_number
minute_df = minute_df.with_columns(pl.arange(0, pl.len()).over("vid").alias("row_id"))
biz_df = biz_df.with_columns(
    pl.arange(0, pl.len()).over(["vid", "signal_name"]).alias("row_id")
)

print("minute_df: ", minute_df)
print("biz_df: ", biz_df)

# 按 vid + row_id 对齐
aligned = biz_df.join(minute_df, on=["vid", "row_id"], how="inner")
print("aligned: ", aligned)

# 用 time_df 的 timestamp 覆盖
result = aligned.select(
    ["vid", "timestamp_ms_right", "signal_name", "signal_value"]
).rename({"timestamp_ms_right": "timestamp"})
print(result)
