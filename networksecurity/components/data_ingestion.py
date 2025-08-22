from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

from networksecurity.entity.config_entity import DataIngestionConfig
from networksecurity.entity.artifact_entity import DataIngestionArtifact

import os
import sys
import numpy as np
import pandas as pd
import pymongo
import certifi  # Add this import
from typing import List
from sklearn.model_selection import train_test_split

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")


class DataIngestion():
    def __init__(self, data_ingestion_config: DataIngestionConfig):
        try:
            self.data_ingestion_config = data_ingestion_config
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def export_collection_as_dataframe(self):
        try:
            database_name = self.data_ingestion_config.database_name
            collection_name = self.data_ingestion_config.collection_name

            # Fix SSL issue with certifi
            self.mongo_client = pymongo.MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            collection = self.mongo_client[database_name][collection_name]

            # Add debugging to check data retrieval
            document_count = collection.count_documents({})
            logging.info(f"Total documents in collection '{collection_name}': {document_count}")

            if document_count == 0:
                raise ValueError(f"No documents found in collection '{collection_name}' in database '{database_name}'")

            df = pd.DataFrame(list(collection.find()))
            logging.info(f"DataFrame created with shape: {df.shape}")

            if "_id" in df.columns.to_list():
                df = df.drop(columns=["_id"], axis=1)
            df.replace({"na": np.nan}, inplace=True)

            logging.info(f"Final DataFrame shape after preprocessing: {df.shape}")
            return df

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def export_data_into_feature_store(self, dataframe: pd.DataFrame):
        try:
            # Validate dataframe before processing
            if dataframe.empty:
                raise ValueError("Cannot export empty dataframe to feature store")

            feature_store_file_path = self.data_ingestion_config.feature_store_file_path
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path, exist_ok=True)
            dataframe.to_csv(feature_store_file_path, index=False, header=True)

            logging.info(f"Exported {len(dataframe)} rows to feature store")
            return dataframe

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def split_data_as_train_test(self, dataframe: pd.DataFrame):
        try:
            # Add validation before splitting
            if dataframe.empty:
                raise ValueError("Cannot split empty dataframe")

            if len(dataframe) < 2:
                raise ValueError(f"Dataset too small for splitting: {len(dataframe)} samples. Need at least 2 samples.")

            # Check if we have enough samples for the split ratio
            min_test_samples = max(1, int(len(dataframe) * self.data_ingestion_config.train_test_split_ratio))
            min_train_samples = len(dataframe) - min_test_samples

            if min_train_samples < 1:
                logging.warning(f"Adjusting split ratio due to small dataset size: {len(dataframe)} samples")
                # For very small datasets, just take 1 sample for test
                test_size = 1
            else:
                test_size = self.data_ingestion_config.train_test_split_ratio

            logging.info(f"Splitting {len(dataframe)} samples with test_size={test_size}")

            train_set, test_set = train_test_split(
                dataframe,
                test_size=test_size,
                random_state=42  # Add random state for reproducibility
            )

            logging.info(f"Train set size: {len(train_set)}, Test set size: {len(test_set)}")
            logging.info("Performed train test split on the dataframe")

            logging.info("Exited split_data_as_train_test method of Data_Ingestion class")

            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
            os.makedirs(dir_path, exist_ok=True)

            logging.info(f"Exporting train and test file path")

            train_set.to_csv(
                self.data_ingestion_config.training_file_path, index=False, header=True
            )
            test_set.to_csv(
                self.data_ingestion_config.test_file_path, index=False, header=True
            )
            logging.info(f"Exported train and test file path.")

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def initiate_data_ingestion(self):
        try:
            dataframe = self.export_collection_as_dataframe()

            # Validate dataframe before proceeding
            if dataframe.empty:
                raise ValueError("No data retrieved from MongoDB collection")

            dataframe = self.export_data_into_feature_store(dataframe)
            self.split_data_as_train_test(dataframe)

            dataingestionartifact = DataIngestionArtifact(
                trained_file_path=self.data_ingestion_config.training_file_path,
                test_file_path=self.data_ingestion_config.test_file_path
            )
            return dataingestionartifact

        except Exception as e:
            raise NetworkSecurityException(e, sys)
