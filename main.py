import os
import re
import uuid
import shutil
import colorama

from PIL import Image
from flask import Flask, request, render_template, jsonify, send_file

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

red = colorama.Fore.RED
grn = colorama.Fore.GREEN
ylw = colorama.Fore.YELLOW
rst = colorama.Fore.RESET

os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)


def cleanup(job_id):
    try:
        shutil.rmtree(f"uploads/{job_id}", ignore_errors=True)
    except:
        pass


def convert_to_pdf(job_id):
    images = []

    try:
        upload_dir = f"uploads/{job_id}"

        for filename in os.listdir(upload_dir):
            path = os.path.join(upload_dir, filename)

            try:
                img = Image.open(path)

                if img.mode != "RGB":
                    img = img.convert("RGB")

                images.append(img)

            except Exception:
                continue

        if not images:
            return {
                "status": False,
                "message": "No valid images found"
            }

        output_pdf = f"outputs/{job_id}.pdf"

        images[0].save(
            output_pdf,
            save_all=True,
            append_images=images[1:]
        )

        return {"status": True}

    except Exception as err:
        return {
            "status": False,
            "message": str(err)
        }

    finally:
        for img in images:
            try:
                img.close()
            except:
                pass


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    job_id = str(uuid.uuid4())

    try:
        print(f"{ylw}Running Job... {rst}(ID: {job_id})")

        images = request.files.getlist("images")

        if not images:
            return jsonify({
                "status": False,
                "message": "Images List is Empty!"
            }), 400

        upload_dir = f"uploads/{job_id}"
        os.makedirs(upload_dir, exist_ok=True)

        for image in images:
            if image.filename:
                image.save(
                    os.path.join(upload_dir, image.filename)
                )

        res = convert_to_pdf(job_id)

        if not res["status"]:
            cleanup(job_id)

            return jsonify({
                "status": False,
                "message": res["message"]
            }), 500

        print(f"{grn}Job Finished. {rst}(ID: {job_id})")

        return jsonify({
            "status": True,
            "url": f"/download/{job_id}"
        })

    except Exception as err:
        cleanup(job_id)

        print(f"{red}Job Error! {rst}(ID: {job_id})\n{err}")

        return jsonify({
            "status": False,
            "message": str(err)
        }), 500


@app.errorhandler(413)
def too_large(e):
    return jsonify({
        "status": False,
        "message": "Upload size exceeds 20 MB limit"
    }), 413


@app.route("/download/<job_id>")
def download(job_id):

    if not re.match(r"^[a-f0-9\-]+$", job_id):
        return "Invalid Job ID", 400

    pdf_path = f"outputs/{job_id}.pdf"

    if not os.path.exists(pdf_path):
        return "PDF File Not Found", 404

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name="QuickPDF.pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)