from distutils.dir_util import copy_tree
from os import mkdir, makedirs, path, walk, remove, system, listdir
import pathlib
import json
import sys
import shutil
import subprocess
from boto3 import client
import socket
import uuid
import io
from utils.utils import s3_client, lambda_constants

lambda_client = client("lambda")


def try_shutil(dest_folder):
    try:
        shutil.rmtree(dest_folder)
    except:
        # print("Folder was not deleted")
        pass
    try:
        makedirs(dest_folder)
    except:
        # print("Folder was not created")
        pass


def iterate_root_dirs(root_dirs):
    for dirs in root_dirs:
        copy_tree(root_folder + dirs, dest_folder + dirs, preserve_mode=1, preserve_times=1, update=0, verbose=1, dry_run=0)


if sys.platform == "darwin":
    # if "thaty" in socket.gethostname().lower():
    root_folder = "/Users/devesch/Documents/GitHub/petmapa/"


elif sys.platform == "win32":
    if "dh9evn9" in socket.gethostname().lower():
        root_folder = "C:/Users/eugen/Desktop/Desenvolvimento/petmapa/"
    elif "DESKTOP-7VHGH1S".lower() in socket.gethostname().lower():
        root_folder = "D:/usuario/Documents/GitHub/testdrive/"


last_update_data = json.load(open("last_update_data.json", "r", encoding="utf-8"))
new_paths = {}
web_pack_change = False
s3_images_change = False


for filepath, subdirs, files in walk(root_folder + "src/assets"):
    for name in files:
        if "images" not in filepath:
            new_paths[str(pathlib.PurePath(filepath, name)).replace("\\", "/").replace(root_folder, "")] = path.getmtime(pathlib.PurePath(filepath, name))
            if str(pathlib.PurePath(filepath, name)).replace("\\", "/").replace(root_folder, "") not in last_update_data:
                web_pack_change = True
                continue
            if last_update_data[str(pathlib.PurePath(filepath, name)).replace("\\", "/").replace(root_folder, "")] != new_paths[str(pathlib.PurePath(filepath, name)).replace("\\", "/").replace(root_folder, "")]:
                web_pack_change = True
        else:
            new_paths[str(pathlib.PurePath(filepath, name)).replace("\\", "/").replace(root_folder, "")] = path.getmtime(pathlib.PurePath(filepath, name))
            if str(pathlib.PurePath(filepath, name)).replace("\\", "/").replace(root_folder, "") not in last_update_data:
                s3_images_change = True
                continue
            if last_update_data[str(pathlib.PurePath(filepath, name)).replace("\\", "/").replace(root_folder, "")] != new_paths[str(pathlib.PurePath(filepath, name)).replace("\\", "/").replace(root_folder, "")]:
                s3_images_change = True


if web_pack_change:
    system("npm run dev")


new_version = str(uuid.uuid4())

### CSS ###

css_src_dir = root_folder + r"dist/style/style.css"
css_dst_dir = root_folder + r"dist/style/style_" + new_version + ".css"

# if css_src_dir not in last_update_data:
#     css_change = True
# elif last_update_data[css_src_dir] != path.getmtime(pathlib.PurePath(css_src_dir.replace("style.css", ""), "style.css")):
#     css_change = True

# if css_change:
shutil.copy(css_src_dir, css_dst_dir)

# new_paths[css_src_dir] = path.getmtime(pathlib.PurePath(css_src_dir.replace("style.css", ""), "style.css"))

### BUNDLE ###

bundle_src_dir = root_folder + r"dist/js/bundle.js"
bundle_dst_dir = root_folder + r"dist/js/bundle_" + new_version + ".js"

# if bundle_src_dir not in last_update_data:
#     bundle_change = True
# elif last_update_data[bundle_src_dir] != path.getmtime(pathlib.PurePath(bundle_src_dir.replace("bundle.js", ""), "bundle.js")):
#     bundle_change = True

# if bundle_change:
shutil.copy(bundle_src_dir, bundle_dst_dir)

# new_paths[css_src_dir] = path.getmtime(pathlib.PurePath(css_src_dir.replace("bundle.js", ""), "bundle.js"))

### JS MASK ###

js_mask_src_dir = root_folder + r"src/assets/js/mask.js"
js_mask_dst_dir = root_folder + r"src/assets/js/mask_" + new_version + ".js"

# if js_mask_src_dir not in last_update_data:
#     js_mask_change = True
# elif last_update_data[js_mask_src_dir] != path.getmtime(pathlib.PurePath(js_mask_src_dir.replace("mask.js", ""), "mask.js")):
#     js_mask_change = True

# if js_mask_change:
shutil.copy(js_mask_src_dir, js_mask_dst_dir)

with open("src/html/main/header.html", "r") as read_file:
    header = read_file.read()

header = header.replace("style.css", "style_" + new_version + ".css")
header = header.replace("bundle.js", "bundle_" + new_version + ".js")
header = header.replace("mask.js", "mask_" + new_version + ".js")

with open("src/html/main/header.html", "w") as read_file:
    read_file.write(header)

root_dirs = ["utils/", "objects/", "pages/", "src/html", "pdfkit/"]
project_folder = root_folder.replace((root_folder.split("/")[-2] + "/"), "") + "build_" + str(root_folder.split("/")[-2])
dest_folder = project_folder + "/tmp/"


try:
    remove(project_folder + "/archive.zip")
except:
    # print("Folder was not deleted")
    pass

try_shutil(dest_folder)
iterate_root_dirs(root_dirs)
shutil.copy(root_folder + "lambda_function.py", dest_folder + "lambda_function.py")

process = shutil.make_archive(project_folder + "/archive", "zip", dest_folder)

f = open(project_folder + "/archive.zip", "rb")
response = lambda_client.update_function_code(
    FunctionName="petmapa",
    ZipFile=f.read(),
)
print(str(response))

shutil.copy(root_folder + "lambda_function_send_case_email.py", dest_folder + "lambda_function.py")

process = shutil.make_archive(project_folder + "/archive", "zip", dest_folder)

f = open(project_folder + "/archive.zip", "rb")
response = lambda_client.update_function_code(
    FunctionName="send_case_email",
    ZipFile=f.read(),
)

# if s3_images_change:
process3 = subprocess.Popen("aws s3 rm s3://cdn.petmapa.com.br/assets/images --recursive", shell=True)
process3 = subprocess.Popen("aws s3 rm s3://cdn.petmapa.com.br/fonts --recursive", shell=True)
process3.wait()

process3 = subprocess.Popen("aws s3 cp " + str(root_folder) + "src/assets/images s3://cdn.petmapa.com.br/assets/images --recursive", shell=True)
process3 = subprocess.Popen("aws s3 cp " + str(root_folder) + "dist/fonts s3://cdn.petmapa.com.br/fonts --recursive", shell=True)
process3.wait()

process3 = subprocess.Popen("aws s3 rm s3://cdn.petmapa.com.br/style --recursive", shell=True)
process3.wait()
process3 = subprocess.Popen("aws s3 rm s3://cdn.petmapa.com.br/js --recursive", shell=True)
process3.wait()


# s3_client.upload_file("src/assets/js/jquery.min.js", lambda_constants["cdn_bucket"], "js/jquery.min.js", ExtraArgs={"ContentType": "text/javascript"})
s3_client.upload_file("src/assets/js/mask_" + new_version + ".js", lambda_constants["cdn_bucket"], "js/mask_" + new_version + ".js", ExtraArgs={"ContentType": "text/javascript"})
s3_client.upload_file("dist/js/bundle_" + new_version + ".js", lambda_constants["cdn_bucket"], "js/bundle_" + new_version + ".js", ExtraArgs={"ContentType": "text/javascript"})
s3_client.upload_file("dist/style/style_" + new_version + ".css", lambda_constants["cdn_bucket"], "style/style_" + new_version + ".css", ExtraArgs={"ContentType": "text/css"})


with open("src/html/main/header.html", "r") as read_file:
    header = read_file.read()
header = header.replace("style_" + new_version + ".css", "style.css")
header = header.replace("bundle_" + new_version + ".js", "bundle.js")
header = header.replace("mask_" + new_version + ".js", "mask.js")

with open("src/html/main/header.html", "w") as read_file:
    read_file.write(header)

remove(css_dst_dir)
remove(bundle_dst_dir)
remove(js_mask_dst_dir)


with open("last_update_data.json", "w") as outfile:
    json.dump(new_paths, outfile)

print("UPDATE COMPLETED")
