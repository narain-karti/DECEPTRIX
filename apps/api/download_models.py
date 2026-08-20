import os
import urllib.request

def download_file(url, dest):
    if not os.path.exists(dest):
        print(f"Downloading {dest}...")
        urllib.request.urlretrieve(url, dest)
        print("Done.")

def main():
    model_dir = os.path.join("models", "cv2_dnn")
    os.makedirs(model_dir, exist_ok=True)
    
    prototxt_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
    caffemodel_url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
    
    download_file(prototxt_url, os.path.join(model_dir, "deploy.prototxt"))
    download_file(caffemodel_url, os.path.join(model_dir, "res10_300x300_ssd_iter_140000.caffemodel"))

if __name__ == "__main__":
    main()
