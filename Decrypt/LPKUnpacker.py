from __future__ import unicode_literals
import argparse
import zipfile
import json
import logging
import os
import re
from hashlib import md5
from typing import Tuple

import filetype
from filetype.types import Type

# -------------------- utils (merged) --------------------
def hashed_filename(s: str) -> str:
    t = md5()
    t.update(s.encode())
    return t.hexdigest()

def normalize(s: str) -> str:
    s = ''.join(c for c in s if ord(c) >= 32 or c == ' ')
    s = re.sub(r'[<>:\"|?*]', '', s)
    if not s.strip():
        s = "unnamed"
    return s

def safe_mkdir(s: str):
    os.makedirs(s, exist_ok=True)

def genkey(s: str) -> int:
    ret = 0
    for i in s:
        ret = (ret * 31 + ord(i)) & 0xffffffff
    if ret & 0x80000000:
        ret = ret | 0xffffffff00000000
    return ret

def decrypt(key: int, data: bytes) -> bytes:
    ret = []
    for slice in [data[i:i+1024] for i in range(0, len(data), 1024)]:
        tmpkey = key
        for i in slice:
            tmpkey = (65535 & 2531011 + 214013 * tmpkey >> 16) & 0xffffffff
            ret.append((tmpkey & 0xff) ^ i)
    return bytes(ret)

match_rule = re.compile(r"[0-9a-f]{32}.bin3?")
def is_encrypted_file(s: str) -> bool:
    if type(s) != str:
        return False
    return match_rule.fullmatch(s) is not None

def find_encrypted_file(s: str) -> str:
    files = re.findall(match_rule, s)
    if files == []:
        return None
    return files[0]

def travels_dict(dic: dict):
    for k in dic:
        if type(dic[k]) == dict:
            for p, v in travels_dict(dic[k]):
                yield f"{k}_{p}", v
        elif type(dic[k]) == list:
            for p, v in travels_list(dic[k]):
                yield f"{k}_{p}", v
        else:
            yield str(k), dic[k]
        
def travels_list(vals: list):
    for i in range(len(vals)):
        if type(vals[i]) == dict:
            for p, v in travels_dict(vals[i]):
                yield f"{i}_{p}", v
        elif type(vals[i]) == list:
            for p, v in travels_list(vals[i]):
                yield f"{i}_{p}", v
        else:
            yield str(i), vals[i]


class Moc3(Type):
    MIME = "application/moc3"
    EXTENSION = "moc3"
    def __init__(self):
        super(Moc3, self).__init__(mime=Moc3.MIME, extension=Moc3.EXTENSION)
    
    def match(self, buf):
        return len(buf) > 3 and buf.startswith(b"MOC3")

class Moc(Type):
    MIME = "application/moc"
    EXTENSION = "moc"
    def __init__(self):
        super(Moc, self).__init__(mime=Moc.MIME, extension=Moc.EXTENSION)
    
    def match(self, buf):
        return len(buf) > 3 and buf.startswith(b"moc")

filetype.add_type(Moc3())
filetype.add_type(Moc())

def guess_type(data: bytes):
    ftype = filetype.guess(data)
    if ftype != None:
        return "." + ftype.extension
    try:
        json.loads(data.decode("utf8"))
        return ".json"
    except:
        return ""


# -------------------- LpkLoader (merged) --------------------
logger = logging.getLogger("lpkLoder")

class LpkLoader():
    def __init__(self, lpkpath, configpath) -> None:
        self.lpkpath = lpkpath
        self.configpath = configpath
        self.lpkType = None
        self.encrypted = "true"
        self.trans = {}
        self.entrys = {}
        self.load_lpk()
    
    def load_lpk(self):
        self.lpkfile = zipfile.ZipFile(self.lpkpath)
        try:
            config_mlve_raw = self.lpkfile.read(hashed_filename("config.mlve")).decode()
        except KeyError:
            try:
                config_mlve_raw = self.lpkfile.read("config.mlve").decode('utf-8-sig')
            except Exception:
                logger.fatal("Failed to retrieve lpk config!")
                raise


        self.mlve_config = json.loads(config_mlve_raw)

        logger.debug(f"mlve config:\n {self.mlve_config}")
        self.lpkType = self.mlve_config.get("type")
        # only steam workshop lpk needs config.json to decrypt
        if self.lpkType == "STM_1_0":
            self.load_config()
    
    def load_config(self):
        if not self.configpath:
            raise ValueError("STM type lpk requires --config pointing to config.json")
        self.config = json.loads(open(self.configpath, "r", encoding="utf8").read())
    
    def extract(self, outputdir: str):
        if self.lpkType in ["STD2_0", "STM_1_0"]:
            for chara in self.mlve_config["list"]:
                if self.lpkType == "STM_1_0" and hasattr(self, 'config') and 'title' in self.config:
                    chara_name = self.config["title"]
                else:
                    chara_name = chara["character"] if chara["character"] != "" else "character"
                subdir =  os.path.join(outputdir, normalize(chara_name))
                safe_mkdir(subdir)

                for i in range(len(chara["costume"])):
                    logger.info(f"extracting {chara_name}_costume_{i}")
                    self.extract_costume(chara["costume"][i], subdir)

                # replace encryped filename to decrypted filename in entrys(model.json)
                for name in self.entrys:
                    out_s: str = self.entrys[name]
                    for k in self.trans:
                        out_s = out_s.replace(k, self.trans[k])
                    open(os.path.join(subdir, name), "w", encoding="utf8").write(out_s)
        else:
            try:
                print("Deprecated/unknown lpk format detected. Attempting with STD_1_0 format...")
                print("Decryption may not work for some packs, even though this script outputs all files.")
                self.encrypted = self.mlve_config.get("encrypt", "true")
                if self.encrypted == "false":
                    print("lpk is not encrypted, extracting all files...")
                    self.lpkfile.extractall(outputdir)
                    return
                # For STD_1_0 and earlier
                for file in self.lpkfile.namelist():
                    if os.path.splitext(file)[-1] == '':
                        continue
                    subdir = os.path.join(outputdir, os.path.dirname(file))
                    outputFilePath = os.path.join(subdir, os.path.basename(file))
                    safe_mkdir(subdir)
                    if os.path.splitext(file)[-1] in [".json", ".mlve", ".txt"]:
                        print(f"Extracting {file} -> {outputFilePath}")
                        self.lpkfile.extract(file, outputdir)
                    else:
                        print(f"Decrypting {file} -> {outputFilePath}")
                        decryptedData = self.decrypt_file(file)
                        with open(outputFilePath, "wb") as outputFile:
                            outputFile.write(decryptedData)
            except Exception as e:
                logger.fatal(f"Failed to decrypt {self.lpkpath}, possibly wrong/unsupported format: {e}")
                raise
    
    def extract_costume(self, costume: dict, dir: str):
        if costume["path"] == "":
            return

        filename :str = costume["path"]

        self.check_decrypt(filename)

        self.extract_model_json(filename, dir)

    def extract_model_json(self, model_json: str, dir):
        logger.debug(f"========= extracting model {model_json} =========")
        # already extracted
        if model_json in self.trans:
            return

        subdir = dir
        entry_s = self.decrypt_file(model_json).decode(encoding="utf8")
        entry = json.loads(entry_s)

        out_s = json.dumps(entry, ensure_ascii=False)
        id = len(self.entrys)

        self.entrys[f"model{id}.json"] = out_s

        self.trans[model_json] = f"model{id}.json"

        logger.debug(f"model{id}.json:\n{entry}")

        for name, val in travels_dict(entry):
            logger.debug(f"{name} -> {val}")
            # extract submodel
            if (name.lower().endswith("_command") or name.lower().endswith("_postcommand")) and val:
                commands = [c.strip() for c in val.split(";") if c.strip()]
                for cmd in commands:
                    lower_cmd = cmd.lower()

                    if lower_cmd.startswith("change_model"):
                        target = cmd[len("change_model"):].strip().strip('\"\'')
                        if target:
                            target = target.split()[0]
                        fallback = find_encrypted_file(cmd)
                        target_file = target if target else fallback
                        if target_file:
                            self.extract_model_json(target_file, dir)
                            continue

                    enc_file = find_encrypted_file(cmd)
                    if enc_file == None:
                        continue

                    if lower_cmd.startswith("change_cos"):
                        self.extract_model_json(enc_file, dir)
                    else:
                        name += f"_{id}"
                        name = self.name_change(name)
                        _, suffix = self.recovery(enc_file, os.path.join(subdir, name))
                        self.trans[enc_file] = name + suffix


            if is_encrypted_file(val):
                enc_file = val
                # already decrypted
                if enc_file in self.trans:
                    continue
                # recover regular files
                else:
                    name += f"_{id}"
                    name = self.name_change(name)
                    _, suffix = self.recovery(enc_file, os.path.join(subdir, name))
                    self.trans[enc_file] = name + suffix
        
        logger.debug(f"========= end of model {model_json} =========")


    def check_decrypt(self, filename):
        '''
        Check if decryption work.

        If lpk earsed fileId in config.json, this function will automatically try to use lpkFile as fileId.
        If all attemptions failed, this function will read fileId from ``STDIN``.
        '''

        logger.info("try to decrypt entry model.json")

        try:
            self.decrypt_file(filename).decode(encoding="utf8")
        except UnicodeDecodeError:
            logger.info("trying to auto fix fileId")
            success = False
            possible_fileId = []
            possible_fileId.append(self.config["lpkFile"].strip('.lpk'))
            for fileid in possible_fileId:
                self.config["fileId"] = fileid
                try:
                    self.decrypt_file(filename).decode(encoding="utf8")
                except UnicodeDecodeError:
                    continue

                success = True
                break
            if not success:
                print("steam workshop fileid is usually a foler under PATH_TO_YOUR_STEAM/steamapps/workshop/content/616720/([0-9]+)")
                fileid = input("auto fix failed, please input fileid manually: ")
                self.config["fileId"] = fileid
                try:
                    self.decrypt_file(filename).decode(encoding="utf8")
                except UnicodeDecodeError:
                    logger.fatal("decrypt failed!")
                    raise

    def recovery(self, filename, output) -> Tuple[bytes, str]:
        ret = self.decrypt_file(filename)
        suffix = guess_type(ret)
        print(f"recovering {filename} -> {output+suffix}")
        open(output + suffix, "wb").write(ret)
        return ret, suffix

    def getkey(self, file: str):
        if self.lpkType == "STM_1_0" and self.mlve_config["encrypt"] != "true":
            return 0
        if self.lpkType == "STM_1_0":
            return genkey(self.mlve_config["id"] + self.config["fileId"] + file + self.config["metaData"])
        elif self.lpkType == "STD2_0":
            return genkey(self.mlve_config["id"] + file)
        elif self.lpkType == "STD_1_0":
            return genkey(self.mlve_config["id"] + file)
        else:
            raise Exception(f"not support type {self.mlve_config['type']}")

    def decrypt_file(self, filename) -> bytes:
        data = self.lpkfile.read(filename)
        return self.decrypt_data(filename, data)

    def decrypt_data(self, filename: str, data: bytes) -> bytes:
        key = self.getkey(filename)
        return decrypt(key, data)
    
    def name_change(self, name: str) -> str:
        # remove FileReferences_ and normalize slashes
        name = name.replace("FileReferences_", "")
        return name.replace("\\", "/")


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Single-file LPK unpacker")
    # target_lpk is optional now: default to current directory so script can be run without args
    parser.add_argument("target_lpk", nargs='?', default='.', help="path to lpk file or directory to scan (default: current directory)")
    # Make output_dir optional; default to current directory
    # If not provided, default will be the script's directory under an `output` subfolder
    parser.add_argument("output_dir", nargs='?', default=None, help="directory to store result (default: script_dir/output)")
    parser.add_argument("-c", "--config", help="(optional) override config.json for STM_1_0 packs (if not provided, script will look for config.json next to each .lpk)")
    parser.add_argument("-v", "--verbosity", action="count", default=0, help="increase output verbosity")
    return parser


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()

    loglevels = [logging.FATAL, logging.INFO, logging.DEBUG]
    verbosity = args.verbosity if args.verbosity < len(loglevels) else len(loglevels) -1
    logging.basicConfig(level=loglevels[verbosity], format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    target = args.target_lpk
    # collect lpk files
    lpk_files = []
    if os.path.isdir(target):
        for root, _, files in os.walk(target):
            for f in files:
                if f.lower().endswith('.lpk'):
                    lpk_files.append(os.path.join(root, f))
    else:
        # single file (may be a path to a single .lpk)
        if os.path.isfile(target) and target.lower().endswith('.lpk'):
            lpk_files.append(target)
        else:
            # treat as pattern or missing file
            print(f"Target '{target}' is not a directory or a .lpk file.")
            exit(1)

    if not lpk_files:
        print(f"No .lpk files found under '{target}'.")
        exit(0)

    # Default output directory is a folder named 'output' inside the script directory if not specified
    if args.output_dir:
        base_out = args.output_dir
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_out = os.path.join(script_dir, 'output')
        safe_mkdir(base_out)
    for lpk in lpk_files:
        lpk_name = os.path.splitext(os.path.basename(lpk))[0]
        per_out = os.path.join(base_out, lpk_name)
        safe_mkdir(per_out)

        # determine config: prefer user-supplied global config, otherwise look for config.json next to the lpk
        if args.config:
            config_path = args.config
        else:
            maybe = os.path.join(os.path.dirname(lpk), 'config.json')
            config_path = maybe if os.path.isfile(maybe) else None

        print(f"Processing: {lpk} -> {per_out} (config: {config_path})")
        try:
            loader = LpkLoader(lpk, config_path)
        except Exception as e:
            print(f"Failed to initialize loader for {lpk}: {e}")
            continue

        try:
            loader.extract(per_out)
        except Exception as e:
            print(f"Failed to extract {lpk}: {e}")
            continue
