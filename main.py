import os, uuid, colorama
from PIL import Image
from flask import Flask, request, render_template, jsonify, send_file

app = Flask(__name__)

red = colorama.Fore.RED
grn = colorama.Fore.GREEN
ylw = colorama.Fore.YELLOW
rst = colorama.Fore.RESET 

os.makedirs("uploads",exist_ok=True)
os.makedirs("outputs",exist_ok=True)

def convert_to_pdf(job_id):
    try:
        images = []
        for imge in os.listdir(f"uploads/{job_id}"):
            img = Image.open(f"uploads/{job_id}/{imge}")
            if img.mode != "RGB": img = img.convert("RGB")
            images.append(img)
        images[0].save(f"outputs/{job_id}.pdf", save_all=True, append_images=images[1:])
        return {"status": True}
    except Exception as err: return {"status": False, "message": err} 

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    try:
        job_id = str(uuid.uuid4())
        print(f"{ylw}Running Job... {rst}(ID: {job_id})")
        images = request.files.getlist("images")
        if not images: return jsonify({"status": False, "message": "Images List is Empty!S"}), 400
        os.makedirs(f"uploads/{job_id}",exist_ok=True)
        for image in images: image.save(f"uploads/{job_id}/{image.filename}")
        res = convert_to_pdf(job_id)
        if not res["status"]: return jsonify({"status": False, "message": res["message"]}), 500
        print(f"{grn}Job Finished. {rst}(ID: {job_id})")
        return jsonify({"status": True, "url": f"/download/{job_id}"})
    except Exception as err:
        print(f"{red}Job Error! {rst}(ID: {job_id})\n{err}")
        return jsonify({"status": False, "message": str(err)}), 500

@app.route("/download/<job_id>")
def download(job_id):
    if not os.path.exists(f"outputs/{job_id}.pdf"): return f"PDF File Not Found! ({job_id})"
    return send_file(f"outputs/{job_id}.pdf",as_attachment=True)

app.run(host="0.0.0.0",port=5000,debug=True)