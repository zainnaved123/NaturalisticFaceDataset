from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(
    app, resources={r"/*": {"origins": "http://localhost:3000"}}
)  # Enable CORS for specific origin

# Load the dataset
DATASET_PATH = "output_clips"
JSON_PATH = os.path.join(DATASET_PATH, "clip_details.json")


def load_dataset():
    with open(JSON_PATH, "r") as file:
        return json.load(file)


dataset = load_dataset()


# Endpoint to filter the dataset
@app.route("/filter", methods=["GET"])
def filter_dataset():
    gender = request.args.get("gender")
    race = request.args.get("race")
    age = request.args.get("age")

    filtered_data = dataset
    if gender:
        filtered_data = [clip for clip in filtered_data if clip["gender"] == gender]
    if race:
        filtered_data = [clip for clip in filtered_data if clip["race"] == race]
    if age:
        age = int(age)
        filtered_data = [clip for clip in filtered_data if clip["age"] == age]

    return jsonify(filtered_data)


# Endpoint to download filtered dataset
@app.route("/download", methods=["POST"])
def download_dataset():
    filter_criteria = request.json
    filtered_data = dataset

    gender = filter_criteria.get("gender")
    race = filter_criteria.get("race")
    age = filter_criteria.get("age")

    if gender:
        filtered_data = [clip for clip in filtered_data if clip["gender"] == gender]
    if race:
        filtered_data = [clip for clip in filtered_data if clip["race"] == race]
    if age:
        age = int(age)
        filtered_data = [clip for clip in filtered_data if clip["age"] == age]

    # Create a zip file with filtered clips
    import zipfile
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdirname:
        zip_filename = os.path.join(tmpdirname, "filtered_dataset.zip")
        with zipfile.ZipFile(zip_filename, "w") as zipf:
            for clip in filtered_data:
                clip_path = clip["file_path"]
                zipf.write(clip_path, os.path.basename(clip_path))

        return send_file(
            zip_filename, as_attachment=True, download_name="filtered_dataset.zip"
        )


if __name__ == "__main__":
    app.run(debug=True)
