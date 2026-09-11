import pyarrow.dataset as ds
import pyarrow.parquet as pq

dataset = ds.dataset("main_parquet", format="parquet")

with pq.ParquetWriter(
    "main_data.parquet",
    dataset.schema,
    compression="zstd",
    use_dictionary=True,
) as writer:
    for batch in dataset.to_batches(batch_size=500_000):
        writer.write_batch(batch, row_group_size=500_000)