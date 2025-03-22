import csv
import json
import pandas as pd
import argparse


def convert_to_annotation_json(input_file, output_file):
    """
    Converts CSV or XLS data to the annotation.json format.

    Args:
        input_file (str): Path to the input CSV or XLS file.
        output_file (str): Path to the output JSON file.
    """

    if input_file.endswith(".csv"):
        try:
            with open(input_file, "r") as csvfile:
                reader = csv.DictReader(csvfile)
                data = list(reader)
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return
    elif input_file.endswith(".xls") or input_file.endswith(".xlsx"):
        try:
            df = pd.read_excel(input_file)
            data = df.to_dict("records")
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return
    else:
        print("Unsupported file format. Please use CSV or XLS/XLSX.")
        return

    annotation_data = {}
    for row in data:
        video_name = row.get("video name") or row.get("video_name") or row.get("video")
        start_time = row.get("start time") or row.get("start_time") or row.get("start")
        end_time = row.get("end time") or row.get("end_time") or row.get("end")

        if not video_name or not start_time or not end_time:
            print(f"Skipping row due to missing data: {row}")
            continue

        try:
            start_time = float(start_time)
            end_time = float(end_time)
        except ValueError:
            print(f"Skipping row due to invalid time format: {row}")
            continue

        if video_name not in annotation_data:
            annotation_data[video_name] = []

        annotation_data[video_name].append(
            {"start_time": start_time, "end_time": end_time}
        )

    try:
        with open(output_file, "w") as jsonfile:
            json.dump(annotation_data, jsonfile, indent=4)
        print(f"Successfully converted data to {output_file}")
    except Exception as e:
        print(f"Error writing JSON file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert CSV or XLS data to annotation.json format."
    )
    parser.add_argument("--in-file", help="Path to the input CSV or XLS file")
    args = parser.parse_args()

    convert_to_annotation_json(args.in_file, "backend/data/annotation.json")
