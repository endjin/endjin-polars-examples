# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.12"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

import logging

from builtin.internal_classes.data_wrangler import DataWrangler, OneLakeFabricDataSource

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

_log_format = "%(asctime)s %(name)s %(levelname)s %(message)s"
_formatter = logging.Formatter(fmt=_log_format)
for _handler in logging.getLogger().handlers:
    _handler.setFormatter(_formatter)
logging.getLogger().setLevel(logging.INFO)

logger = logging.getLogger(name="polars_benchmark_notebook")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

data_source = OneLakeFabricDataSource(
    workspace_name="SQLBits 2026 Demo",
    lakehouse_name="HousePriceAnalytics",
    file_pattern="land_registry_data/pp-*.csv",
    column_names=DataWrangler.COLUMN_NAMES,
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

wrangler = DataWrangler(data_source)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

wrangler.process_to_silver()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
