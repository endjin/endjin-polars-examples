import requests
import fsspec

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LandRegstryImporter:

    HOUSE_PRICE_BASE_URL = "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/"

    # Each file is approximately 100MB in size.  Change the number of years to control the total data size.
    def __init__(self, raw_data_download_path: str, storage_options: dict, number_of_years: int = 5):
        self.raw_data_download_path = raw_data_download_path
        self.storage_options = storage_options
        self.number_of_years = number_of_years

        self.list_of_files = [f"pp-{year}.csv" for year in range(2025, 2025 - number_of_years, -1)]

    def download_land_registry_data(self):

        logger.info("Starting download of Land Registry data...")
        
        logger.info(f"Number of files to download: {len(self.list_of_files)}")

        for file_number, file_name in enumerate(self.list_of_files):
        
            remote_file_url = f"{self.HOUSE_PRICE_BASE_URL}{file_name}"
            path_to_save_file = self.raw_data_download_path + "/" + file_name

            # Download the CSV file with streaming enabled to avoid OOM on limited memory
            with requests.get(remote_file_url, stream=True) as response:
                response.raise_for_status()  # Ensure we notice bad responses

                # fsspec automatically handles the protocol (file:// versus abfss://) based on the source_path
                with fsspec.open(path_to_save_file, mode='wb', **self.storage_options) as f:
                    # Write in 1MB chunks
                    for chunk in response.iter_content(chunk_size=1024*1024):
                        f.write(chunk)

            logger.info(f"Downloaded file {file_number + 1} of {len(self.list_of_files)}: filename {file_name} to: {path_to_save_file}")
        logger.info("Completed downloading Land Registry data.")
