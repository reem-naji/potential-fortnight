import os
import pyarrow as pa
import pyarrow.parquet as pq
import mssql_python
from tqdm import tqdm
# -----------------------------
# CONFIG
# -----------------------------


BATCH_SIZE = 250_000
ROW_GROUP_SIZE = 500_000
COMPRESSION = "zstd"
ROW_COUNTS = {
    "a": 16_155_725,
    "b": 16_155_725,
    **{f"D_{i:03d}": 1_000_000 for i in range(13)},
}
SINGLE_FILE = False  # recommended: False -> main_parquet/ directory

MAIN_TABLES = ["a", "b"] + [f"D_{i:03d}" for i in range(13)]
# D_000 ... D_012

# -----------------------------
# BUILD CANONICAL SCHEMA
# -----------------------------
MAIN_COLS = ["DIA"]

for i in range(1, 26):
    MAIN_COLS.extend([f"H{i}", f"ACTIVA_H{i}", f"REACTIVA_H{i}"])

MAIN_COLS.extend([
    "DE_MUNICIP",
    "FECHA_ALTA_STRO",
    "TARGET_TENENCIA_CUPS",
    "IDENTIFICADOR",
    "CNAE",
    "PRODUCTO",
    "MERCADO",
])

INT_COLS = set()
for i in range(1, 26):
    INT_COLS.update([f"H{i}", f"ACTIVA_H{i}", f"REACTIVA_H{i}"])

fields = []
for c in MAIN_COLS:
    if c == "IDENTIFICADOR":
        fields.append(pa.field(c, pa.int64()))
    elif c in INT_COLS:
        fields.append(pa.field(c, pa.int32()))
    else:
        fields.append(pa.field(c, pa.string()))

MAIN_SCHEMA = pa.schema(fields)


def select_sql(table: str) -> str:
    parts = []
    for c in MAIN_COLS:
        if c == "IDENTIFICADOR":
            parts.append(f"TRY_CAST(NULLIF([{c}], '') AS BIGINT) AS [{c}]")
        elif c in INT_COLS:
            parts.append(f"TRY_CAST(NULLIF([{c}], '') AS INT) AS [{c}]")
        else:
            parts.append(f"CAST([{c}] AS VARCHAR(50)) AS [{c}]")

    return f"SELECT {', '.join(parts)} FROM [{table}]"


def iter_main_batches(cur, table, batch_size, total_rows):
    cur.execute(select_sql(table))

    pbar = tqdm(total=total_rows, unit="rows", unit_scale=True, desc=table)

    while True:
        rows = cur.fetchmany(batch_size)
        if not rows:
            break

        pydict = {c: [] for c in MAIN_COLS}
        for row in rows:
            for c, v in zip(MAIN_COLS, row):
                pydict[c].append(v)

        pbar.update(len(rows))
        yield pa.Table.from_pydict(pydict, schema=MAIN_SCHEMA)

    pbar.close()


# -----------------------------
# CONNECT
# -----------------------------
conn = mssql_python.connect(os.getenv("MSSQL_CONNECTION_STRING"))
cur = conn.cursor()
cur.arraysize = BATCH_SIZE


# -----------------------------
# EXPORT MAIN DATA
# -----------------------------
if SINGLE_FILE:
    out_path = "main_data.parquet"
    writer = pq.ParquetWriter(
        out_path,
        MAIN_SCHEMA,
        compression=COMPRESSION,
        use_dictionary=True,
    )

    try:
        for table in MAIN_TABLES:
            print(f"Reading {table}...")
            for batch in iter_main_batches(cur, table, BATCH_SIZE, ROW_COUNTS[table]):
                writer.write_table(batch, row_group_size=ROW_GROUP_SIZE)
    finally:
        writer.close()

else:
    os.makedirs("main_parquet", exist_ok=True)

    for table in MAIN_TABLES:
        out_path = f"main_parquet/{table}.parquet"
        print(f"Reading {table} -> {out_path}")

        writer = pq.ParquetWriter(
            out_path,
            MAIN_SCHEMA,
            compression=COMPRESSION,
            use_dictionary=True,
        )

        try:
            for batch in iter_main_batches(cur, table, BATCH_SIZE, ROW_COUNTS[table]):
                writer.write_table(batch, row_group_size=ROW_GROUP_SIZE)
        finally:
            writer.close()


# -----------------------------
# EXPORT SMALL TABLES
# -----------------------------
SMALL_TABLES = [
    "all_actual_levels",
    "IDENTIFICADOR_92224",
    "IDENTIFICADOR_records_counts",
    "last_day_data_92224",
    "levels",
    "muncipility_province",
    "Municip_customers_count",
    "municiplity",
    "municiplity_IDENTIFICADORS_Count",
    "predicted_hours",
    "predicted_levels",
    "predicted_levels_24",
]

os.makedirs("small_parquet", exist_ok=True)

for table in SMALL_TABLES:
    print(f"Reading small table {table}...")
    cur.execute(f"SELECT * FROM [{table}]")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()

    if not rows:
        print(f"Skipping empty table: {table}")
        continue

    columns = list(zip(*rows))
    pydict = {c: list(col) for c, col in zip(cols, columns)}

    tbl = pa.Table.from_pydict(pydict)
    pq.write_table(
        tbl,
        f"small_parquet/{table}.parquet",
        compression=COMPRESSION,
    )

print("Done.")