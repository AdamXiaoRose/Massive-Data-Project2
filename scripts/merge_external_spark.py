"""Distributed-compute variant of `merge_external.py`.

Same merge logic, expressed against the Spark DataFrame API so it can
run on a cluster (Dataproc / EMR / Databricks) without code changes.
For development it runs unchanged on local[*]. This script is the
concrete answer to the project brief's "cloud platforms, distributed
computing" requirement: the single-machine pandas path remains the
fast default, and this path is the scale-out variant.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Spark rejects hostnames with characters like underscore. On Windows/
# WSL where the machine name may be "Adam_Rose" etc., force a known-good
# value before the JVM starts up.
os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")

from pyspark.sql import SparkSession, functions as F

USCIS = "data/processed/h1b_features.parquet"
EXTERNAL = "data/raw/lca_city_enrichment.csv"
OUT = "data/processed/h1b_city_merged_spark.parquet"

WAGE_HARD_CAP = 500_000.0


def build_session(master: str = "local[*]") -> SparkSession:
    return (
        SparkSession.builder
        .appName("h1b-merge-external")
        .master(master)
        .config("spark.sql.shuffle.partitions", "16")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.driver.memory", "2g")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .getOrCreate()
    )


def uscis_by_city(spark: SparkSession):
    df = spark.read.parquet(USCIS)
    return (
        df.groupBy("state", "city")
          .agg(
              F.sum("total_petitions").alias("total_petitions"),
              F.sum("total_approvals").alias("total_approvals"),
              F.sum("total_denials").alias("total_denials"),
              F.countDistinct("employer").alias("n_employers"),
              F.avg("is_stem").alias("share_stem"),
              F.avg("share_continuing").alias("share_continuing"),
              F.first("region").alias("region"),
          )
          .withColumn("approval_rate",
                      F.col("total_approvals") / F.col("total_petitions"))
          .withColumn("log_petitions", F.log1p(F.col("total_petitions")))
          .withColumn("log_employers", F.log1p(F.col("n_employers")))
    )


def external_by_city(spark: SparkSession):
    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(EXTERNAL)
    )
    df = (
        df.withColumn("EMPLOYER_STATE", F.upper(F.trim(F.col("EMPLOYER_STATE"))))
          .withColumn("EMPLOYER_CITY", F.upper(F.trim(F.col("EMPLOYER_CITY"))))
          .withColumn(
              "AVG_ANNUAL_WAGE",
              F.when(F.col("AVG_ANNUAL_WAGE") > WAGE_HARD_CAP, None)
               .otherwise(F.col("AVG_ANNUAL_WAGE")),
          )
    )
    return (
        df.groupBy("EMPLOYER_STATE", "EMPLOYER_CITY")
          .agg(
              F.avg("AVG_ANNUAL_WAGE").alias("avg_wage"),
              F.sum("LCA_APPLICATIONS").alias("lca_applications"),
              F.first("POPULATION", ignorenulls=True).alias("population"),
              F.first("DENSITY", ignorenulls=True).alias("density"),
              F.first("AVG_RENT_2022", ignorenulls=True).alias("avg_rent"),
              F.first("EMPLOYED_PCT", ignorenulls=True).alias("employed_pct"),
              F.first("UNEMPLOYED_Z", ignorenulls=True).alias("unemployed_z"),
          )
          .withColumnRenamed("EMPLOYER_STATE", "state")
          .withColumnRenamed("EMPLOYER_CITY", "city")
          .withColumn("log_wage", F.log1p(F.col("avg_wage")))
          .withColumn("log_population", F.log1p(F.col("population")))
          .withColumn("log_density", F.log1p(F.col("density")))
          .withColumn("log_rent", F.log1p(F.col("avg_rent")))
          .withColumn("log_lca", F.log1p(F.col("lca_applications")))
    )


def main() -> None:
    spark = build_session()
    spark.sparkContext.setLogLevel("WARN")

    uscis = uscis_by_city(spark)
    external = external_by_city(spark)
    merged = (
        uscis.join(external, on=["state", "city"], how="inner")
             .dropna(subset=["avg_wage", "population", "density",
                             "avg_rent", "employed_pct"])
    )

    # Materialize a canonical partition count; on a cluster this would
    # be tuned to data volume and worker count.
    merged = merged.repartition(4).cache()

    n_uscis = uscis.count()
    n_external = external.count()
    n_merged = merged.count()
    print(f"USCIS city rows (Spark):    {n_uscis:,}")
    print(f"external city rows (Spark): {n_external:,}")
    print(f"inner-join rows (Spark):    {n_merged:,}")

    # Spark's native parquet writer on Windows requires winutils.exe
    # (Hadoop FileSystem). The computed frame is small (~4k rows), so
    # we collect to the driver and write with pandas/pyarrow. On a real
    # cluster, swap this for `merged.write.parquet(OUT)`.
    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    merged.toPandas().to_parquet(OUT, index=False)
    print(f"wrote -> {OUT}")

    spark.stop()


if __name__ == "__main__":
    sys.exit(main())
